"""Helix-Bio: domain-specialized biomedical research agent.

Public API re-exports the pipeline-level + block-level primitives that make up the
walking-skeleton MVP. The organizing idea: strong generalist model + typed MCP-like
tools over authoritative biomedical databases + ontology-ID-bound outputs + a
faithfulness gate that refuses unsupported claims + a dual-use safety perimeter.
"""
from __future__ import annotations

from .dual_use import DualUseSafetyLayer, DualUseVerdict
from .faithfulness import FaithfulnessGate, FaithfulnessReport
from .memory import ResearcherMemory
from .models import (
    Brief,
    Claim,
    Evidence,
    Finding,
    OntologyID,
    Report,
    Section,
    SourceRef,
)
from .ontology import OntologyGrounder
from .pipeline import HelixPipeline, PipelineOutput
from .router import KnowledgeRouter, RoutingDecision
from .tools import (
    MockAlphaFold,
    MockBLAST,
    MockChEMBL,
    MockEnsembl,
    MockPDB,
    MockPubMed,
    MockUniProt,
    build_default_tools,
)
from .trace import InspectableTrace, TraceEvent

__all__ = [
    "Brief",
    "Claim",
    "DualUseSafetyLayer",
    "DualUseVerdict",
    "Evidence",
    "FaithfulnessGate",
    "FaithfulnessReport",
    "Finding",
    "HelixPipeline",
    "InspectableTrace",
    "KnowledgeRouter",
    "MockAlphaFold",
    "MockBLAST",
    "MockChEMBL",
    "MockEnsembl",
    "MockPDB",
    "MockPubMed",
    "MockUniProt",
    "OntologyGrounder",
    "OntologyID",
    "PipelineOutput",
    "Report",
    "ResearcherMemory",
    "RoutingDecision",
    "Section",
    "SourceRef",
    "TraceEvent",
    "build_default_tools",
]
