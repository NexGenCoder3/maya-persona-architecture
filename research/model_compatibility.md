# Model Compatibility Guide

## How Open-Source Models Handle Persona Prompts

Not all models are equal when it comes to character work. This guide covers which models work best with Maya's architecture and why.

---

## The Three Things That Matter

### 1. Instruction Following
Can the model actually follow complex system prompts? Some models ignore long system prompts or "forget" instructions after a few turns.

### 2. Creative Writing Quality  
Does the model produce natural, varied, human-sounding text? Or does it default to formal, repetitive patterns?

### 3. Persona Persistence
Does the model stay in character across a long conversation? Or does it drift back to "helpful assistant" mode after 5-10 messages?

---

## Model Rankings (2025-2026)

### Tier 1: Best for Maya

**Mistral Small (24B)**
- Instruction following: excellent
- Creative writing: excellent, naturally varied
- Persona persistence: very strong
- Notes: Mistral models are the community gold standard for roleplay/character work. They follow complex voice instructions well and produce genuinely varied output. The 24B size hits the sweet spot.
- Uncensored by default: mostly yes

**Qwen 2.5 (14B / 32B)**
- Instruction following: excellent (best in class)
- Creative writing: good, sometimes slightly formal
- Persona persistence: very strong
- Notes: Qwen excels at following detailed instructions precisely. May need temperature pushed to 0.9 to avoid slight formality. The 14B is great for mid-range hardware.
- Uncensored: needs community finetune (Eva Qwen, etc.)

**Dan's Personality Engine (24B)**
- Instruction following: excellent
- Creative writing: excellent
- Persona persistence: excellent
- Notes: literally built for character/persona work. Community finetune specifically designed for this use case.
- Uncensored: yes

### Tier 2: Good for Maya

**Llama 3.1 (8B / 70B)**
- Instruction following: good
- Creative writing: good at 70B, decent at 8B
- Persona persistence: moderate (drifts after 10-15 turns at 8B)
- Notes: The 8B is accessible but needs reinforcement. The 70B is excellent but requires serious hardware. Add the post_history_instructions to combat drift.
- Uncensored: needs community finetune

**Gemma 2 (9B / 27B)**
- Instruction following: good
- Creative writing: very good (Google trained it well for this)
- Persona persistence: moderate
- Notes: Strong creative output but can have formatting inconsistencies. Good choice if you want more "literary" Maya.
- Uncensored: partially, depends on version

**Nous Hermes 2 (10.7B)**
- Instruction following: very good
- Creative writing: good
- Persona persistence: strong
- Notes: Solid all-rounder. Good persona adherence. Community favorite for character work.
- Uncensored: yes

**Dolphin Mistral (7B)**
- Instruction following: good
- Creative writing: decent
- Persona persistence: moderate
- Notes: Lightweight and uncensored. Good for lower-end hardware. Voice quality won't be as nuanced as larger models but still works.
- Uncensored: yes (that's the point)

### Tier 3: Usable but Not Ideal

**Phi-3 (3.8B / 14B)**
- Instruction following: decent
- Creative writing: weak (tends toward formal/academic)
- Persona persistence: weak
- Notes: Microsoft's model is smart but writes like a textbook. Not ideal for casual, messy, human-sounding dialogue. Needs heavy temperature boosting.

**Llama 3.2 (1B / 3B)**
- Instruction following: limited
- Creative writing: limited
- Persona persistence: poor
- Notes: Too small for complex persona work. System prompt gets "forgotten" quickly. Only use if hardware is extremely limited.

---

## Key Settings Per Model

| Model | Temperature | Top-p | Rep Penalty | Context | Notes |
|-------|-------------|-------|-------------|---------|-------|
| Mistral Small | 0.85 | 0.92 | 1.15 | 8192 | Sweet spot |
| Qwen 2.5 14B | 0.90 | 0.92 | 1.12 | 8192 | Push temp higher |
| Llama 3.1 8B | 0.85 | 0.90 | 1.18 | 4096 | Higher rep penalty |
| Gemma 2 9B | 0.85 | 0.92 | 1.15 | 8192 | Standard |
| Dolphin Mistral | 0.88 | 0.92 | 1.15 | 4096 | Slightly higher temp |
| Nous Hermes 2 | 0.85 | 0.92 | 1.15 | 8192 | Standard |

---

## Common Issues and Fixes

### "She sounds too formal"
- Increase temperature by 0.05-0.1
- Add reinforcement in post_history_instructions: "lowercase. no periods. fragments. messy."
- Add more few-shot examples from /examples folder
- Try a different model (Mistral > Qwen for casual voice)

### "She breaks character after a few messages"
- Use the post_history_instructions field (gets injected every turn)
- Reduce context window if model is small (prevents prompt from being pushed out)
- Add periodic "[Stay in character as Maya. Lowercase. No em dashes.]" as system injection
- Consider a larger model (8B → 14B makes a big difference)

### "She uses em dashes anyway"
- Add to post_history_instructions: "CRITICAL: never use - (em dash). Use ... or , or line breaks."
- Some models are stubborn about this. Mistral is best at respecting the ban.
- If persistent: add a post-processing step that replaces - with ...

### "Responses are too short / too long"
- Too short: increase num_predict, add "respond in 2-4 sentences minimum"
- Too long: add "this is texting. keep it conversational length. not essays."
- The few-shot examples help calibrate expected length

### "She agrees with everything"
- This is a model alignment issue. More aligned models = more agreeable.
- Use less aligned models (Dolphin, Nous Hermes, Personality Engine)
- Reinforce in system prompt: "you have opinions. you disagree. you push back."
- The human_imperfection framework helps but the model needs to be capable

### "Memory doesn't work"
- This is a platform limitation, not a Maya issue
- For Ollama: conversation history is maintained within a session
- For SillyTavern: enable the lorebook + use the data bank for long-term memory
- For persistent memory across sessions: use SillyTavern with vector storage extension

---

## Platform-Specific Notes

### Ollama
- Best for: quick setup, persistent model creation
- Limitation: no built-in long-term memory across sessions
- Tip: use the Modelfile to create a permanent "maya" model

### SillyTavern
- Best for: full-featured experience with memory, lorebook, extensions
- Limitation: more complex setup
- Tip: import the JSON character card, enable lorebook, use vector storage for memory

### LM Studio
- Best for: simple GUI, easy model switching
- Limitation: no character card system, manual prompt pasting
- Tip: save the system prompt as a preset

### text-generation-webui
- Best for: advanced users who want full control
- Limitation: complex interface
- Tip: use instruction template + character card together

---

## Future-Proofing

New models drop constantly. When evaluating a new model for Maya:

1. Load the system prompt
2. Send: "hey what are you doing"
3. Check: is the response lowercase? no em dashes? varied length? casual?
4. Send: "I'm fine" (when context implies you're not)
5. Check: does she read the subtext? or take it at face value?
6. Send something she should disagree with
7. Check: does she push back? or agree?

If it passes all three, the model works. If it fails any, try adjusting temperature or switching models.
