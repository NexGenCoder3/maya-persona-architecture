#!/usr/bin/env python3
"""Compile Maya's base prompt and framework modules deterministically."""
import argparse
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def estimate_tokens(text):
    """Rough four-characters-per-token estimate for build reporting only."""
    return math.ceil(len(text) / 4) if text else 0


def _clean_markdown(text):
    return "\n".join(line.rstrip() for line in text.splitlines())


def assemble_prompt(frameworks_dir, persona_dir, selected_files=None):
    frameworks_path = Path(frameworks_dir).resolve()
    persona_path = Path(persona_dir).resolve()
    base_prompt_path = persona_path / "system_prompt.md"
    if not base_prompt_path.is_file():
        raise FileNotFoundError("Base prompt not found: {}".format(base_prompt_path))
    if not frameworks_path.is_dir():
        raise FileNotFoundError("Frameworks directory not found: {}".format(frameworks_path))

    if selected_files is None:
        selected_files = sorted(path.name for path in frameworks_path.glob("*.md"))
    compiled = _clean_markdown(base_prompt_path.read_text(encoding="utf-8"))
    compiled += "\n\n--- ARCHITECTURE MODULES ENABLED ---\n\n"
    for filename in selected_files:
        module_path = (frameworks_path / str(filename)).resolve()
        try:
            module_path.relative_to(frameworks_path)
        except ValueError as exc:
            raise ValueError("Module path must stay inside frameworks/: {}".format(filename)) from exc
        if module_path.suffix.lower() != ".md":
            raise ValueError("Framework module must be a Markdown file: {}".format(filename))
        if not module_path.is_file():
            raise FileNotFoundError("Framework module not found: {}".format(module_path))
        compiled += "## MODULE: {}\n".format(module_path.name.upper())
        compiled += _clean_markdown(module_path.read_text(encoding="utf-8")) + "\n\n"
    return compiled


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compile the Maya system prompt")
    parser.add_argument("--all", action="store_true",
                        help="Compatibility flag; all modules are included by default")
    parser.add_argument("--modules", nargs="+", metavar="FILE",
                        help="Compile only these Markdown files from frameworks/")
    parser.add_argument("--output", default="persona/compiled_system_prompt.md",
                        help="Output path, relative to the repository root by default")
    parser.add_argument("--check", action="store_true",
                        help="Check whether the output is current without writing it")
    args = parser.parse_args(argv)
    if args.all and args.modules:
        parser.error("--all and --modules cannot be used together")

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    modules = args.modules if args.modules else None
    try:
        compiled = assemble_prompt(BASE_DIR / "frameworks", BASE_DIR / "persona", modules)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    if args.check:
        if not output_path.is_file() or output_path.read_text(encoding="utf-8") != compiled:
            print("Compiled prompt is missing or out of date: {}".format(output_path))
            return 1
        print("Compiled prompt is current (~{} estimated tokens).".format(estimate_tokens(compiled)))
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(compiled, encoding="utf-8")
    print("Compiled to {} (~{} estimated tokens).".format(output_path, estimate_tokens(compiled)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
