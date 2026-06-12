#!/usr/bin/env python3
"""
Maya Persona Loader v6.0
~ Persistent memory (SQLite)
~ Context window trimming (configurable)
~ Ollama + OpenAI-compatible backends
~ ChatML/Hermes template support
~ Lean prompt auto-selection for small models
"""
import argparse
import json
import os
import sqlite3
import requests
from pathlib import Path
from datetime import datetime

# ============================================================
# MEMORY SYSTEM (SQLite)
# ============================================================
class MayaMemory:
    def __init__(self, db_path="maya_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS long_term_memory 
                         (id INTEGER PRIMARY KEY, content TEXT, timestamp DATETIME)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS mood_state 
                         (key TEXT PRIMARY KEY, value TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS conversation_log
                         (id INTEGER PRIMARY KEY, role TEXT, content TEXT, timestamp DATETIME)''')
        self.conn.commit()

    def save_memory(self, content):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO long_term_memory (content, timestamp) VALUES (?, ?)", 
                       (content, datetime.now()))
        self.conn.commit()

    def get_recent_memories(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute("SELECT content FROM long_term_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [row[0] for row in cursor.fetchall()]

    def set_mood(self, mood_dict):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO mood_state (key, value) VALUES ('current_mood', ?)", 
                       (json.dumps(mood_dict),))
        self.conn.commit()

    def get_mood(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM mood_state WHERE key='current_mood'")
        row = cursor.fetchone()
        return json.loads(row[0]) if row else {"tired": 0, "happy": 50, "annoyed": 0}

    def log_message(self, role, content):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO conversation_log (role, content, timestamp) VALUES (?, ?, ?)",
                       (role, content, datetime.now()))
        self.conn.commit()


# ============================================================
# CONTEXT TRIMMING
# ============================================================
def estimate_tokens(text):
    """Rough token estimate: ~4 chars per token for English."""
    return len(text) // 4

def trim_context(messages, max_tokens=6000, system_tokens=0):
    """
    Trim conversation history to fit within context window.
    Keeps system prompt + most recent messages.
    Always preserves at least the last 4 exchanges.
    """
    available = max_tokens - system_tokens
    if available <= 0:
        return messages[-4:] if len(messages) > 4 else messages

    kept = []
    running_total = 0
    for msg in reversed(messages):
        msg_tokens = estimate_tokens(msg.get("content", ""))
        if running_total + msg_tokens > available and len(kept) >= 4:
            break
        kept.insert(0, msg)
        running_total += msg_tokens

    return kept


# ============================================================
# PROMPT LOADING
# ============================================================
BASE_DIR = Path(__file__).parent.parent

def load_prompt(use_lean=False):
    """Load system prompt. Use lean version for small context models."""
    if use_lean:
        lean_path = BASE_DIR / "persona" / "lean_system_prompt.md"
        if lean_path.exists():
            return lean_path.read_text()
    
    compiled_path = BASE_DIR / "persona" / "compiled_system_prompt.md"
    if compiled_path.exists():
        return compiled_path.read_text()
    
    base_path = BASE_DIR / "persona" / "system_prompt.md"
    if base_path.exists():
        return base_path.read_text()
    
    return "You are Maya. A professional dancer. You love your partner."


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
# CHATML / HERMES TEMPLATE
# ============================================================
def format_chatml(messages):
    """Format messages in ChatML/Hermes template."""
    output = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        output += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    output += "<|im_start|>assistant\n"
    return output


# ============================================================
# BACKENDS
# ============================================================
def chat_ollama(messages, model="mistral-small", stream=True, url=None):
    """Chat via Ollama API."""
    url = url or "http://localhost:11434"
    endpoint = f"{url}/api/chat"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {"temperature": 0.85, "top_p": 0.9, "repeat_penalty": 1.1}
    }
    
    if not stream:
        r = requests.post(endpoint, json=payload)
        return r.json()["message"]["content"]
    
    response = requests.post(endpoint, json=payload, stream=True)
    full_response = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            chunk = data.get("message", {}).get("content", "")
            print(chunk, end="", flush=True)
            full_response += chunk
            if data.get("done"):
                break
    print()
    return full_response


def chat_openai(messages, model="mistral-small", stream=True, url=None):
    """Chat via OpenAI-compatible API (LM Studio, text-gen-webui, etc.)."""
    url = url or "http://localhost:1234/v1"
    endpoint = f"{url}/chat/completions"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.85,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "stream": stream,
    }
    
    if not stream:
        r = requests.post(endpoint, json=payload, headers=headers)
        data = r.json()
        return data["choices"][0]["message"]["content"]
    
    response = requests.post(endpoint, json=payload, headers=headers, stream=True)
    full_response = ""
    for line in response.iter_lines():
        if line:
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                line_str = line_str[6:]
            if line_str.strip() == "[DONE]":
                break
            try:
                data = json.loads(line_str)
                chunk = data["choices"][0].get("delta", {}).get("content", "")
                print(chunk, end="", flush=True)
                full_response += chunk
            except (json.JSONDecodeError, KeyError):
                continue
    print()
    return full_response


# ============================================================
# API SERVER
# ============================================================
def start_api_server(model, backend, port=5000, url=None, use_lean=False, max_context=6000):
    """Start Flask API server for external integrations."""
    from flask import Flask, request as flask_request, jsonify
    app = Flask(__name__)
    
    system_prompt = load_prompt(use_lean=use_lean)
    chat_fn = chat_openai if backend == "openai" else chat_ollama

    @app.route("/v1/chat/completions", methods=["POST"])
    def chat():
        data = flask_request.json
        messages = data.get("messages", [])
        
        system_tokens = estimate_tokens(system_prompt)
        trimmed = trim_context(messages, max_tokens=max_context, system_tokens=system_tokens)
        final_messages = [{"role": "system", "content": system_prompt}] + trimmed
        
        resp = chat_fn(final_messages, model, stream=False, url=url)
        return jsonify({"choices": [{"message": {"role": "assistant", "content": resp}}]})

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "model": model, "backend": backend})

    print(f"Maya API server starting on port {port} (model={model}, backend={backend})")
    app.run(host="0.0.0.0", port=port)


# ============================================================
# INTERACTIVE MODE
# ============================================================
def run_interactive(model, backend="ollama", url=None, use_lean=False, max_context=6000, use_chatml=False):
    """Run interactive chat session."""
    memory = MayaMemory()
    system_prompt = load_prompt(use_lean=use_lean)
    
    recent = memory.get_recent_memories()
    mood = memory.get_mood()
    enhanced_system = system_prompt
    if recent:
        enhanced_system += f"\n\nTHINGS YOU REMEMBER: {json.dumps(recent)}"
    enhanced_system += f"\nCURRENT MOOD STATE: {json.dumps(mood)}"
    
    system_tokens = estimate_tokens(enhanced_system)
    chat_fn = chat_openai if backend == "openai" else chat_ollama
    
    print("Maya v6.0 ~ Persistent Memory | Context Trimming | Multi-Backend")
    print(f"Model: {model} | Backend: {backend} | Lean: {use_lean} | Max Context: {max_context}")
    print("Type 'quit' to exit\n")
    
    messages = MAYA_EXAMPLES.copy()
    
    while True:
        user_input = input("\nyou: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        
        messages.append({"role": "user", "content": user_input})
        memory.log_message("user", user_input)
        
        trimmed = trim_context(messages, max_tokens=max_context, system_tokens=system_tokens)
        final_messages = [{"role": "system", "content": enhanced_system}] + trimmed
        
        print("\nmaya: ", end="")
        response = chat_fn(final_messages, model, stream=True, url=url)
        
        messages.append({"role": "assistant", "content": response})
        memory.log_message("assistant", response)
        
        if len(user_input) > 20:
            memory.save_memory(f"He said: {user_input}")
        if len(response) > 50:
            memory.save_memory(f"I told him: {response[:100]}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Maya Persona Loader v6.0")
    parser.add_argument("--model", default="mistral-small", help="Model name")
    parser.add_argument("--backend", choices=["ollama", "openai"], default="ollama",
                        help="Backend: ollama or openai (LM Studio, text-gen-webui)")
    parser.add_argument("--url", default=None, 
                        help="Custom API URL (default: localhost:11434 for ollama, localhost:1234 for openai)")
    parser.add_argument("--api", action="store_true", help="Start as API server")
    parser.add_argument("--port", type=int, default=5000, help="API server port")
    parser.add_argument("--lean", action="store_true", 
                        help="Use lean prompt (recommended for models with <32k context)")
    parser.add_argument("--max-context", type=int, default=6000,
                        help="Max context tokens for conversation history (default: 6000)")
    parser.add_argument("--chatml", action="store_true",
                        help="Use ChatML/Hermes message template")
    
    args = parser.parse_args()
    
    if args.api:
        start_api_server(args.model, args.backend, args.port, args.url, args.lean, args.max_context)
    else:
        run_interactive(args.model, args.backend, args.url, args.lean, args.max_context, args.chatml)
