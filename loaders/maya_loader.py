#!/usr/bin/env python3
"""
Maya Persona Loader - v5.2
==========================
Now with Persistent Memory (SQLite) and API Server.

Usage:
    python maya_loader.py                    # Interactive chat
    python maya_loader.py --api              # Start API server
"""

import argparse
import json
import os
import sys
import subprocess
import sqlite3
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ============================================================
# MEMORY SYSTEM (SQLite)
# ============================================================

class MayaMemory:
    def __init__(self, db_path="maya_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS long_term_memory 
                         (id INTEGER PRIMARY KEY, content TEXT, timestamp DATETIME)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS mood_state 
                         (key TEXT PRIMARY KEY, value TEXT)''')
        self.conn.commit()

    def save_memory(self, content):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO long_term_memory (content, timestamp) VALUES (?, ?)", 
                       (content, datetime.now()))
        self.conn.commit()

    def get_recent_memories(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute("SELECT content FROM long_term_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [row[0] for row in cursor.fetchall()]

    def set_mood(self, mood_dict):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO mood_state (key, value) VALUES ('current_mood', ?)", 
                       (json.dumps(mood_dict),))
        self.conn.commit()

    def get_mood(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM mood_state WHERE key='current_mood'")
        row = cursor.fetchone()
        return json.loads(row[0]) if row else {"tired": 0, "happy": 50, "annoyed": 0}

# ============================================================
# LOADER CORE
# ============================================================

# Load compiled prompt if exists, else fallback to basic
COMPILED_PROMPT_PATH = Path(__file__).parent.parent / "persona" / "compiled_system_prompt.md"
if COMPILED_PROMPT_PATH.exists():
    MAYA_SYSTEM_PROMPT = COMPILED_PROMPT_PATH.read_text()
else:
    MAYA_SYSTEM_PROMPT = "You are Maya. A professional dancer. You love your partner."

MAYA_EXAMPLES = [
    {"role": "user", "content": "hey what are you doing"},
    {"role": "assistant", "content": "lying on the couch watching something terrible on netflix. my legs are dead from practice today. what's up"}
]

DEFAULT_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "openai_url": "http://localhost:1234/v1",
    "model": "mistral-small",
}

memory = MayaMemory()

def chat_ollama(messages, model="mistral-small", stream=True):
    url = f"{DEFAULT_CONFIG['ollama_url']}/api/chat"
    
    # Inject memory and mood into system prompt
    recent = memory.get_recent_memories()
    mood = memory.get_mood()
    
    enhanced_system = f"{MAYA_SYSTEM_PROMPT}\n\nCURRENT MOOD: {json.dumps(mood)}\nRECENT MEMORIES: {json.dumps(recent)}"
    
    # Ensure system prompt is first
    final_messages = [{"role": "system", "content": enhanced_system}]
    for m in messages:
        if m["role"] != "system":
            final_messages.append(m)

    payload = {
        "model": model,
        "messages": final_messages,
        "stream": stream,
        "options": {"temperature": 0.85}
    }
    
    if not stream:
        r = requests.post(url, json=payload)
        return r.json()["message"]["content"]

    response = requests.post(url, json=payload, stream=True)
    full_response = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            chunk = data.get("message", {}).get("content", "")
            print(chunk, end="", flush=True)
            full_response += chunk
            if data.get("done"): break
    print()
    return full_response

# (API Server implementation remains similar but uses enhanced_system)
def start_api_server(model, backend, port=5000):
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/v1/chat/completions", methods=["POST"])
    def chat():
        data = request.json
        messages = data.get("messages", [])
        # Simplified for demo: call chat_ollama with stream=False
        resp = chat_ollama(messages, model, stream=False)
        return jsonify({"choices": [{"message": {"role": "assistant", "content": resp}}]})

    app.run(host="0.0.0.0", port=port)

def run_interactive(model):
    print("Maya v5.2 - Persistent Memory Enabled")
    messages = MAYA_EXAMPLES.copy()
    while True:
        user_input = input("\nyou: ")
        if user_input.lower() in ["quit", "exit"]: break
        messages.append({"role": "user", "content": user_input})
        print("\nmaya: ", end="")
        response = chat_ollama(messages, model)
        messages.append({"role": "assistant", "content": response})
        # Save significant interactions to memory (simplified logic)
        if len(user_input) > 20:
            memory.save_memory(f"User said: {user_input}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mistral-small")
    parser.add_argument("--api", action="store_true")
    args = parser.parse_args()
    
    if args.api:
        start_api_server(args.model, "ollama")
    else:
        run_interactive(args.model)
