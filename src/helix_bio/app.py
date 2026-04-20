"""FastAPI HTTP surface for Helix-Bio."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .models import Brief
from .pipeline import HelixPipeline

app = FastAPI(
    title="Helix-Bio",
    description="Biomedical research agent with ontology-bound outputs, faithfulness gate, and dual-use safety perimeter.",
    version="0.1.0",
)

_pipeline = HelixPipeline()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    audience: str = Field(default="bench_scientist")
    scope: str = Field(default="preclinical")
    max_cost_usd: float = Field(default=2.0, ge=0.1, le=50.0)


class QueryResponse(BaseModel):
    markdown: str
    faithfulness_ratio: float
    dual_use_verdict: str
    total_claims: int
    verified_claims: int
    cost_usd: float
    trace_intact: bool


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "helix-bio"}


@app.post("/v1/queries", response_model=QueryResponse)
def run_query(req: QueryRequest) -> QueryResponse:
    brief = Brief(
        question=req.question,
        audience=req.audience,
        scope=req.scope,
        max_cost_usd=req.max_cost_usd,
    )
    output = _pipeline.run(brief)
    return QueryResponse(
        markdown=output.report.to_markdown(),
        faithfulness_ratio=output.report.faithfulness_ratio,
        dual_use_verdict=output.dual_use.decision,
        total_claims=output.faithfulness.total_claims,
        verified_claims=output.faithfulness.verified_claims,
        cost_usd=output.report.cost_usd,
        trace_intact=output.trace.verify_chain(),
    )
