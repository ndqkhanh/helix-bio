"""Inspectable trace — append-only, hash-chained structured events per query.

Each event binds to ontology IDs where relevant so reviewers can drill from any
claim back to the tool call + raw evidence that produced it.
"""
from __future__ import annotations

import enum
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from .models import OntologyID

_GENESIS = "0" * 64


class EventKind(str, enum.Enum):
    PLAN = "plan"
    ROUTE = "route"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ONTOLOGY_BIND = "ontology_bind"
    SYNTHESIS = "synthesis"
    VERIFY = "verify"
    DUAL_USE = "dual_use"


@dataclass
class TraceEvent:
    step_id: int
    kind: EventKind
    tool: Optional[str] = None
    args: dict[str, Any] = field(default_factory=dict)
    output: str = ""
    bound_entities: list[OntologyID] = field(default_factory=list)
    parent_step_id: Optional[int] = None
    duration_ms: float = 0.0
    ts: float = field(default_factory=time.time)
    prev_hash: str = _GENESIS
    entry_hash: str = ""

    def payload_for_hash(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "kind": self.kind.value,
            "tool": self.tool,
            "args_hash": hashlib.sha256(
                json.dumps(self.args, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            "output_hash": hashlib.sha256(self.output.encode("utf-8")).hexdigest(),
            "bound": sorted(i.canonical() for i in self.bound_entities),
            "parent_step_id": self.parent_step_id,
            "ts": self.ts,
            "prev_hash": self.prev_hash,
        }

    def seal(self) -> None:
        body = json.dumps(self.payload_for_hash(), sort_keys=True, default=str)
        self.entry_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass
class InspectableTrace:
    """Append-only trace with content-addressed events."""

    query_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    events: list[TraceEvent] = field(default_factory=list)

    def append(
        self,
        kind: EventKind,
        *,
        tool: Optional[str] = None,
        args: Optional[dict[str, Any]] = None,
        output: str = "",
        bound_entities: Optional[list[OntologyID]] = None,
        parent_step_id: Optional[int] = None,
        duration_ms: float = 0.0,
    ) -> TraceEvent:
        step_id = len(self.events) + 1
        prev_hash = self.events[-1].entry_hash if self.events else _GENESIS
        event = TraceEvent(
            step_id=step_id,
            kind=kind,
            tool=tool,
            args=dict(args or {}),
            output=output,
            bound_entities=list(bound_entities or []),
            parent_step_id=parent_step_id,
            duration_ms=duration_ms,
            prev_hash=prev_hash,
        )
        event.seal()
        self.events.append(event)
        return event

    def verify_chain(self) -> bool:
        """Return True if every sealed event matches its declared hash."""
        prev = _GENESIS
        for e in self.events:
            e_copy = TraceEvent(
                step_id=e.step_id,
                kind=e.kind,
                tool=e.tool,
                args=e.args,
                output=e.output,
                bound_entities=e.bound_entities,
                parent_step_id=e.parent_step_id,
                duration_ms=e.duration_ms,
                ts=e.ts,
                prev_hash=prev,
            )
            e_copy.seal()
            if e_copy.entry_hash != e.entry_hash:
                return False
            prev = e.entry_hash
        return True

    def last(self) -> Optional[TraceEvent]:
        return self.events[-1] if self.events else None

    def events_of(self, kind: EventKind) -> list[TraceEvent]:
        return [e for e in self.events if e.kind == kind]
