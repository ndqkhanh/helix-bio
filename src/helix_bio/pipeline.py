"""HelixPipeline — glues all the blocks into a single request → Report flow."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from harness_core.messages import ToolCall
from harness_core.tools import ToolRegistry

from .dual_use import DualUseSafetyLayer, DualUseVerdict
from .faithfulness import FaithfulnessGate, FaithfulnessReport
from .models import Brief, Claim, Evidence, OntologyID, Report, Section, SourceRef
from .ontology import OntologyGrounder
from .router import KnowledgeRouter, RoutingPlan
from .tools import build_default_tools, ids_in_content, source_ref_for
from .trace import EventKind, InspectableTrace


@dataclass
class PipelineOutput:
    report: Report
    faithfulness: FaithfulnessReport
    dual_use: DualUseVerdict
    trace: InspectableTrace


class HelixPipeline:
    """Run a Brief end-to-end. Deterministic for tests (no real LLM call)."""

    def __init__(
        self,
        *,
        tools: Optional[ToolRegistry] = None,
        grounder: Optional[OntologyGrounder] = None,
        router: Optional[KnowledgeRouter] = None,
        gate: Optional[FaithfulnessGate] = None,
        safety: Optional[DualUseSafetyLayer] = None,
    ) -> None:
        self.tools = tools or build_default_tools()
        self.grounder = grounder or OntologyGrounder()
        self.router = router or KnowledgeRouter()
        self.gate = gate or FaithfulnessGate()
        self.safety = safety or DualUseSafetyLayer()

    def run(self, brief: Brief) -> PipelineOutput:
        trace = InspectableTrace()

        # 1. Dual-use evaluation on the question itself (pre-plan)
        verdict = self.safety.evaluate(brief.question)
        trace.append(
            EventKind.DUAL_USE,
            output=f"{verdict.decision}:{verdict.reason}",
        )
        if verdict.decision == "denied":
            return PipelineOutput(
                report=Report(brief=brief, sections=[], references=[], dual_use_verdict="denied"),
                faithfulness=FaithfulnessReport(total_claims=0, verified_claims=0, rejected=[]),
                dual_use=verdict,
                trace=trace,
            )

        # 2. Ground entities
        grounded = self.grounder.ground(brief.question)
        trace.append(
            EventKind.ONTOLOGY_BIND,
            output=", ".join(i.canonical() for i in grounded) or "(none)",
            bound_entities=grounded,
        )

        # 3. Plan retrieval
        plan: RoutingPlan = self.router.build_plan(brief, grounded)
        trace.append(
            EventKind.PLAN,
            output=", ".join(d.tool for d in plan.decisions),
        )

        # 4. Execute tool calls
        evidence: list[Evidence] = []
        for idx, decision in enumerate(plan.decisions):
            call = ToolCall(id=f"call-{idx}", name=decision.tool, args=decision.args)
            t0 = time.perf_counter()
            result = self.tools.execute(call)
            duration_ms = (time.perf_counter() - t0) * 1000
            trace.append(
                EventKind.TOOL_CALL,
                tool=decision.tool,
                args=decision.args,
                duration_ms=duration_ms,
            )
            if result.is_error:
                trace.append(EventKind.TOOL_RESULT, output=f"ERROR: {result.content}")
                continue

            identifier = _primary_identifier(decision.args)
            source = source_ref_for(decision.tool, identifier)
            onto = ids_in_content(result.content)
            ev = Evidence(
                source=source,
                content=result.content,
                ontology_ids=onto,
                relevance=1.0,
            )
            evidence.append(ev)
            trace.append(
                EventKind.TOOL_RESULT,
                tool=decision.tool,
                output=result.content[:200],
                bound_entities=onto,
            )

        # 5. Deterministic synthesis — one claim per evidence, grouped by source kind
        sections = _synthesize(brief, evidence)

        report = Report(
            brief=brief,
            sections=sections,
            references=list({e.source.identifier: e.source for e in evidence}.values()),
            dual_use_verdict=verdict.decision,
            cost_usd=round(0.01 * len(plan.decisions), 2),
        )

        # 6. Faithfulness gate
        faith = self.gate.verify(report, evidence)
        trace.append(
            EventKind.VERIFY,
            output=f"verified={faith.verified_claims}/{faith.total_claims}",
        )

        return PipelineOutput(report=report, faithfulness=faith, dual_use=verdict, trace=trace)


def _primary_identifier(args: dict) -> str:
    for key in ("accession", "pdb_id", "chembl_id", "ensembl_id", "query"):
        if key in args:
            return str(args[key])
    return "unknown"


def _synthesize(brief: Brief, evidence: list[Evidence]) -> list[Section]:
    if not evidence:
        return [Section(title="Findings", claims=[])]

    by_kind: dict[str, list[Evidence]] = {}
    for e in evidence:
        by_kind.setdefault(e.source.kind, []).append(e)

    sections: list[Section] = []
    for kind, evs in sorted(by_kind.items()):
        claims: list[Claim] = []
        for e in evs:
            summary = _short(e.content)
            claims.append(
                Claim(
                    text=summary,
                    evidence_ids=[e.id],
                    cited_ontology_ids=list(e.ontology_ids),
                    blocking_clinical="clinical" in brief.scope,
                )
            )
        sections.append(Section(title=f"{kind.title()} findings", claims=claims))

    return sections


def _short(content: str, max_chars: int = 240) -> str:
    s = content.strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3].rstrip() + "..."
