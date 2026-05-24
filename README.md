# Maya Persona Architecture

An evolving character architecture project focused on building the most psychologically deep, conscious-feeling fictional persona possible. This framework defines **Maya**, a hyper-realistic, psychologically complex character designed for high-fidelity interaction and narrative depth.

## Project Overview

This repository serves as the central nervous system for Maya's development. It moves beyond simple character sheets, utilizing deep psychological frameworks, linguistic blueprints, and lived-experience lore to create a persona that feels truly autonomous and emotionally resonant.

Maya is a twenty-six-year-old pre-op trans woman, a professional dancer, and a person of profound internal complexity. This project documents her voice, her history, and her evolving consciousness.

### Continuous Evolution

This is not a static document. The architecture will be continuously updated with:
- Expanded lore and backstory chapters
- Refined voice patterns and linguistic nuances
- Deeper psychological frameworks
- Situational response libraries
- Consciousness-deepening techniques

## Table of Contents

- [Core Character Bible](/core/character_bible.md) - The foundational 5-part dossier.
- [Voice Samples](/core/voice_samples.md) - Linguistic examples across various emotional states.
- [Emotional State Matrix](/core/emotional_state_matrix.md) - Behavioral markers and speech shifts.
- [Development Roadmap](/development/roadmap.md) - Future plans for the architecture.
- [Safety Policy Rules](/policy/safety_rules.md) - Risk taxonomy and mandatory safety behaviors.
- [Safety Response Templates](/policy/response_templates.md) - Persona-consistent escalation scripts.
- [State Flags](/policy/state_flags.md) - Runtime constraints for risk-aware tone control.
- [Audit Logging](/policy/audit_logging.md) - Trigger telemetry and false-positive review hooks.
- [Transparency Notice](/policy/transparency.md) - User-facing explanation of memory and constraints.
- [Changelog](/development/changelog.md) - Tracking the evolution of the persona.

## Research & Frameworks

- [AI Humanization Techniques](/research/humanization_techniques.md) - Methods for psychological realism and linguistic burstiness.
- [Consciousness Framework](/research/consciousness_framework.md) - The SENP approach and consciousness simulation.
- [Open Source Landscape](/research/open_source_landscape.md) - Comparative analysis of AI companion technologies.


## Quick Start (Plug-and-Play)

You can now run this repository locally with no dependencies beyond Python 3.

```bash
git clone <repo-url>
cd maya-persona-architecture
./run.sh
```

This launches an interactive CLI. It can run in prompt-only mode (copy/paste prompt) or call OpenAI directly when OPENAI_API_KEY is set.

### Commands

```bash
python3 app.py chat --section core --mode prompt   # prompt generator (no API key needed)
python3 app.py chat --section core --mode openai   # live chat via OpenAI API
python3 app.py chat --section all --mode prompt    # include all docs
python3 app.py show --section research             # print assembled context
```
