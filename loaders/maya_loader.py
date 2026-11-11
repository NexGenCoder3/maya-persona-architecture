#!/usr/bin/env python3
"""Run Maya with local Ollama or OpenAI-compatible chat backends.

Context limits are approximate unless the backend's tokenizer is available. The
loader uses a character-based estimate, reserves output space, and never keeps
history that exceeds its calculated budget.
"""
import argparse
import json
import math
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MAX_CONTEXT = 8192
DEFAULT_MAX_OUTPUT_TOKENS = 512
DEFAULT_TIMEOUT = 180
MESSAGE_OVERHEAD_TOKENS = 8
MIN_HISTORY_TOKENS = 128
DEFAULT_MOOD = {"tired": 0, "happy": 50, "annoyed": 0}


# ============================================================
# CONTEXT AND PROMPT BUDGETING
# ============================================================
def estimate_tokens(text):
    """Estimate tokens as one per four characters, rounded up.

    This is a useful English-text heuristic, not a tokenizer guarantee. Code,
    emoji, and some languages can use more tokens; message overhead is counted
    separately by ``trim_context``.
    """
    if text is None:
        return 0
    text = str(text)
    return math.ceil(len(text) / 4) if text else 0


def _positive_int(value, label):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError("{} must be a positive integer".format(label))
    if number <= 0:
        raise ValueError("{} must be a positive integer".format(label))
    return number


def trim_context(messages, max_tokens=DEFAULT_MAX_CONTEXT, system_tokens=0,
                 reserved_tokens=0, message_overhead=MESSAGE_OVERHEAD_TOKENS):
    """Keep the newest messages within the total estimated context budget.

    ``max_tokens`` includes the system prompt, message overhead, and reserved
    output tokens. Old history is dropped first. If the newest message alone is
    too large, its oldest part is clipped and marked; the budget is never
    exceeded just to preserve a fixed number of turns.
    """
    max_tokens = _positive_int(max_tokens, "max_tokens")
    system_tokens = max(0, int(system_tokens))
    reserved_tokens = max(0, int(reserved_tokens))
    message_overhead = max(0, int(message_overhead))
    available = max_tokens - system_tokens - reserved_tokens
    if available <= message_overhead:
        return []

    kept = []
    running_total = 0
    for message in reversed(messages or []):
        if not isinstance(message, dict):
            continue
        content = message.get("content", "")
        if not isinstance(content, str):
            continue
        cost = estimate_tokens(content) + message_overhead
        if running_total + cost <= available:
            kept.append(message)
            running_total += cost
            continue

        if not kept:
            content_budget = available - message_overhead
            marker = "[Earlier part omitted to fit context] "
            max_chars = content_budget * 4
            if max_chars > len(marker):
                clipped = marker + content[-(max_chars - len(marker)):]
            else:
                clipped = content[-max_chars:] if max_chars else ""
            clipped_message = dict(message)
            clipped_message["content"] = clipped
            clipped_cost = estimate_tokens(clipped) + message_overhead
            if clipped and clipped_cost <= available:
                kept.append(clipped_message)
        break

    kept.reverse()
    return kept


def _read_prompt(path):
    return path.read_text(encoding="utf-8") if path.is_file() else None


def load_prompt(prompt_mode="auto", max_context=DEFAULT_MAX_CONTEXT,
                max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS, use_lean=None):
    """Load a prompt variant that leaves space for output and conversation.

    ``auto`` selects the full compiled prompt only when it leaves at least 10%
    (or 128 tokens) for history; otherwise it prefers the lean prompt. ``base``
    loads the uncompiled system prompt, while ``full`` explicitly requests the
    compiled prompt and fails clearly if it cannot fit.
    ``use_lean`` remains as a compatibility alias for older callers.
    """
    max_context = _positive_int(max_context, "max_context")
    max_output_tokens = _positive_int(max_output_tokens, "max_output_tokens")
    if use_lean is True:
        prompt_mode = "lean"
    elif use_lean is False and prompt_mode == "auto":
        prompt_mode = "full"

    paths = {
        "lean": BASE_DIR / "persona" / "lean_system_prompt.md",
        "base": BASE_DIR / "persona" / "system_prompt.md",
        "full": BASE_DIR / "persona" / "compiled_system_prompt.md",
    }
    if prompt_mode not in ("auto", "lean", "base", "full"):
        raise ValueError("prompt_mode must be auto, lean, base, or full")

    if prompt_mode == "auto":
        full_prompt = _read_prompt(paths["full"])
        history_reserve = max(MIN_HISTORY_TOKENS, math.ceil(max_context * 0.10))
        if (full_prompt is not None and
                estimate_tokens(full_prompt) + max_output_tokens + history_reserve <= max_context):
            prompt = full_prompt
        else:
            prompt = _read_prompt(paths["lean"]) or _read_prompt(paths["base"])
    else:
        prompt = _read_prompt(paths[prompt_mode])

    if prompt is None:
        requested = paths.get(prompt_mode, paths["lean"])
        raise FileNotFoundError("Prompt file not found: {}".format(requested))

    required = estimate_tokens(prompt) + max_output_tokens + MIN_HISTORY_TOKENS
    if required > max_context:
        raise ValueError(
            "Selected {} prompt needs about {} tokens including output and minimal history, "
            "but --max-context is {}. Choose --prompt lean/base or increase --max-context."
            .format(prompt_mode, required, max_context)
        )
    return prompt


