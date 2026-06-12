#!/usr/bin/env python3
"""
Maya Framework Assembler
========================
Compiles modular framework files into a single deployable system prompt.

Usage:
    python maya_build.py --all                # Compile all frameworks
    python maya_build.py --config core.json   # Compile based on config
"""

import argparse
import os
from pathlib import Path

def assemble_prompt(frameworks_dir, persona_dir, selected_files=None):
    """Assemble the system prompt from selected framework files."""
    f_dir = Path(frameworks_dir)
    p_dir = Path(persona_dir)
    
    # Base prompt is always included
    base_prompt_path = p_dir / "system_prompt.md"
    if not base_prompt_path.exists():
        print(f"Error: {base_prompt_path} not found.")
        return ""
    
    compiled = base_prompt_path.read_text() + "\n\n"
    compiled += "--- ARCHITECTURE MODULES ENABLED ---\n\n"
    
    # If no files selected, take all .md files in frameworks
    if not selected_files:
        selected_files = [f.name for f in f_dir.glob("*.md")]
    
    for filename in selected_files:
        f_path = f_dir / filename
        if f_path.exists():
            print(f"Integrating module: {filename}")
            compiled += f"## MODULE: {filename.upper()}\n"
            compiled += f_path.read_text() + "\n\n"
        else:
            print(f"Warning: Framework file {filename} not found.")
            
    return compiled

def main():
    parser = argparse.ArgumentParser(description="Maya Framework Assembler")
    parser.add_argument("--all", action="store_true", help="Compile all frameworks")
    parser.add_argument("--output", default="persona/compiled_system_prompt.md", help="Output file path")
    
    args = parser.parse_args()
    
    frameworks_dir = "frameworks"
    persona_dir = "persona"
    
    if args.all:
        compiled = assemble_prompt(frameworks_dir, persona_dir)
        with open(args.output, "w") as f:
            f.write(compiled)
        print(f"✓ Compiled system prompt saved to {args.output}")
    else:
        print("Please specify --all or a config file (config not yet implemented).")

if __name__ == "__main__":
    main()
