"""Faithfulness gate — verify every claim has ontology-bound evidence.

Rules (structural, before any LLM eval):
  1. Every claim must have ≥1 evidence_id pointing at a known Evidence record.
  2. If the claim cites an OntologyID, that ID must appear in at least one cited
     evidence chunk's ontology_ids OR in its content (canonical syntax).
  3. Any numeric value mentioned in the claim must be present in at least one
     cited evidence chunk (string-level match; simple but catches the common
     "fabricated number" failure).
  4. Clinical-marked claims must cite authoritative- or peer_reviewed-tier sources.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .models import Claim, Evidence, OntologyID, Report


@dataclass
class FaithfulnessReport:
    total_claims: int
    verified_claims: int
    rejected: list[tuple[str, str]]  # (claim_id, reason)
    clinical_violations: list[str] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        if self.total_claims == 0:
            return 1.0
        return self.verified_claims / self.total_claims


_NUMBER_RX = re.compile(r"\b\d+(?:\.\d+)?\b")


class FaithfulnessGate:
    """Verify a `Report` against an evidence store; mark claims `verified` or not."""

    def verify(self, report: Report, evidence: list[Evidence]) -> FaithfulnessReport:
        by_id: dict[str, Evidence] = {e.id: e for e in evidence}
        total = 0
        verified = 0
        rejected: list[tuple[str, str]] = []
        clinical_violations: list[str] = []

        for section in report.sections:
            for claim in section.claims:
                total += 1
                reason = self._check(claim, by_id)
                if reason is None:
                    claim.verified = True
                    verified += 1
                    if claim.blocking_clinical:
                        if not self._has_strong_source(claim, by_id):
                            clinical_violations.append(claim.id)
                            claim.verified = False
                            claim.verification_note = "clinical claim lacks authoritative/peer_reviewed source"
                            verified -= 1
                            rejected.append((claim.id, claim.verification_note))
                else:
                    claim.verified = False
                    claim.verification_note = reason
                    rejected.append((claim.id, reason))

        report.faithfulness_ratio = (verified / total) if total else 1.0
        return FaithfulnessReport(
            total_claims=total,
            verified_claims=verified,
            rejected=rejected,
            clinical_violations=clinical_violations,
        )

    # ---- internals ------------------------------------------------------------

    @staticmethod
    def _check(claim: Claim, by_id: dict[str, Evidence]) -> Optional[str]:
        if not claim.evidence_ids:
            return "no evidence bound"
        # Resolve all evidence
        evs: list[Evidence] = []
        for eid in claim.evidence_ids:
            if eid not in by_id:
                return f"evidence id {eid!r} not found"
            evs.append(by_id[eid])

        # Ontology check
        for cid in claim.cited_ontology_ids:
            if not any(
                cid.canonical() in [o.canonical() for o in ev.ontology_ids]
                or cid.canonical() in ev.content
                for ev in evs
            ):
                return f"cited ontology id {cid.canonical()} not found in any cited evidence"

        # Number check
        for num in _NUMBER_RX.findall(claim.text):
            if not any(num in ev.content for ev in evs):
                return f"numeric value {num!r} not found in cited evidence"

        return None

    @staticmethod
    def _has_strong_source(claim: Claim, by_id: dict[str, Evidence]) -> bool:
        tiers = [
            by_id[eid].source.trust_tier for eid in claim.evidence_ids if eid in by_id
        ]
        return any(t in ("authoritative", "peer_reviewed") for t in tiers)
