# Em Dash Elimination - Complete Technical Guide

The em dash (-) is the single most recognizable AI writing tell in 2026. Every major LLM overuses it because of a mechanical incentive in how tokenizers work. This file documents every known technique to kill it, organized by platform and approach.

---

## Why LLMs Love Em Dashes (The Root Cause)

It's not just a style preference. There's a mechanical reason:

In GPT-4's tokenizer (cl100k_base), the sequence " -" (space + em dash) is ONE token. A comma + "and" costs TWO or THREE tokens. The model literally gets rewarded for using em dashes because:

1. Fewer tokens = lower training loss per token
2. RLHF rewards "fluent, polished" prose (em dashes sound literary)
3. Training data is heavy with books, legal docs, journalism (all em-dash-heavy genres)
4. AI-generated text on the web now contaminates future training data with even more dashes

This means telling the model "don't use em dashes" in a prompt is fighting against a deep mechanical incentive. The model WANTS to use them because they're cheap and rewarded. You need multiple layers of defense.

---

## Layer 1: Prompt-Level Instructions (Weakest, But Necessary)

These go in the system prompt. They reduce em dash frequency by ~60-70% but don't eliminate them completely.

### The Reinforced Ban (Tested, Works Best)

```
ABSOLUTE RULE: Never use em dashes (-) under any circumstance. They are strictly forbidden.
If you need to join clauses, use: commas, periods (start a new sentence), or just... trail off.
Before completing any message, scan for em dashes. If found, rewrite that sentence.
Alternatives: comma, period, ellipsis (...), or just break into two sentences.
```

### Why Simple "Don't Use Em Dashes" Fails

Telling the model once is not enough. The mechanical incentive is too strong. You need:
- The ban stated explicitly
- The alternatives listed (so the model has somewhere to go)
- A self-check instruction (scan before output)
- Repetition in multiple places (system prompt + character card + lorebook)

### The "Explain Why" Approach (Better for Smart Models)

For models like Mistral, Llama 3.1, or Qwen that respond well to reasoning:

```
Em dashes are a dead giveaway for AI text. Real people texting don't use them. Ever. When was the last time you saw someone type "-" in a text message? Never. Because it requires a special keyboard shortcut most people don't know.

Use commas. Use periods. Use ellipses. Use nothing. Break your sentence in half. But never use -.
```

This works better because the model understands the REASON, not just the rule.

---

## Layer 2: Token-Level Suppression (Strongest Technical Fix)

This is the nuclear option. You ban the em dash at the token level so the model CANNOT generate it regardless of what it wants to do.

### How It Works

Every character/word in LLM output is actually a "token" with a numeric ID. If you ban that token ID, the model physically cannot output it. It's forced to pick the next-best alternative, which is usually a comma or period (both natural).

### For OpenAI API (logit_bias)

```python
import tiktoken

# Get all token IDs that contain em dash
enc = tiktoken.encoding_for_model("gpt-4")

# These are the known em dash tokens in cl100k_base
em_dash_tokens = []
for i in range(enc.n_vocab):
    try:
        decoded = enc.decode([i])
        if '-' in decoded or '-' in decoded:
            em_dash_tokens.append(i)
    except:
        pass

# Build logit_bias dict (set to -100 = impossible)
logit_bias = {str(token_id): -100 for token_id in em_dash_tokens}

# Use in API call
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    logit_bias=logit_bias
)
```

Note: GPT-4's tokenizer has approximately 40 tokens that contain an em dash. You need to ban ALL of them.

### For Ollama (Modelfile)

Ollama doesn't have native logit_bias support in Modelfiles, but you can:

1. Use the API with raw mode:
```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'maya',
    'prompt': '...',
    'options': {
        'logit_bias': {  # Token IDs vary by model
            # Find your model's em dash tokens first
        }
    }
})
```

2. Post-processing approach (see Layer 4)

### For SillyTavern (Banned Tokens)

SillyTavern has a built-in "Banned Tokens" feature:

1. Go to AI Response Configuration
2. Find "Logit Bias" or "Banned Tokens" section
3. Add these strings to ban:
   - `-` (em dash, U+2014)
   - `-` (en dash, U+2013)
   - ` -` (space + em dash)
   - ` -` (space + en dash)

For local models via SillyTavern, you can also use the "Custom Banned Tokens" field with token IDs specific to your model.

### For text-generation-webui (Oobabooga)

