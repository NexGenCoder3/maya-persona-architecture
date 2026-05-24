from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

Mood = Literal[
    "grounded",
    "warm",
    "playful",
    "reflective",
    "anxious",
    "defensive",
    "vulnerable",
]


@dataclass(slots=True)
class EmotionalSnapshot:
    """Rolling emotional metrics for the active conversation."""

    trust: float = 0.45
    volatility: float = 0.30
    relationship_depth: float = 0.20
    mood: Mood = "grounded"

    def clamp(self) -> None:
        self.trust = max(0.0, min(1.0, self.trust))
        self.volatility = max(0.0, min(1.0, self.volatility))
        self.relationship_depth = max(0.0, min(1.0, self.relationship_depth))


@dataclass(slots=True)
class RuntimeState:
    """Typed runtime state persisted during a single chat session."""

    turn_count: int = 0
    emotional: EmotionalSnapshot = field(default_factory=EmotionalSnapshot)
    current_topic: str = "getting_acquainted"
    recency_summary: list[str] = field(default_factory=list)
    salient_entities: dict[str, float] = field(default_factory=dict)
    last_user_message: str = ""
    last_assistant_message: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def register_turn(self, user_message: str, assistant_message: str) -> None:
        self.turn_count += 1
        self.last_user_message = user_message
        self.last_assistant_message = assistant_message
        self.updated_at = datetime.now(timezone.utc)

        summary_fragment = f"U: {user_message[:90]} | A: {assistant_message[:90]}"
        self.recency_summary.append(summary_fragment)
        self.recency_summary = self.recency_summary[-6:]

    def update_topic(self, topic: str) -> None:
        self.current_topic = topic.strip().lower().replace(" ", "_") or self.current_topic
