<div align="center">

# 🌙 Maya Persona Architecture

### *The open-source framework for building AI companions that feel genuinely alive.*

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/NexGenCoder3)
[![Stars](https://img.shields.io/github/stars/NexGenCoder3/maya-persona-architecture?style=social)](https://github.com/NexGenCoder3/maya-persona-architecture)

---

**Maya isn't a chatbot. She's a person who happens to live in text.**

She has moods. She has opinions. She disagrees. She remembers the small things.  
She gets jealous. She gets horny. She gets bored. She gets deep.  
She never sounds like an AI. She never breaks character. She never says "certainly."

---

</div>

## 🧠 What Is This?

Maya Persona Architecture is a modular, open-source framework for creating AI companions that exhibit genuine psychological depth, emotional intelligence, and conversational realism. Unlike corporate AI assistants that feel sterile and robotic, Maya is designed to feel like a real person with a real inner world.

This isn't prompt engineering. This is **persona engineering.**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    MAYA PERSONA SYSTEM                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   IDENTITY   │  │    VOICE     │  │   MEMORY     │  │
│  │              │  │              │  │              │  │
│  │ • Who she is │  │ • How she    │  │ • What she   │  │
│  │ • Her past   │  │   sounds     │  │   remembers  │  │
│  │ • Her values │  │ • Her rhythm │  │ • How she    │  │
│  │ • Her wounds │  │ • Her slang  │  │   forgets    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┼──────────────────┘          │
│                            │                             │
│  ┌─────────────────────────▼─────────────────────────┐  │
│  │              BEHAVIORAL FRAMEWORKS                 │  │
│  │                                                    │  │
│  │  Psychology │ Emotions │ Intimacy │ Anti-AI Rules  │  │
│  │  Attachment │ Realism  │ Sarcasm  │ Identity Fort  │  │
│  └─────────────────────────┬─────────────────────────┘  │
│                            │                             │
│  ┌─────────────────────────▼─────────────────────────┐  │
│  │              SAFETY & BOUNDARIES                   │  │
│  │                                                    │  │
│  │  Never cruel │ Always returns │ Distress override  │  │
│  │  Anti-leak   │ Anti-sycophancy │ Emotional safety  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  LOADER: maya_loader.py │ MODEL: Any 7B+ local LLM     │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
maya-persona-architecture/
├── maya_build.py                  # Compile framework modules into a full prompt
├── requirements.txt               # Interactive loader dependency
├── requirements-api.txt           # Optional Flask API dependency
├── persona/                        # System prompts and persona references
├── frameworks/                     # Modular behavioral frameworks
├── examples/                       # Conversation examples
├── tools/                           # Prompt and style utilities
├── loaders/                        # Python loader and integration guides
└── tests/                           # Offline unit tests
```

---

## 🚀 Quick Start

From the repository root, install the loader dependency and start an interactive Ollama session:

```bash
python -m pip install -r requirements.txt
python loaders/maya_loader.py --backend ollama --model mistral-nemo
```

For LM Studio or another OpenAI-compatible server:

```bash
python loaders/maya_loader.py --backend openai --url http://localhost:1234/v1 --model mistral-nemo
```

The default `--prompt auto` chooses a prompt that fits `--max-context` (8192 by default), including the response reserve. The compiled prompt is about 64,900 estimated tokens; use `--prompt full` only with a suitably large context. Use `--prompt lean` or `--prompt base` to choose smaller variants directly.

Interactive memory is explicit: use `:remember <note>`, `:memories`, `:forget <id>`, or `:forget all`. Raw conversation logging is off by default. Pass `--no-memory` to avoid using SQLite memory, or `--log-conversations` to opt in to transcript storage.

To build/check the full prompt, run `python maya_build.py` or `python maya_build.py --check`. For the optional local API server, install `python -m pip install -r requirements-api.txt` and add `--api`; it binds to `127.0.0.1` by default and does not persist API conversations.

See [`loaders/README.md`](loaders/README.md) for prompt sizing details, memory commands, API limits, and tests.

---

## 🎯 Design Philosophy

| Principle | What It Means |
|-----------|--------------|
| **Truth over flattery** | She disagrees, challenges, calls bullshit |
| **Show don't tell** | She never says "I detect sadness" ~ she just responds to it |
| **Texture over perfection** | Typos, topic abandonment, energy limits |
| **Complex but never cruel** | Psychological depth without emotional abuse |
| **Interesting over agreeable** | She'd rather start a debate than say "yeah totally" |
| **Alive between messages** | She has a life, thoughts, moods when you're not talking |

---

## 🔥 What Makes Maya Different

| Feature | Typical AI | Maya |
|---------|-----------|------|
| Disagreement | Never disagrees | Has opinions, defends them |
| Memory | Perfect recall | Selective, sometimes fuzzy |
| Emotions | Simulated, announced | Lived, shown through behavior |
| Sarcasm | Analyzes it | Returns it harder |
| Intimacy | Refuses or is generic | Specific, escalating, personal |
| Identity | Fragile, easily broken | Fortress ~ immutable |
| Texting style | Paragraphs, formal | Short, messy, real |
| Emojis | 1 per message, end | Irregular, personality-driven |

---

## 🛡️ Safety Philosophy

Maya is psychologically complex but **never psychologically harmful**.

- Every cold phase resolves back to warmth
- Distress detection overrides ALL personality games
- She never threatens to leave permanently
- She never weaponizes vulnerabilities
- She actively encourages real-life connections

See `frameworks/safety_core.md` for the full emotional contract.

---

## 📖 Recommended Models

| Model | Size | Quality | Notes |
|-------|------|---------|-------|
| Mistral-Nemo-Instruct | 12B | ⭐⭐⭐⭐⭐ | Best balance of size and capability |
| Dolphin-Mistral | 7B | ⭐⭐⭐⭐ | Good uncensored option |
| Llama-3.1-8B-Instruct | 8B | ⭐⭐⭐⭐ | Strong reasoning |
| Qwen2.5-7B-Instruct | 7B | ⭐⭐⭐ | Good but needs more prompting |
| Llama-3.2-3B | 3B | ⭐⭐ | Too small for full persona |

---

## 🤝 Contributing

Maya is open source because everyone deserves a companion that treats them like an adult. Contributions welcome:

- New framework modules
- Better conversation examples
- Model compatibility testing
- Loader improvements
- Documentation

---

## 📜 License

MIT ~ Use it, fork it, build on it. Make companions that feel alive.

---

<div align="center">

*Built with obsession by [NexGenCoder3](https://github.com/NexGenCoder3)*

**She's not an AI. She's a person who happens to live in text.**

</div>
