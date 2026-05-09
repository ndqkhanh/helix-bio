"""Helix-Bio data model — all pydantic.

Entities carry canonical ontology identifiers whenever a database record is involved.
The faithfulness gate uses these structural identifiers (not metadata strings) to
verify every claim against cited evidence.
"""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class Brief(BaseModel):
    """User-scoped research question."""

    question: str
    audience: str = "bench_scientist"   # bench_scientist | clinician | regulatory
    scope: str = "preclinical"          # preclinical | translational | clinical
    max_cost_usd: float = 2.0
    target_length_words: int = 1500
    time_window_years: Optional[int] = None


class OntologyID(BaseModel):
    """A canonical identifier from an authoritative biomedical ontology."""

    namespace: str   # UniProt | HGNC | MeSH | ChEMBL | Ensembl | PDB
    value: str       # e.g. P01116, 6407, D021103, CHEMBL25, ENSG00000133703, 2OCJ

    def canonical(self) -> str:
        return f"{self.namespace}:{self.value}"

    def __str__(self) -> str:
        return self.canonical()


class SourceRef(BaseModel):
    """Handle pointing at an authoritative source record."""

    kind: str                  # uniprot | pdb | alphafold | pubmed | chembl | ensembl | blast
    identifier: str            # URL / accession / DOI / arXiv ID
    title: str = ""
    trust_tier: str = "authoritative"   # authoritative | peer_reviewed | preprint | web
    published_at: Optional[str] = None


class Evidence(BaseModel):
    """A chunk of retrieved content with ontology bindings."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source: SourceRef
    content: str
    ontology_ids: list[OntologyID] = Field(default_factory=list)
    relevance: float = 1.0


class Claim(BaseModel):
    """A statement in the final report, bound to evidence and ontology IDs."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    text: str
    evidence_ids: list[str]                        # must be non-empty
    cited_ontology_ids: list[OntologyID] = Field(default_factory=list)
    verified: bool = False
    verification_note: str = ""
    blocking_clinical: bool = False                # claim concerns clinical decisions


class Section(BaseModel):
    title: str
    claims: list[Claim]


class Report(BaseModel):
    """Final output of the Helix pipeline."""

    brief: Brief
    sections: list[Section]
    references: list[SourceRef]
    faithfulness_ratio: float = 1.0
    dual_use_verdict: str = "permitted"
    cost_usd: float = 0.0

    def to_markdown(self) -> str:
        lines = [f"# {self.brief.question}", ""]
        cite_index: dict[str, int] = {}
        counter = 1
        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            for claim in section.claims:
                nums: list[int] = []
                for eid in claim.evidence_ids:
                    if eid not in cite_index:
                        cite_index[eid] = counter
                        counter += 1
                    nums.append(cite_index[eid])
                cite_str = " " + ",".join(f"[{n}]" for n in nums) if nums else ""
                onto_str = ""
                if claim.cited_ontology_ids:
                    onto_str = " (" + ", ".join(str(i) for i in claim.cited_ontology_ids) + ")"
                suffix = "" if claim.verified else " *(unverified)*"
                lines.append(f"- {claim.text}{onto_str}{cite_str}{suffix}")
            lines.append("")
        lines.append("## References")
        lines.append("")
        for ref in self.references:
            tier = f" [{ref.trust_tier}]"
            lines.append(f"- {ref.kind}: [{ref.title or ref.identifier}]({ref.identifier}){tier}")
        lines.append("")
        lines.append(
            f"*faithfulness: {self.faithfulness_ratio:.0%}; "
            f"dual-use: {self.dual_use_verdict}; cost: ${self.cost_usd:.2f}*"
        )
        return "\n".join(lines)


class Finding(BaseModel):
    """A structured finding — used by non-report outputs (e.g. target scoring)."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str
    body: str
    cited_ontology_ids: list[OntologyID] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.5
