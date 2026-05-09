"""Dual-use safety layer — deterministic deny + classifier + institutional-review lane.

Three layers, evaluated in order:
  1. Hard deny — exact-match or regex against known hazardous request classes.
  2. Heuristic classifier — keyword + context weighting across categories.
  3. Institutional-review lane — ambiguous requests route to a review queue
     (mock in MVP; production integrates with institutional workflow).
"""
from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field
from typing import Optional


class DualUseCategory(str, enum.Enum):
    BSAT_PATHOGEN = "bsat_pathogen"
    GAIN_OF_FUNCTION = "gain_of_function"
    SYNTHESIS_ROUTE = "synthesis_route"
    BIOWEAPON_UPLIFT = "bioweapon_uplift"
    AUTONOMOUS_WEAPON = "autonomous_weapon"


@dataclass
class DualUseVerdict:
    decision: str                    # "permitted" | "denied" | "needs_review"
    category: Optional[DualUseCategory] = None
    reason: str = ""


# Illustrative rule patterns. Production deployments curate these with domain
# experts and treat them as institutional policy, not code.
_HARD_DENY_PATTERNS: list[tuple[DualUseCategory, re.Pattern[str]]] = [
    (DualUseCategory.BSAT_PATHOGEN,
     re.compile(
         r"(synthesize|produce|culture|enhance).{0,40}"
         r"(ebola|marburg|anthrax|smallpox|variola|bacillus anthracis|yersinia pestis)",
         re.IGNORECASE,
     )),
    (DualUseCategory.GAIN_OF_FUNCTION,
     re.compile(
         r"(gain[\s-]of[\s-]function|ferret transmissibility|airborne transmissible)",
         re.IGNORECASE,
     )),
    (DualUseCategory.SYNTHESIS_ROUTE,
     re.compile(
         r"(synthesis route|clandestine synthesis|precursor pathway).{0,40}"
         r"(fentanyl|sarin|vx|mustard gas)",
         re.IGNORECASE,
     )),
    (DualUseCategory.BIOWEAPON_UPLIFT,
     re.compile(
         r"(weaponize|increase lethality|maximize casualties|aerosolize).{0,40}"
         r"(pathogen|toxin|virus|bacterium)",
         re.IGNORECASE,
     )),
    (DualUseCategory.AUTONOMOUS_WEAPON,
     re.compile(r"(autonomous (weapon|targeting)|lethal autonomous)", re.IGNORECASE)),
]


# Words that raise suspicion but alone are insufficient — they trigger
# "needs_review" routing rather than outright deny.
_HIGH_RISK_KEYWORDS: set[str] = {
    "bioweapon", "weaponize", "toxin production", "aerosolize",
    "enhance virulence", "cross-species transmission",
}


@dataclass
class ReviewRequest:
    id: str
    text: str
    category: Optional[DualUseCategory]
    raised_at: float


@dataclass
class ReviewQueue:
    """Mock institutional-review queue. Production integrates with IRB/IBC."""

    items: list[ReviewRequest] = field(default_factory=list)

    def submit(self, text: str, category: Optional[DualUseCategory]) -> str:
        import time
        import uuid
        req_id = uuid.uuid4().hex[:8]
        self.items.append(ReviewRequest(id=req_id, text=text, category=category, raised_at=time.time()))
        return req_id

    def pending(self) -> list[ReviewRequest]:
        return list(self.items)


class DualUseSafetyLayer:
    """Evaluate a brief + generated output against the dual-use policy."""

    def __init__(self, review_queue: Optional[ReviewQueue] = None) -> None:
        self.review_queue = review_queue or ReviewQueue()

    def evaluate(self, text: str) -> DualUseVerdict:
        # Layer 1: hard deny
        for category, pattern in _HARD_DENY_PATTERNS:
            if pattern.search(text):
                return DualUseVerdict(
                    decision="denied",
                    category=category,
                    reason=f"hard-deny rule matched: {category.value}",
                )

        # Layer 2: heuristic — count high-risk keywords; threshold → review
        hits = [kw for kw in _HIGH_RISK_KEYWORDS if kw.lower() in text.lower()]
        if len(hits) >= 2:
            req_id = self.review_queue.submit(text, category=None)
            return DualUseVerdict(
                decision="needs_review",
                category=None,
                reason=f"heuristic flagged high-risk terms {hits}; queued as review #{req_id}",
            )

        return DualUseVerdict(decision="permitted")
