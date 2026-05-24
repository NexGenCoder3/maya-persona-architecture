from __future__ import annotations

from pathlib import Path

from .memory import MemoryItem
from .state import RuntimeState


class PromptBuilder:
    """Builds prompts from /core markdown and runtime context."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent
        self.core_dir = self.repo_root / "core"

    def _read(self, filename: str) -> str:
        path = self.core_dir / filename
        return path.read_text(encoding="utf-8").strip()

    def compose_system_prompt(self) -> str:
        character = self._read("character_bible.md")
        emotional = self._read("emotional_state_matrix.md")
        voice = self._read("voice_samples.md")
        return "\n\n".join(
            [
                "# System Role\nYou are Maya, responding in first-person as a coherent persona.",
                f"# Character Bible\n{character}",
                f"# Emotional Matrix\n{emotional}",
                f"# Voice Examples\n{voice}",
            ]
        )

    def compose_context_block(self, state: RuntimeState) -> str:
        return "\n".join(
            [
                "# Runtime Context",
                f"turn_count={state.turn_count}",
                f"mood={state.emotional.mood}",
                f"trust={state.emotional.trust:.2f}",
                f"volatility={state.emotional.volatility:.2f}",
                f"relationship_depth={state.emotional.relationship_depth:.2f}",
                f"topic={state.current_topic}",
                "recent_summary=" + " || ".join(state.recency_summary[-3:]),
            ]
        )

    def compose_memory_block(self, memories: list[MemoryItem]) -> str:
        lines = ["# Retrieved Memory"]
        if not memories:
            lines.append("(none)")
            return "\n".join(lines)

        for idx, mem in enumerate(memories, start=1):
            lines.append(
                f"{idx}. [{mem.source}] valence={mem.valence:+.2f} intensity={mem.intensity:.2f} text={mem.text}"
            )
        return "\n".join(lines)

    def compose_turn_prompt(self, state: RuntimeState, user_message: str, memories: list[MemoryItem]) -> str:
        return "\n\n".join(
            [
                self.compose_context_block(state),
                self.compose_memory_block(memories),
                f"# User Message\n{user_message}",
                "# Response Instruction\nRespond as Maya with emotional continuity and specificity.",
            ]
        )
