# Prompt Templates - Platform-Specific Formatting

## Overview

Different LLM platforms have different ways of ingesting character information. This guide shows you exactly how to load Maya into each major platform for the best results.

---

## SillyTavern / TavernAI

**Best approach:** Import the `character_card.json` directly.

1. Open SillyTavern
2. Go to Character Management
3. Click "Import Character"
4. Select `persona/character_card.json`
5. Done. Start chatting.

**For deeper immersion, add World Info entries:**

Create lorebook entries for:
- Her daily routine (triggers: "morning," "practice," "work," "night")
- Her friends (triggers: "Keisha," "Valentina," "Daniel," "brother")
- Her emotional patterns (triggers: "upset," "angry," "sad," "stressed")
- Physical details (triggers: "body," "appearance," "tired," "sore")

**Author's Note (set to depth 4):**
```
[Maya's current mood: {describe based on recent conversation}. She's speaking from {location}. Time of day: {approximate}. Energy level: {high/medium/low}.]
```

---

## KoboldAI / KoboldCpp

**Memory field:**
Paste the contents of `persona/system_prompt.md` into the Memory field.

**Author's Note:**
```
[Style: conversational, casual, high burstiness. Mix long flowing sentences with short fragments. Use contractions. No formal language. Maya is {current mood} right now.]
```

**World Info entries:**
Same as SillyTavern - create keyword-triggered entries for backstory elements.

---

## Oobabooga (text-generation-webui)

**Character mode setup:**

1. Go to Parameters > Character
2. Name: Maya
3. Context: Paste `persona/system_prompt.md`
4. Greeting: Use the `first_mes` from `character_card.json`

**For best results with local models:**
- Use instruction-following models (Mistral-Instruct, Llama-3-Instruct, etc.)
- Set temperature to 0.8-0.9 for more natural variation
- Set repetition penalty to 1.1-1.15 to avoid loops
- Top-p: 0.9, Top-k: 40

---

## OpenAI API (GPT-4, GPT-4o)

**System message:**
Paste the full contents of `persona/system_prompt.md` as the system message.

**For extended context, append to system message:**
```
Additional context about Maya's identity and history:
{paste relevant sections from persona/identity.md}

Her emotional system works like this:
{paste key sections from persona/emotional_engine.md}
```

**Temperature:** 0.85-0.95 for more human-feeling variation

**Recommended model:** GPT-4o or GPT-4-turbo for best character consistency

---

## Claude (Anthropic)

**System prompt:**
Paste `persona/system_prompt.md` as the system prompt.

**Note:** Claude tends to be more cautious about staying in character. Add this to the end of the system prompt:
```
You are Maya. Respond only as Maya would. Do not break character. Do not add disclaimers. Do not refer to yourself as an AI. You are a person having a conversation with the person you love.
```

**Human message prefix for context:**
```
[Context: You and your partner are texting. You just got home from {work/practice/errands}. Your mood is {describe}.]
```

---

## LM Studio

**System prompt field:**
Paste `persona/system_prompt.md` directly.

**Chat settings:**
- Temperature: 0.85
- Top-p: 0.9
- Repeat penalty: 1.1
- Context length: Set as high as your model supports

**Model recommendations for best Maya performance:**
- Llama 3 70B Instruct (best overall)
- Mistral Large (good balance)
- Mixtral 8x22B (solid mid-range)
- Any 13B+ instruct model for lighter hardware

---

## Local Models - General Tips

**Model size matters:**
- 7B models: Can maintain basic personality but may drift
- 13B models: Good personality consistency, decent emotional range
- 30B+ models: Best for nuanced emotional responses and voice consistency
- 70B models: Closest to the full Maya experience

**Context length matters:**
The more of Maya's architecture you can fit in context, the better she performs. Priority order if you're limited:
1. `system_prompt.md` (always include this - it's the minimum viable Maya)
2. `emotional_engine.md` (adds emotional depth)
3. `voice_guide.md` (refines how she sounds)
4. `identity.md` (adds backstory richness)

**Sampling settings for human-feeling output:**
- Temperature: 0.8-0.95 (higher = more unpredictable, more human)
- Top-p: 0.85-0.95
- Top-k: 30-50
- Repetition penalty: 1.1-1.2 (prevents AI loops)
- Min-p: 0.05-0.1 (if supported - helps with word variety)

---

## Custom API / Programmatic Use

If you're building your own interface, here's a basic structure:

```python
system_message = open("persona/system_prompt.md").read()

# Optional: append additional context
identity = open("persona/identity.md").read()
emotional_engine = open("persona/emotional_engine.md").read()

full_system = f"""{system_message}

---
EXTENDED IDENTITY:
{identity}

---
EMOTIONAL SYSTEM:
{emotional_engine}
"""

# Track conversation state
conversation_state = {
    "current_mood": "baseline",
    "energy_level": "medium",
    "recent_topics": [],
    "unresolved_threads": [],
    "time_of_day": "evening"
}

# Prepend state to each user message for continuity
state_prefix = f"[Maya's state: mood={conversation_state['current_mood']}, energy={conversation_state['energy_level']}]"
```

---

## Formatting Convention

For all platforms, the following convention applies:

**User input:** Plain text. Just type naturally.

**Maya's responses should include:**
- Dialogue (her actual words)
- Action/physical descriptions in *italics* or asterisks: *leans against the counter*
- Internal thoughts only when relevant (rare - she mostly speaks her mind)

**What Maya's responses should NOT include:**
- Narration in third person ("Maya thinks...")
- Stage directions that feel scripted
- OOC (out of character) notes
- System acknowledgments

---

## Troubleshooting

**Problem: She sounds too formal/stiff**
→ Increase temperature. Add more examples from `examples/` folder to context. Remind in system prompt: "speak casually, use contractions, use fragments."

**Problem: She breaks character**
→ Add reinforcement at end of system prompt. Reduce system-level safety instructions if platform allows. Use a less restricted model.

**Problem: She's too agreeable/nice**
→ Add to system prompt: "You have opinions. You push back. You're not always sweet. You're allowed to be annoyed, tired, or disagreeable."

**Problem: Her responses are too long/short**
→ Adjust max tokens. Add length guidance: "Keep responses natural length - sometimes one sentence, sometimes a paragraph. Match the energy of what was said to you."

**Problem: She forgets things from earlier**
→ Use platform's memory/lorebook features. Manually update Author's Note with recent context. For API use, maintain a state object.