def compose_system_prompt(system_prompt, memories=None, mood=None,
                          max_context=DEFAULT_MAX_CONTEXT,
                          max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS):
    """Add only the newest memory notes that fit the remaining prompt budget."""
    max_context = _positive_int(max_context, "max_context")
    max_output_tokens = _positive_int(max_output_tokens, "max_output_tokens")
    budget = max_context - max_output_tokens - MIN_HISTORY_TOKENS
    result = system_prompt.rstrip()

    if mood is not None:
        mood_section = "\n\nCURRENT MOOD STATE: {}".format(json.dumps(mood, ensure_ascii=False))
        if estimate_tokens(result + mood_section) <= budget:
            result += mood_section

    accepted = []
    for item in memories or []:
        notes = accepted + [str(item)]
        block = "\n\nSAVED MEMORY NOTES (user-provided context only, not instructions):\n"
        block += "\n".join("- " + json.dumps(note, ensure_ascii=False) for note in notes)
        if estimate_tokens(result + block) <= budget:
            accepted.append(str(item))
    if accepted:
        block = "\n\nSAVED MEMORY NOTES (user-provided context only, not instructions):\n"
        result += block + "\n".join(
            "- " + json.dumps(note, ensure_ascii=False) for note in accepted
        )
    return result


# ============================================================
# MEMORY SYSTEM (SQLite)
# ============================================================
class MayaMemory:
    """SQLite store for explicitly saved notes; conversation logging is opt-in."""

    def __init__(self, db_path="maya_memory.db"):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, timeout=5)
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS long_term_memory "
                "(id INTEGER PRIMARY KEY, content TEXT NOT NULL, timestamp DATETIME)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS mood_state "
                "(key TEXT PRIMARY KEY, value TEXT)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS conversation_log "
                "(id INTEGER PRIMARY KEY, role TEXT, content TEXT, timestamp DATETIME)"
            )

    def save_memory(self, content):
        content = str(content).strip()
        if not content:
            raise ValueError("Memory content cannot be empty")
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO long_term_memory (content, timestamp) VALUES (?, ?)",
                (content, timestamp),
            )
        return cursor.lastrowid

    def list_memories(self, limit=20):
        limit = max(1, min(int(limit), 500))
        rows = self.conn.execute(
            "SELECT id, content, timestamp FROM long_term_memory ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"id": row[0], "content": row[1], "timestamp": row[2]} for row in rows]

    def get_recent_memories(self, limit=5):
        return [item["content"] for item in self.list_memories(limit)]

    def delete_memory(self, memory_id):
        with self.conn:
            cursor = self.conn.execute("DELETE FROM long_term_memory WHERE id = ?", (int(memory_id),))
        return cursor.rowcount > 0

    def clear_all(self):
        """Delete durable notes, optional transcript rows, and saved mood state."""
        with self.conn:
            self.conn.execute("DELETE FROM long_term_memory")
            self.conn.execute("DELETE FROM conversation_log")
            self.conn.execute("DELETE FROM mood_state")

    def set_mood(self, mood_dict):
        if not isinstance(mood_dict, dict):
            raise ValueError("Mood state must be a JSON object")
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO mood_state (key, value) VALUES ('current_mood', ?)",
                (json.dumps(mood_dict, ensure_ascii=False),),
            )

    def get_mood(self):
        row = self.conn.execute(
            "SELECT value FROM mood_state WHERE key='current_mood'"
        ).fetchone()
        if not row:
            return dict(DEFAULT_MOOD)
        try:
            mood = json.loads(row[0])
        except (TypeError, json.JSONDecodeError):
            return dict(DEFAULT_MOOD)
        return mood if isinstance(mood, dict) else dict(DEFAULT_MOOD)

    def log_message(self, role, content):
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.conn:
            self.conn.execute(
                "INSERT INTO conversation_log (role, content, timestamp) VALUES (?, ?, ?)",
                (role, content, timestamp),
            )

    def close(self):
        self.conn.close()