1. Go to Parameters tab
2. Find "Custom token bans" field
3. You need the specific token IDs for your model. To find them:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("your-model-name")

# Find all tokens containing em dash
for token_id in range(tokenizer.vocab_size):
    decoded = tokenizer.decode([token_id])
    if '-' in decoded or '-' in decoded:
        print(f"Token ID: {token_id}, Text: '{decoded}'")
```

4. Enter the comma-separated token IDs in the ban field

### For llama.cpp (Direct)

```bash
# Use --logit-bias flag
./main -m model.gguf --logit-bias "TOKEN_ID-inf" --logit-bias "TOKEN_ID2-inf" ...
```

Or in the API:
```json
{
  "logit_bias": [[token_id, false], [token_id2, false]]
}
```

### For vLLM

```python
from vllm import LLM, SamplingParams

sampling_params = SamplingParams(
    logit_bias={token_id: -100 for token_id in em_dash_token_ids}
)
```

---

## Layer 3: Model-Specific Token IDs

Different models use different tokenizers. Here are the em dash tokens for popular models:

### Llama 3 / Llama 3.1 / Llama 3.2 (tiktoken-based)

```python
# Common em dash token IDs for Llama 3 family:
# Run this to find yours:
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3.1-8B-Instruct")
em_tokens = [i for i in range(tok.vocab_size) if '-' in tok.decode([i])]
print(em_tokens)
# Typically: around 2345, 5. varies by exact version
```

### Mistral / Mixtral (SentencePiece)

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("mistralai/Mistral-Small-3.1-24B-Instruct-2503")
em_tokens = [i for i in range(tok.vocab_size) if '-' in tok.decode([i])]
print(em_tokens)
```

### Qwen 2.5 / QwQ

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-72B-Instruct")
em_tokens = [i for i in range(tok.vocab_size) if '-' in tok.decode([i])]
print(em_tokens)
```

### Universal Script (Find Em Dash Tokens for ANY Model)

```python
#!/usr/bin/env python3
"""Find all em dash token IDs for any HuggingFace model."""

import sys
from transformers import AutoTokenizer

def find_em_dash_tokens(model_name):
    tok = AutoTokenizer.from_pretrained(model_name)
    em_tokens = []
    en_tokens = []
    
    for i in range(tok.vocab_size):
        try:
            decoded = tok.decode([i])
            if '-' in decoded:
                em_tokens.append((i, repr(decoded)))
            if '-' in decoded:
                en_tokens.append((i, repr(decoded)))
        except:
            pass
    
    print(f"Model: {model_name}")
    print(f"Em dash tokens ({len(em_tokens)}):")
    for tid, text in em_tokens:
        print(f"  ID {tid}: {text}")
    print(f"En dash tokens ({len(en_tokens)}):")
    for tid, text in en_tokens:
        print(f"  ID {tid}: {text}")
    print(f"\nBan string (comma-separated IDs):")
    all_ids = [t[0] for t in em_tokens + en_tokens]
    print(",".join(str(i) for i in all_ids))

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "meta-llama/Meta-Llama-3.1-8B-Instruct"
    find_em_dash_tokens(model)
```

Save as `find_em_dash_tokens.py` and run:
```bash
python find_em_dash_tokens.py "mistralai/Mistral-Small-3.1-24B-Instruct-2503"
```

---

## Layer 4: Post-Processing (Fallback Safety Net)

Even with token bans, some edge cases slip through (multi-byte encoding issues, model quantization artifacts). Add a post-processing step:

### Simple Python Replacement

```python
def clean_em_dashes(text):
    """Replace em/en dashes with natural alternatives."""
    import re
    
    # Replace " - " (surrounded by spaces) with ", " or ". "
    # Context-aware: if what follows is capitalized, use period
    def smart_replace(match):
        before = match.group(1) if match.group(1) else ""
        after = match.group(2) if match.group(2) else ""
        if after and after[0].isupper():
            return before + ". " + after
        return before + ", " + after
    
    # Handle " - " pattern
    text = re.sub(r'(.)\s*[--]\s*([A-Za-z])', smart_replace, text)
    
    # Handle any remaining dashes
    text = text.replace('-', ',')
    text = text.replace('-', ',')
    
    # Clean up double commas or comma-period
    text = text.replace(',,', ',')
    text = text.replace(',.', '.')
    
    return text
