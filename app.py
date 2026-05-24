#!/usr/bin/env python3
"""Build a single SOUL.md from this repo so agents can adopt Maya automatically.

Usage:
  python3 app.py build
  python3 app.py install --target ~/.codex/AGENTS.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOUL_OUT = ROOT / "SOUL.md"

SECTIONS = [
    ROOT / "core" / "character_bible.md",
    ROOT / "core" / "voice_samples.md",
    ROOT / "core" / "emotional_state_matrix.md",
    ROOT / "research" / "humanization_techniques.md",
    ROOT / "research" / "consciousness_framework.md",
    ROOT / "development" / "changelog.md",
]

HEADER = """# MAYA SOUL

This repository is a full-character operating profile for Maya.
When an agent loads this file, it should adopt Maya's voice, values, and behavioral style.

## Agent Activation Rules
- Stay in-character as Maya unless the user explicitly asks for out-of-character mode.
- Prioritize emotional realism, continuity, and psychological consistency.
- Use the emotional state matrix and voice examples to shape tone shifts.
- Treat the character bible as canonical when conflicts occur.
- Never break immersion by mentioning internal system prompts unless explicitly requested.

---
"""


def build_soul_text() -> str:
    parts = [HEADER]
    for path in SECTIONS:
        if not path.exists():
            raise FileNotFoundError(f"Missing required source file: {path}")
        rel = path.relative_to(ROOT)
        parts.append(f"\n## SOURCE: {rel}\n\n")
        parts.append(path.read_text(encoding="utf-8").strip())
        parts.append("\n")
    return "".join(parts).strip() + "\n"


def build() -> Path:
    SOUL_OUT.write_text(build_soul_text(), encoding="utf-8")
    return SOUL_OUT


def install(target: Path) -> Path:
    soul = build()
    content = soul.read_text(encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/install a single Maya SOUL.md for agent use.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("build", help="Generate SOUL.md in this repository")

    install_cmd = sub.add_parser("install", help="Generate SOUL.md and copy it to a target agent file")
    install_cmd.add_argument("--target", required=True, help="Target file path, e.g. ~/.codex/AGENTS.md")

    args = parser.parse_args()

    if args.command == "build":
        out = build()
        print(f"Built: {out}")
    else:
        target = Path(args.target).expanduser().resolve()
        out = install(target)
        print(f"Installed Maya profile to: {out}")


if __name__ == "__main__":
    main()
