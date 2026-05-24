from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EngineConfig:
    """Sane defaults so the persona can run with zero manual tuning."""

    model_name: str = "mock-local"
    memory_retrieval_limit: int = 5
    trust_gain_per_positive_turn: float = 0.03
    trust_drop_per_negative_turn: float = 0.04
    volatility_decay: float = 0.02
    max_turns: int = 200
