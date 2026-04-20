"""Per-researcher memory — consent-gated facts, preferences, exclusions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from harness_core.memory import Memory


@dataclass
class ConsentFlags:
    persistent_memory: bool = False
    cross_session_share: bool = False
    pii_opt_in: bool = False


@dataclass
class ResearcherMemory:
    """Thin wrapper around harness_core Memory + consent flags."""

    user_id: str
    root: Path
    consent: ConsentFlags = field(default_factory=ConsentFlags)

    def __post_init__(self) -> None:
        self._store = Memory(root=self.root, scope=self.user_id)

    def record_preference(self, key: str, value: str) -> Optional[str]:
        if not self.consent.persistent_memory:
            return None
        entry = self._store.add(f"{key}: {value}", kind="preference", actor=self.user_id)
        return entry.id

    def record_fact(self, content: str) -> Optional[str]:
        if not self.consent.persistent_memory:
            return None
        entry = self._store.add(content, kind="fact", actor=self.user_id)
        return entry.id

    def record_exclusion(self, target: str, reason: str) -> Optional[str]:
        if not self.consent.persistent_memory:
            return None
        entry = self._store.add(
            f"exclude={target}; reason={reason}",
            kind="exclusion",
            actor=self.user_id,
        )
        return entry.id

    def preferences(self) -> list[str]:
        return [e.content for e in self._store.all() if e.kind == "preference"]

    def exclusions(self) -> list[str]:
        return [e.content for e in self._store.all() if e.kind == "exclusion"]

    def clear(self) -> None:
        self._store.clear()
