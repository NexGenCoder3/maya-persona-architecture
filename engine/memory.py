from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

EmotionalWeightHook = Callable[[str, float], float]


@dataclass(slots=True)
class MemoryItem:
    text: str
    source: str
    valence: float = 0.0
    intensity: float = 0.5
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def score(self) -> float:
        recency = 1.0
        return (abs(self.valence) * 0.4) + (self.intensity * 0.6) * recency


class MemoryStore:
    """In-memory append/retrieve storage with emotional weighting hooks."""

    def __init__(self, weight_hook: EmotionalWeightHook | None = None) -> None:
        self._items: list[MemoryItem] = []
        self._weight_hook = weight_hook

    def append(self, text: str, source: str, *, valence: float = 0.0, intensity: float = 0.5) -> MemoryItem:
        item = MemoryItem(text=text.strip(), source=source, valence=valence, intensity=max(0.0, min(1.0, intensity)))
        self._items.append(item)
        return item

    def retrieve(self, query: str, *, limit: int = 5) -> list[MemoryItem]:
        q = query.lower().strip()
        ranked: list[tuple[float, MemoryItem]] = []

        for item in self._items:
            lexical = 1.0 if q and q in item.text.lower() else 0.2
            emotional = item.score
            score = (lexical * 0.65) + (emotional * 0.35)
            if self._weight_hook:
                score = self._weight_hook(item.text, score)
            ranked.append((score, item))

        ranked.sort(key=lambda row: row[0], reverse=True)
        return [item for _, item in ranked[:limit]]

    def latest(self, *, limit: int = 10) -> list[MemoryItem]:
        return self._items[-limit:]
