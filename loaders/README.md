# Run Maya with the Python loader

Run commands from the repository root. The interactive loader needs Python 3.8+ and `requests`; the optional local API mode also needs Flask.

```bash
python -m pip install -r requirements.txt
python loaders/maya_loader.py --backend ollama --model mistral-nemo
```

For an OpenAI-compatible local server such as LM Studio, use its chat API base URL:

```bash
python loaders/maya_loader.py \
  --backend openai \
  --url http://localhost:1234/v1 \
  --model mistral-nemo
```

## Prompt and context size

`--max-context` is the model's **total** context budget, not a history-only limit. It includes Maya's prompt, recent messages, message overhead, and the response allowance from `--max-output-tokens` (512 by default). The loader estimates tokens from text length, so actual tokenization can vary by model and language.

The default `--prompt auto` uses the compiled prompt only when it leaves room for output and conversation history. Otherwise it selects the lean prompt. At this checkout, the lean prompt is about 750 estimated tokens, the base prompt about 2,800, and the compiled prompt about 64,900. To choose a prompt explicitly:

```bash
python loaders/maya_loader.py --prompt lean --max-context 8192
python loaders/maya_loader.py --prompt base --max-context 8192
python loaders/maya_loader.py --prompt full --max-context 81920
```

`--lean` remains a shortcut for `--prompt lean`. History is dropped oldest-first; if the newest message by itself is too large, its oldest text is clipped with a marker. The loader does not keep extra messages when doing so would exceed its estimated budget.

Rebuild the full prompt from all framework modules (modules are sorted for repeatable output), or check whether the generated file is current:

```bash
python maya_build.py
python maya_build.py --check
```

Use `--modules memory_architecture.md safety_core.md` to compile a selected set of modules. The output defaults to `persona/compiled_system_prompt.md`.

## Memory and privacy controls

Interactive mode stores only notes you explicitly save. It does not automatically convert conversation text into long-term memories, and raw conversation logging is off by default. Memory is kept in a local SQLite database, `maya_memory.db` in the current working directory, as plaintext on disk.

While chatting, use:

- `:remember <note>` to save a note deliberately.
- `:memories` to inspect saved notes and their IDs.
- `:forget <id>` to delete one note.
- `:forget all` to delete all saved notes, transcript rows, and mood state in that profile database.
- `:help` to show the commands.

Use `--no-memory` to avoid reading or writing the database for a session. Raw conversation turns can be stored only if you explicitly pass `--log-conversations`; do not combine that option with `--no-memory`. Choose another `--memory-db /path/to/profile.db` to use a separate profile. Back up or remove the database only after the loader has exited.

## Local API mode

Install the optional API dependency and start the server:

```bash
python -m pip install -r requirements-api.txt
python loaders/maya_loader.py --api --backend openai --url http://localhost:1234/v1 --model mistral-nemo
```

The server listens on `127.0.0.1:5000` by default, supports non-streaming `POST /v1/chat/completions`, and reports process configuration at `GET /health`. It does not persist API conversations or use the interactive SQLite memory. Requests can contain `system`, `developer`, `user`, and `assistant` text messages; `stream: true` is rejected. The response follows the usual chat-completion envelope, with token counts marked as estimates.

The API server has no authentication. Keep it on loopback unless you have separately secured a trusted network. `--api-host 0.0.0.0` exposes it on all interfaces and should not be used on an untrusted or public network.

## Tests

The standard-library tests run without contacting a model backend:

```bash
python -m unittest discover -s tests -v
```

Flask API tests run when Flask is installed; otherwise those tests are skipped.