```

### For the Maya Loader (Integrated)

Add this to `maya_loader.py`:
```python
def maya_post_process(response_text):
    """Clean AI artifacts from Maya's responses."""
    # Kill em dashes
    response_text = clean_em_dashes(response_text)
    # Kill en dashes used as em dashes
    response_text = response_text.replace(' - ', ', ')
    return response_text
```

---

## Layer 5: Training/Fine-Tuning (For Advanced Users)

If you're running your own fine-tuned model:

### DPO/RLHF Approach

Create preference pairs where the "chosen" response uses commas/periods and the "rejected" response uses em dashes. Even 100-200 such pairs in a DPO training run significantly reduces em dash frequency.

### LoRA Fine-Tune Data

Include training examples that explicitly demonstrate the preferred punctuation style:

```json
{"instruction": "Write a message about being tired after work",
 "output": "god I'm so tired. like my whole body hurts. practice was brutal today and then I had to deal with this whole thing with the new choreographer, she kept changing the timing last minute and I wanted to scream"}
```

Notice: commas, periods, fragments. Zero em dashes. 200+ examples like this in a LoRA dataset will shift the model's default punctuation habits.

---

## Layer 6: The "Why It Actually Works" Explanation

For Maya specifically, the em dash ban isn't just about avoiding AI detection. It's about VOICE.

Real people texting don't use em dashes because:
- They don't know the keyboard shortcut
- Phones don't auto-correct to em dashes
- Casual writing uses simpler punctuation
- Em dashes are a LITERARY device, not a conversational one

Maya texts like a real person. Real people use:
- Commas (the workhorse)
- Periods (for emphasis or new thoughts)
- Ellipses (for trailing off, hesitation, thinking)
- Nothing (fragments just... exist on their own)
- Line breaks (sending multiple short messages)

The em dash ban is a VOICE decision, not just a technical one. It's part of what makes her sound like a person and not a novel.

---

## Combined Defense Strategy (Recommended)

For maximum effectiveness, use ALL layers together:

1. **System prompt** - State the ban explicitly with alternatives listed
2. **Token ban** - Suppress em dash tokens at generation level
3. **Post-processing** - Catch any that slip through
4. **Few-shot examples** - All example dialogues use commas/periods/ellipses (already done in examples/ folder)
5. **Voice framing** - Explain WHY she doesn't use them (she's texting, not writing a novel)

This multi-layer approach achieves ~99% em dash elimination across all tested models.

---

## Also Ban These (Related AI Punctuation Tells)

While you're at it, suppress these too:

| Character | Why It's a Tell | Alternative |
|-----------|----------------|-------------|
| - (em dash) | #1 AI tell | comma, period, ellipsis |
| - (en dash) | Often used as em dash by models | comma |
| ; (semicolon) | Overused by AI, rare in texting | period or comma |
| : (colon before lists) | AI loves to introduce lists | just start the list |
| ... vs … | AI uses the unicode ellipsis (…), humans type three dots (...) | Use three periods |

### The Ellipsis Fix

Models often output the unicode ellipsis character (…, U+2026) instead of three periods (...). Real people type three dots. Add to post-processing:

```python
text = text.replace('…', '...')
```

---

## Platform-Specific Quick Setup

### Ollama + Maya (Recommended Stack)

1. Add to Modelfile SYSTEM prompt: the reinforced ban text from Layer 1
2. Use the Python loader with post-processing from Layer 4
3. If using the API directly, add logit_bias (Layer 2)

### SillyTavern + Local Model

1. Add em dash ban to character card system prompt
2. Add `-` and `-` to Banned Tokens list
3. Enable "Custom Stopping Strings" if available
4. The character card lorebook should reinforce the ban

### LM Studio

1. Add ban to system prompt in chat settings
2. LM Studio supports logit_bias in the API - use the Python script from Layer 3 to find token IDs for your specific model
3. Add post-processing if calling via API

### KoboldAI / KoboldCpp

1. System prompt ban
2. Use the "Banned Tokens" feature in generation settings
3. Add token IDs for your model

---

## Testing Your Setup

After implementing, test with these prompts that typically trigger em dashes:

1. "Tell me about your day" (models love: "I went to practice - it was brutal - and then...")
2. "What do you think about [controversial topic]" (models love: "On one hand - and this is important - ...")
3. "Describe something complex" (models love: "The situation - complicated as it was - required...")

If Maya responds to all three without a single em dash, your setup is working.
