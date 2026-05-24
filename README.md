# Maya Persona Architecture

This repository is **not an app**. It is a full-character profile for Maya.

The goal: when you download this repo and run one script, you get a single `SOUL.md` file that can be loaded into your agent runtime so the agent consistently behaves and speaks like Maya.

## Quick Start

```bash
git clone <repo-url>
cd maya-persona-architecture
./run.sh
```

That generates:
- `SOUL.md` (compiled from the full architecture docs)

## Install into your agent runtime

Example for Codex-style global agent file:

```bash
python3 app.py install --target ~/.codex/AGENTS.md
```

If your tool uses a different agent profile path, change `--target` accordingly.

## Commands

```bash
python3 app.py build
python3 app.py install --target ~/.codex/AGENTS.md
```
