#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

def assemble_prompt(frameworks_dir, persona_dir, selected_files=None):
    f_dir = Path(frameworks_dir)
    p_dir = Path(persona_dir)
    base_prompt_path = p_dir / "system_prompt.md"
    if not base_prompt_path.exists():
        return "Error: base prompt not found"
    compiled = base_prompt_path.read_text() + "\n\n--- ARCHITECTURE MODULES ENABLED ---\n\n"
    if not selected_files:
        selected_files = [f.name for f in f_dir.glob("*.md")]
    for filename in selected_files:
        f_path = f_dir / filename
        if f_path.exists():
            compiled += f"## MODULE: {filename.upper()}\n" + f_path.read_text() + "\n\n"
    return compiled

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output", default="persona/compiled_system_prompt.md")
    args = parser.parse_args()
    if args.all:
        compiled = assemble_prompt("frameworks", "persona")
        with open(args.output, "w") as f: f.write(compiled)
        print(f"Compiled to {args.output}")

if __name__ == "__main__":
    main()
