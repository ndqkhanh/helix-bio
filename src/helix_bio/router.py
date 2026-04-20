"""Knowledge router — decides which tool(s) to invoke for a given sub-query.

Input: a `Brief` plus one grounded entity or query string.
Output: a sequence of `RoutingDecision`s naming tool + args.

Rules are deterministic for MVP; production swaps in an LLM-driven router.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Brief, OntologyID


@dataclass
class RoutingDecision:
    tool: str
    args: dict[str, Any]
    rationale: str = ""
    task_id: str = ""


@dataclass
class RoutingPlan:
    decisions: list[RoutingDecision] = field(default_factory=list)


class KnowledgeRouter:
    """Map grounded entities + free-text to a short pipeline of tool calls."""

    def plan_for_entity(self, oid: OntologyID) -> list[RoutingDecision]:
        """For a single ontology ID, propose tool calls that will produce evidence."""
        ns = oid.namespace
        val = oid.value
        if ns == "UniProt":
            return [
                RoutingDecision(
                    tool="uniprot_query",
                    args={"accession": val},
                    rationale="UniProt AC → fetch protein record",
                ),
                RoutingDecision(
                    tool="alphafold_fetch",
                    args={"accession": val},
                    rationale="AlphaFold available for UniProt AC",
                ),
            ]
        if ns == "PDB":
            return [
                RoutingDecision(
                    tool="pdb_query",
                    args={"pdb_id": val},
                    rationale="PDB ID → structure metadata",
                ),
            ]
        if ns == "ChEMBL":
            return [
                RoutingDecision(
                    tool="chembl_query",
                    args={"chembl_id": val},
                    rationale="ChEMBL compound lookup",
                ),
            ]
        if ns == "Ensembl":
            return [
                RoutingDecision(
                    tool="ensembl_query",
                    args={"ensembl_id": val},
                    rationale="Ensembl gene metadata",
                ),
            ]
        if ns == "HGNC":
            # HGNC doesn't have a direct mock tool; skip
            return []
        if ns == "MeSH":
            return []
        return []

    def plan_for_query(self, brief: Brief) -> list[RoutingDecision]:
        """Always include a literature search for the brief's question."""
        return [
            RoutingDecision(
                tool="pubmed_search",
                args={"query": brief.question, "max_results": 3},
                rationale="literature survey for the research question",
            ),
        ]

    def build_plan(
        self,
        brief: Brief,
        grounded: list[OntologyID],
    ) -> RoutingPlan:
        plan = RoutingPlan()
        for idx, oid in enumerate(grounded):
            for dec in self.plan_for_entity(oid):
                dec.task_id = f"E{idx+1}.{dec.tool}"
                plan.decisions.append(dec)
        for dec in self.plan_for_query(brief):
            dec.task_id = f"Q.{dec.tool}"
            plan.decisions.append(dec)
        return plan
