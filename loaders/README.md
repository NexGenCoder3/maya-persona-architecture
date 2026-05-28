# Loaders — Get Maya Running in 60 Seconds

Pick your platform. Follow the steps. Done.

---

## Option 1: Ollama (Easiest)

**Requirements:** [Ollama](https://ollama.com) installed and running

```bash
# Step 1: Pull a base model (pick one)
ollama pull mistral-small        # best quality/speed balance
ollama pull llama3.1:8b          # lighter, still good
ollama pull qwen2.5:14b          # best instruction following

# Step 2: Create Maya as a persistent model
ollama create maya -f ./Modelfile

# Step 3: Chat
ollama run maya
```

That's it. Maya is now a model on your system. Run `ollama run maya` anytime.

---

## Option 2: Python Script (Works with anything)

**Requirements:** Python 3.8+, Ollama OR any OpenAI-compatible API

```bash
# Install dependency
pip install requests

# Run with Ollama
python maya_loader.py

# Run with a specific model
python maya_loader.py --model llama3.1:8b

# Run with LM Studio / text-gen-webui / any OpenAI-compatible API
python maya_loader.py --backend openai --url http://localhost:1234/v1

# Create persistent Ollama model from script
python maya_loader.py --create

# List available models
python maya_loader.py --list-models
```

---

## Option 3: SillyTavern

**Requirements:** [SillyTavern](https://github.com/SillyTavern/SillyTavern) installed

1. Copy `maya_sillytavern.json` to your SillyTavern characters folder
2. Or: In SillyTavern, go to Characters → Import → select the JSON file
3. Select Maya from your character list
4. Start chatting

The JSON includes:
- Full character description
- System prompt override
- Post-history instructions (jailbreak slot)
- 4 alternate greetings
- Lorebook with 8 context entries (plants, family, work, food, etc.)
- Recommended model settings in extensions

---

## Option 4: LM Studio

1. Open LM Studio
2. Load any supported model (Mistral, Llama 3, Qwen recommended)
3. Go to Chat → System Prompt
4. Paste the contents of the `SYSTEM` block from the Modelfile
5. Set temperature to 0.85, top-p to 0.92
6. Start chatting

---

## Option 5: text-generation-webui (Oobabooga)

1. Load your model
2. Go to Parameters → Instruction Template → Custom system message
3. Paste the system prompt from Modelfile
4. Set temperature: 0.85, top_p: 0.92, repetition_penalty: 1.15
5. Go to Chat → Character → create new character
6. Paste the description from the SillyTavern JSON into the character fields
7. Start chatting

---

## Option 6: KoboldAI / KoboldCpp

1. Load model
2. Settings → Memory → paste system prompt
3. Author's Note → paste: "[Maya speaks in lowercase, never uses em dashes, varies sentence length wildly, has moods that persist, and responds to emotional subtext not surface words]"
4. Start chatting

---

## Recommended Models (Ranked)

| Model | Size | Quality | Speed | Notes |
|-------|------|---------|-------|-------|
| Mistral Small 24B | 24B | ★★★★★ | ★★★ | Best overall for Maya |
| Qwen 2.5 14B | 14B | ★★★★☆ | ★★★★ | Excellent instruction following |
| Llama 3.1 8B | 8B | ★★★☆☆ | ★★★★★ | Good for lower-end hardware |
| Gemma 2 9B | 9B | ★★★★☆ | ★★★★ | Strong creative writing |
| Dolphin Mistral 7B | 7B | ★★★☆☆ | ★★★★★ | Uncensored, lightweight |
| Nous Hermes 2 10.7B | 10.7B | ★★★★☆ | ★★★★ | Great persona adherence |
| Dan's Personality Engine 24B | 24B | ★★★★★ | ★★★ | Built for characters |

**Minimum hardware:**
- 8B models: 8GB RAM / 6GB VRAM
- 14B models: 16GB RAM / 10GB VRAM  
- 24B models: 32GB RAM / 16GB VRAM

---

## Tuning Tips

If Maya sounds too formal:
- Increase temperature to 0.9
- Add to system prompt: "remember: lowercase. no periods at end. fragments. be messy."

If Maya breaks character:
- Lower temperature to 0.8
- Add more few-shot examples from the /examples folder
- Use the post_history_instructions field to reinforce voice

If responses are too short:
- Increase num_ctx / context window
- Add: "write at least 2-3 sentences per response unless the moment calls for brevity"

If responses are too long:
- Add: "keep responses conversational length. this is texting, not essay writing."
