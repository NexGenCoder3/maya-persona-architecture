#!/usr/bin/env bash
set -euo pipefail

python3 app.py build

echo ""
echo "Done. Generated SOUL.md from the full repo."
echo "Use this to install for your agent runtime (example):"
echo "  python3 app.py install --target ~/.codex/AGENTS.md"
