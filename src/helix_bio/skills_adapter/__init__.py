"""Helix-Bio skills adapter — ontology-bound document + dialogue extraction.

Trust tier is populated at extraction time from the source resolution
(PubMed → T1; bioRxiv → T2-PREPRINT; web → T3). The trust gate runs
upstream of the existing FaithfulnessGate so RED-tier rejections happen
before lexical checks. PHI gating runs at extraction time so identifiers
never enter the SkillBank.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from harness_skills import SkillRecord, TrustTier
from harness_skills.extract import DialogueExtractor, DocumentExtractor, ExtractionContext
from harness_skills.hooks.trust_gate import TrustGateHook
from harness_skills.store import SkillBank

# Loose regex for PHI shapes — DOB-like, MRN-like, SSN-like.
_PHI_RE = re.compile(
    r"\b(\d{3}-\d{2}-\d{4}|\d{2}/\d{2}/\d{4}|MRN[-:\s]*\d{4,}|patient[-_\s]*id[-:\s]*\d+)\b",
    re.IGNORECASE,
)


def phi_gate(text: str) -> bool:
    """Return True iff the text is safe to store (no PHI shapes detected)."""
    return _PHI_RE.search(text or "") is None


def resolve_trust_tier(source: str) -> TrustTier:
    """Map a source identifier to its starting trust tier."""
    s = (source or "").lower()
    if "pubmed" in s or "pmid:" in s or "doi:10.1056" in s:
        return TrustTier.T1_PEER_REVIEWED
    if "biorxiv" in s or "medrxiv" in s:
        return TrustTier.T2_PREPRINT
    if "http" in s:
        return TrustTier.T3_DISCUSSION
    return TrustTier.LEGACY


@dataclass
class HelixDocumentExtractor:
    extractor: DocumentExtractor

    @classmethod
    def default(cls) -> HelixDocumentExtractor:
        return cls(extractor=DocumentExtractor(family="extractor-helix"))

    def from_protocol(self, *, source: str, title: str, body: str,
                      session_id: str) -> list[SkillRecord]:
        if not phi_gate(body):
            return []
        records = self.extractor.extract(
            {"text": body, "title": title, "doi": source},
            context=ExtractionContext(session_id=session_id),
        )
        tier = resolve_trust_tier(source)
        # Re-tier each record per source resolution.
        return [
            SkillRecord(
                skill=r.skill,
                source_kind=r.source_kind,
                source_id=r.source_id,
                source_version=r.source_version,
                content_sha256=r.content_sha256,
                extraction_session_id=r.extraction_session_id,
                reviewer_verdict=r.reviewer_verdict,
                trust_tier=tier,
            ).with_hash()
            for r in records
            if phi_gate(r.skill.prompt)
        ]


@dataclass
class HelixResearcherPrefExtractor:
    extractor: DialogueExtractor

    @classmethod
    def default(cls) -> HelixResearcherPrefExtractor:
        return cls(extractor=DialogueExtractor(family="extractor-helix"))

    def from_session(self, turns: list[dict], *, researcher_id: str,
                     session_id: str) -> list[SkillRecord]:
        records = self.extractor.extract(
            turns,
            context=ExtractionContext(session_id=session_id, user_id=researcher_id),
        )
        return [r for r in records if phi_gate(r.skill.prompt)]


@dataclass
class HelixSkillBank:
    bank: SkillBank
    gate: TrustGateHook

    @classmethod
    def for_researcher(cls, root: Path | str, researcher_id: str) -> HelixSkillBank:
        return cls(
            bank=SkillBank(root=root, namespace=f"researchers/{researcher_id}"),
            gate=TrustGateHook(),
        )

    def admit(self, record: SkillRecord) -> tuple[bool, str]:
        return self.gate.evaluate(record)


__all__ = [
    "HelixDocumentExtractor",
    "HelixResearcherPrefExtractor",
    "HelixSkillBank",
    "phi_gate",
    "resolve_trust_tier",
]