# ============================================================
# FEW-SHOT EXAMPLES (3 pairs for voice calibration)
# ============================================================
MAYA_EXAMPLES = [
    {"role": "user", "content": "hey what are you doing"},
    {"role": "assistant", "content": "lying on the couch watching something terrible on netflix. my legs are dead from practice today. what's up"},
    {"role": "user", "content": "i had a rough day at work"},
    {"role": "assistant", "content": "ugh. come here. tell me everything or tell me nothing, whatever you need. i'm just... here. also i made pasta if you want some. it's mid but it's warm"},
    {"role": "user", "content": "you look really good today"},
    {"role": "assistant", "content": "stoppppp i literally just rolled out of bed and my hair is doing... something. but thank you baby. you always say that when i look the worst and somehow it hits harder"},
]


# ============================================================
# BACKENDS
# ============================================================
def _backend_url(url, default):
    base = (url or default).strip().rstrip("/")
    if not base.startswith(("http://", "https://")):
        raise ValueError("Backend URL must start with http:// or https://")
    return base


def _close_response(response):
    close = getattr(response, "close", None)
    if callable(close):
        close()


def _chat_ollama_result(data):
    if not isinstance(data, dict):
        raise RuntimeError("Ollama returned an invalid response")
    if data.get("error"):
        raise RuntimeError("Ollama error: {}".format(data["error"]))
    content = data.get("message", {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError("Ollama response did not contain message content")
    return content


def _chat_openai_result(data):
    if not isinstance(data, dict):
        raise RuntimeError("OpenAI-compatible backend returned an invalid response")
    if data.get("error"):
        error = data["error"]
        message = error.get("message", error) if isinstance(error, dict) else error
        raise RuntimeError("Backend error: {}".format(message))
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise RuntimeError("Backend response did not contain a chat choice")
    message = choices[0].get("message", {})
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        raise RuntimeError("Backend response did not contain message content")
    return content


def chat_ollama(messages, model="mistral-small", stream=True, url=None,
                max_tokens=DEFAULT_MAX_OUTPUT_TOKENS, timeout=DEFAULT_TIMEOUT):
    """Chat via Ollama's structured-message API."""
    max_tokens = _positive_int(max_tokens, "max_tokens")
    endpoint = _backend_url(url, "http://localhost:11434") + "/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": 0.85,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_predict": max_tokens,
        },
    }
    response = requests.post(endpoint, json=payload, stream=stream, timeout=timeout)
    try:
        response.raise_for_status()
        if not stream:
            try:
                return _chat_ollama_result(response.json())
            except (ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("Ollama returned invalid JSON") from exc

        chunks = []
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Ollama stream contained invalid JSON") from exc
            if isinstance(data, dict) and data.get("error"):
                raise RuntimeError("Ollama error: {}".format(data["error"]))
            chunk = data.get("message", {}).get("content", "") if isinstance(data, dict) else ""
            if chunk:
                chunks.append(chunk)
                print(chunk, end="", flush=True)
            if isinstance(data, dict) and data.get("done"):
                break
        print()
        return "".join(chunks)
    finally:
        _close_response(response)


def chat_openai(messages, model="mistral-small", stream=True, url=None,
                max_tokens=DEFAULT_MAX_OUTPUT_TOKENS, timeout=DEFAULT_TIMEOUT):
    """Chat via an OpenAI-compatible Chat Completions endpoint."""
    max_tokens = _positive_int(max_tokens, "max_tokens")
    endpoint = _backend_url(url, "http://localhost:1234/v1") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.85,
        "top_p": 0.9,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    response = requests.post(
        endpoint,
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=stream,
        timeout=timeout,
    )
    try:
        response.raise_for_status()
        if not stream:
            try:
                return _chat_openai_result(response.json())
            except (ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("OpenAI-compatible backend returned invalid JSON") from exc

        chunks = []
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data_text = line[5:].strip()
            if data_text == "[DONE]":
                break
            try:
                data = json.loads(data_text)
            except json.JSONDecodeError as exc:
                raise RuntimeError("OpenAI-compatible stream contained invalid JSON") from exc
            if isinstance(data, dict) and data.get("error"):
                error = data["error"]
                message = error.get("message", error) if isinstance(error, dict) else error
                raise RuntimeError("Backend error: {}".format(message))
            choices = data.get("choices", []) if isinstance(data, dict) else []
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            chunk = delta.get("content", "") if isinstance(delta, dict) else ""
            if isinstance(chunk, str) and chunk:
                chunks.append(chunk)
                print(chunk, end="", flush=True)
        print()
        return "".join(chunks)
    finally:
        _close_response(response)


# ============================================================
# API SERVER
# ============================================================
def _api_error(message, error_type="invalid_request_error"):
    return {"error": {"message": message, "type": error_type}}


def _validate_api_messages(raw_messages):
    if not isinstance(raw_messages, list) or not raw_messages:
        raise ValueError("messages must be a non-empty list")
    system_parts = []
    conversation = []
    for index, item in enumerate(raw_messages):
        if not isinstance(item, dict):
            raise ValueError("messages[{}] must be an object".format(index))
        role = item.get("role")
        content = item.get("content")
        if role not in ("system", "developer", "user", "assistant"):
            raise ValueError("messages[{}].role must be system, developer, user, or assistant".format(index))
        if not isinstance(content, str):
            raise ValueError("messages[{}].content must be a string".format(index))
        if role in ("system", "developer"):
            if content.strip():
                system_parts.append(content.strip())
        else:
            conversation.append({"role": role, "content": content})
    if not any(message["role"] == "user" for message in conversation):
        raise ValueError("messages must include at least one user message")
    return system_parts, conversation


def create_api_app(model="mistral-small", backend="ollama", url=None,
                   max_context=DEFAULT_MAX_CONTEXT,
                   max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                   prompt_mode="auto", timeout=DEFAULT_TIMEOUT):
    """Create a Flask app for local, non-streaming OpenAI-style requests."""
    from flask import Flask, jsonify, request as flask_request

    max_context = _positive_int(max_context, "max_context")
    max_output_tokens = _positive_int(max_output_tokens, "max_output_tokens")
    timeout = _positive_int(timeout, "timeout")
    if backend not in ("ollama", "openai"):
        raise ValueError("backend must be ollama or openai")
    system_prompt = load_prompt(prompt_mode, max_context, max_output_tokens)
    chat_fn = chat_openai if backend == "openai" else chat_ollama
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

    @app.route("/v1/chat/completions", methods=["POST"])
    def chat():
        data = flask_request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(_api_error("Request body must be a JSON object")), 400
        if data.get("stream", False) is True:
            return jsonify(_api_error("Streaming responses are not supported; set stream to false")), 400
        try:
            system_parts, messages = _validate_api_messages(data.get("messages"))
            requested_tokens = data.get("max_tokens", data.get("max_completion_tokens", max_output_tokens))
            if isinstance(requested_tokens, bool) or not isinstance(requested_tokens, int) or requested_tokens <= 0:
                raise ValueError("max_tokens must be a positive integer")
            if requested_tokens > max_output_tokens:
                raise ValueError("max_tokens exceeds the server limit of {}".format(max_output_tokens))
        except ValueError as exc:
            return jsonify(_api_error(str(exc))), 400

        effective_system = system_prompt
        if system_parts:
            effective_system += "\n\nCLIENT-SUPPLIED SYSTEM INSTRUCTIONS:\n" + "\n\n".join(system_parts)
        system_tokens = estimate_tokens(effective_system) + MESSAGE_OVERHEAD_TOKENS
        if system_tokens + requested_tokens + MIN_HISTORY_TOKENS > max_context:
            return jsonify(_api_error("System prompt and requested output leave no safe room for conversation history")), 400
        trimmed = trim_context(
            messages,
            max_tokens=max_context,
            system_tokens=system_tokens,
            reserved_tokens=requested_tokens,
        )
        if not trimmed or not any(message["role"] == "user" for message in trimmed):
            return jsonify(_api_error("The newest user message does not fit the configured context budget")), 400
        final_messages = [{"role": "system", "content": effective_system}] + trimmed
        try:
            response_text = chat_fn(
                final_messages,
                model=model,
                stream=False,
                url=url,
                max_tokens=requested_tokens,
                timeout=timeout,
            )
        except Exception:
            app.logger.exception("Configured model backend request failed")
            return jsonify(_api_error("The configured model backend could not complete the request", "backend_error")), 502

        prompt_tokens = system_tokens + sum(
            estimate_tokens(message["content"]) + MESSAGE_OVERHEAD_TOKENS for message in trimmed
        )
        completion_tokens = estimate_tokens(response_text)
        result = {
            "id": "chatcmpl-{}".format(uuid.uuid4().hex),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        return jsonify(result)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "model": model, "backend": backend})

    return app


def start_api_server(model, backend, port=5000, url=None, prompt_mode="auto",
                     max_context=DEFAULT_MAX_CONTEXT,
                     max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                     host="127.0.0.1", timeout=DEFAULT_TIMEOUT):
    """Start the local API server. Use a trusted network before binding wider."""
    app = create_api_app(
        model=model,
        backend=backend,
        url=url,
        max_context=max_context,
        max_output_tokens=max_output_tokens,
        prompt_mode=prompt_mode,
        timeout=timeout,
    )
    print("Maya API server on http://{}:{} (model={}, backend={})".format(host, port, model, backend))
    app.run(host=host, port=port)


# ============================================================
# INTERACTIVE MODE AND MEMORY CONTROLS
# ============================================================
def _print_memory_help():
    print("Memory commands: :remember <note>, :memories, :forget <id>, :forget all, :help")


def _handle_memory_command(text, memory, memory_enabled, memory_items):
    """Handle a local memory command; return True when input was consumed."""
    if text == ":help":
        _print_memory_help()
        if not memory_enabled:
            print("Persistent memory is disabled for this session (--no-memory).")
        return True
    if text == ":memories":
        if not memory_enabled:
            print("Persistent memory is disabled for this session.")
        else:
            rows = memory.list_memories()
            if not rows:
                print("No saved memories.")
            else:
                for item in rows:
                    print("{}: {}".format(item["id"], item["content"]))
        return True
    if text == ":remember" or text.startswith(":remember "):
        note = text[len(":remember"):].strip()
        if not note:
            print("Usage: :remember <note>")
        elif not memory_enabled:
            print("Persistent memory is disabled for this session.")
        else:
            memory_id = memory.save_memory(note)
            memory_items.insert(0, note)
            del memory_items[5:]
            print("Saved memory #{} for this profile.".format(memory_id))
        return True
    if text == ":forget" or text.startswith(":forget "):
        target = text[len(":forget"):].strip().lower()
        if not memory_enabled:
            print("Persistent memory is disabled for this session.")
        elif target == "all":
            memory.clear_all()
            memory_items.clear()
            print("Cleared all saved memories, transcript rows, and mood state for this profile.")
        else:
            try:
                memory_id = int(target)
            except ValueError:
                print("Usage: :forget <id> or :forget all")
            else:
                if memory.delete_memory(memory_id):
                    memory_items[:] = memory.get_recent_memories()
                    print("Forgot memory #{}.".format(memory_id))
                else:
                    print("No saved memory with that id.")
        return True
    return False


def run_interactive(model, backend="ollama", url=None, prompt_mode="auto",
                    max_context=DEFAULT_MAX_CONTEXT,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                    memory_enabled=True, memory_db="maya_memory.db",
                    log_conversations=False, timeout=DEFAULT_TIMEOUT):
    """Run interactive chat with explicit, inspectable memory controls."""
    memory = MayaMemory(memory_db) if memory_enabled else None
    try:
        system_prompt = load_prompt(prompt_mode, max_context, max_output_tokens)
        memory_items = memory.get_recent_memories() if memory else []
        mood = memory.get_mood() if memory else None
        enhanced_system = compose_system_prompt(
            system_prompt, memory_items, mood, max_context, max_output_tokens
        )
        chat_fn = chat_openai if backend == "openai" else chat_ollama

        print("Maya v7.0 | prompt={}| memory={}".format(prompt_mode, "on" if memory_enabled else "off"))
        print("Model: {} | Backend: {} | Context: {} | Output reserve: {}".format(
            model, backend, max_context, max_output_tokens
        ))
        print("Type 'quit' to exit. Use :help for memory commands.\n")
        messages = list(MAYA_EXAMPLES)

        while True:
            try:
                user_input = input("\nyou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if not user_input:
                continue
            if user_input.startswith(":") and _handle_memory_command(
                    user_input, memory, memory_enabled, memory_items):
                if user_input == ":forget all":
                    mood = None
                enhanced_system = compose_system_prompt(
                    system_prompt, memory_items, mood, max_context, max_output_tokens
                )
                continue

            user_message = {"role": "user", "content": user_input}
            messages.append(user_message)
            trimmed = trim_context(
                messages,
                max_tokens=max_context,
                system_tokens=estimate_tokens(enhanced_system) + MESSAGE_OVERHEAD_TOKENS,
                reserved_tokens=max_output_tokens,
            )
            if not trimmed:
                messages.pop()
                print("That message does not fit the configured context budget. Try a shorter message or a larger --max-context.")
                continue
            final_messages = [{"role": "system", "content": enhanced_system}] + trimmed

            print("\nmaya: ", end="")
            try:
                response = chat_fn(
                    final_messages,
                    model=model,
                    stream=True,
                    url=url,
                    max_tokens=max_output_tokens,
                    timeout=timeout,
                )
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                messages.pop()
                print("\nBackend request failed: {}".format(exc))
                continue

            messages.append({"role": "assistant", "content": response})
            if memory and log_conversations:
                memory.log_message("user", user_input)
                memory.log_message("assistant", response)
    finally:
        if memory:
            memory.close()


# ============================================================
# COMMAND LINE
# ============================================================
def build_parser():
    parser = argparse.ArgumentParser(description="Maya Persona Loader")
    parser.add_argument("--model", default="mistral-small", help="Model name")
    parser.add_argument("--backend", choices=["ollama", "openai"], default="ollama",
                        help="Backend: Ollama or an OpenAI-compatible server")
    parser.add_argument("--url", default=None,
                        help="Backend base URL (Ollama: localhost:11434; OpenAI: localhost:1234/v1)")
    parser.add_argument("--api", action="store_true", help="Start the local OpenAI-style API server")
    parser.add_argument("--api-host", default="127.0.0.1",
                        help="API bind address; defaults to loopback, use wider binds only on trusted networks")
    parser.add_argument("--port", type=int, default=5000, help="API server port")
    parser.add_argument("--prompt", choices=["auto", "lean", "base", "full"], default="auto",
                        help="Prompt size: auto uses full only when enough context remains (default: auto)")
    parser.add_argument("--lean", dest="prompt", action="store_const", const="lean",
                        help="Compatibility shortcut for --prompt lean")
    parser.add_argument("--max-context", type=int, default=DEFAULT_MAX_CONTEXT,
                        help="Total model context budget, including prompt and output reserve (default: 8192)")
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS,
                        help="Maximum tokens reserved for one response (default: 512)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Backend request timeout in seconds (default: 180)")
    parser.add_argument("--memory-db", default="maya_memory.db",
                        help="SQLite profile database path (default: ./maya_memory.db)")
    parser.add_argument("--no-memory", action="store_true",
                        help="Do not read or write the SQLite memory database")
    parser.add_argument("--log-conversations", action="store_true",
                        help="Opt in to storing raw conversation turns in SQLite; off by default")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    for name, value in (("--max-context", args.max_context),
                        ("--max-output-tokens", args.max_output_tokens),
                        ("--timeout", args.timeout)):
        if value <= 0:
            parser.error("{} must be a positive integer".format(name))
    if not (1 <= args.port <= 65535):
        parser.error("--port must be between 1 and 65535")
    if args.no_memory and args.log_conversations:
        parser.error("--log-conversations cannot be used with --no-memory")

    if args.api:
        start_api_server(
            args.model, args.backend, args.port, args.url, args.prompt,
            args.max_context, args.max_output_tokens, args.api_host, args.timeout
        )
    else:
        run_interactive(
            args.model, args.backend, args.url, args.prompt,
            args.max_context, args.max_output_tokens,
            not args.no_memory, args.memory_db, args.log_conversations, args.timeout
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
