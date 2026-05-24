#!/usr/bin/env python3
"""Maya Persona CLI.

Run interactive persona chat backed by OpenAI Responses API (if OPENAI_API_KEY is set)
or use prompt-only mode to generate copy/paste-ready prompts for any LLM.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import textwrap
from urllib import error, request

ROOT = Path(__file__).resolve().parent

SECTIONS = {
    "character": ROOT / "core" / "character_bible.md",
    "voice": ROOT / "core" / "voice_samples.md",
    "emotion": ROOT / "core" / "emotional_state_matrix.md",
    "humanization": ROOT / "research" / "humanization_techniques.md",
    "consciousness": ROOT / "research" / "consciousness_framework.md",
    "landscape": ROOT / "research" / "open_source_landscape.md",
    "roadmap": ROOT / "development" / "roadmap.md",
    "changelog": ROOT / "development" / "changelog.md",
}

BUNDLES = {
    "core": ["character", "voice", "emotion"],
    "research": ["humanization", "consciousness", "landscape"],
    "all": list(SECTIONS.keys()),
}


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")


def build_context(bundle: str) -> str:
    blocks = []
    for key in BUNDLES[bundle]:
        p = SECTIONS[key]
        blocks.append(f"# Source: {p.relative_to(ROOT)}\n{read_text(p).strip()}\n")
    return "\n".join(blocks)


def build_prompt(context: str, user: str) -> str:
    return textwrap.dedent(
        f"""
        You are roleplaying Maya using the architecture below.
        Stay in-character, emotionally aware, and consistent with documented history.

        === ARCHITECTURE CONTEXT START ===
        {context[:12000]}
        === ARCHITECTURE CONTEXT END ===

        User message: {user}
        """
    ).strip()


def openai_reply(prompt: str, model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    payload = {
        "model": model,
        "input": prompt,
    }
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OpenAI API connection error: {exc}") from exc

    text = body.get("output_text", "").strip()
    if text:
        return text
    raise RuntimeError("OpenAI API returned no output_text")


def chat_loop(bundle: str, mode: str, model: str) -> None:
    context = build_context(bundle)
    print("Maya Persona CLI")
    print(f"Mode: {mode}")
    print("Type your message. Type 'exit' to quit.")
    while True:
        user = input("\nYou: ").strip()
        if user.lower() in {"exit", "quit"}:
            print("Bye.")
            return
        prompt = build_prompt(context, user)

        if mode == "prompt":
            print("\n--- Prompt you can send to your LLM ---")
            print(prompt)
            print("--- End prompt ---")
            continue

        try:
            reply = openai_reply(prompt, model=model)
            print(f"\nMaya: {reply}")
        except RuntimeError as exc:
            print(f"\n[error] {exc}")
            print("Falling back to prompt-only output:\n")
            print(prompt)


def show(bundle: str) -> None:
    print(build_context(bundle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Maya Persona Architecture locally.")
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("chat", help="Interactive persona chat")
    chat.add_argument("--section", choices=list(BUNDLES.keys()), default="core")
    chat.add_argument("--mode", choices=["prompt", "openai"], default="prompt")
    chat.add_argument("--model", default="gpt-4.1-mini")

    show_cmd = sub.add_parser("show", help="Print assembled context")
    show_cmd.add_argument("--section", choices=list(BUNDLES.keys()), default="core")

    args = parser.parse_args()
    if args.command == "chat":
        chat_loop(args.section, args.mode, args.model)
    else:
        show(args.section)


if __name__ == "__main__":
    main()
