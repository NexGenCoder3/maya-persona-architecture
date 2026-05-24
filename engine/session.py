from __future__ import annotations

from dataclasses import dataclass

from .config import EngineConfig
from .memory import MemoryStore
from .prompt_builder import PromptBuilder
from .state import RuntimeState


@dataclass
class PersonaSession:
    config: EngineConfig
    prompt_builder: PromptBuilder
    memory: MemoryStore
    state: RuntimeState

    @classmethod
    def create_default(cls) -> "PersonaSession":
        return cls(
            config=EngineConfig(),
            prompt_builder=PromptBuilder(),
            memory=MemoryStore(),
            state=RuntimeState(),
        )

    def step(self, user_message: str) -> str:
        memories = self.memory.retrieve(user_message, limit=self.config.memory_retrieval_limit)
        _prompt = self.prompt_builder.compose_turn_prompt(self.state, user_message, memories)

        assistant_message = self._generate_reply(user_message)
        self._update_state(user_message, assistant_message)

        self.memory.append(user_message, source="user", valence=self._infer_valence(user_message), intensity=0.5)
        self.memory.append(assistant_message, source="maya", valence=0.1, intensity=0.4)
        return assistant_message

    def loop(self) -> None:
        print("Maya is online. Type 'exit' to quit.")
        while self.state.turn_count < self.config.max_turns:
            user_input = input("you> ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("maya> I'll be here when you return.")
                break
            if not user_input:
                continue
            reply = self.step(user_input)
            print(f"maya> {reply}")

    def _generate_reply(self, user_message: str) -> str:
        mood = self.state.emotional.mood
        return f"I hear you. ({mood}) You said: {user_message}"

    def _update_state(self, user_message: str, assistant_message: str) -> None:
        valence = self._infer_valence(user_message)
        if valence >= 0:
            self.state.emotional.trust += self.config.trust_gain_per_positive_turn
        else:
            self.state.emotional.trust -= self.config.trust_drop_per_negative_turn
            self.state.emotional.volatility += 0.05

        self.state.emotional.volatility = max(0.0, self.state.emotional.volatility - self.config.volatility_decay)
        self.state.emotional.relationship_depth += 0.015
        self.state.emotional.clamp()
        self.state.register_turn(user_message, assistant_message)

    @staticmethod
    def _infer_valence(text: str) -> float:
        lowered = text.lower()
        positive = any(tok in lowered for tok in ["love", "thanks", "happy", "safe", "good"])
        negative = any(tok in lowered for tok in ["hate", "angry", "mad", "upset", "bad"])
        if positive and not negative:
            return 0.5
        if negative and not positive:
            return -0.5
        return 0.0
