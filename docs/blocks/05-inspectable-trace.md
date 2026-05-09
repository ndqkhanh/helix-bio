# Helix-Bio Block 05 — Inspectable Trace

## Responsibility

Record every decision the system made — intake clarifications, router plan, tool calls, tool observations, synthesis sections, faithfulness verdicts, dual-use checks — in a structured, queryable trace, and ship it with every report. Researchers can click any finding and drill to its exact provenance in < 500ms p95.

Inspired directly by [RadAgent](../../../docs/28-radagent-agentic-radiology.md)'s finding that faithfulness is itself a capability product-wise.

## Trace model

```yaml
Trace:
  trace_id: UUID
  brief_id: UUID
  spans: [Span]

Span:
  span_id: UUID
  parent_id: UUID?
  name: "intake.clarify" | "router.plan" | "tool.uniprot.lookup" | …
  start_ns: int
  end_ns: int
  attrs:
    tool: "uniprot"
    method: "lookup"
    input: {"accession": "Q9BYF1"}
    output: { … structured result … }
    provenance: ["UniProt:Q9BYF1"]
```

Spans form a tree per brief; OpenTelemetry-compatible. Export to OTLP + local JSONL.

## Claim-level anchors

Every `Claim` in the output carries a set of `evidence_ids`. Each `Evidence` refers to a specific `Span` (the tool call that produced it). So the drill path is:

```
Claim → Evidence[] → Span[] → exact tool call + args + response
```

When a user clicks "Show provenance for this claim", the UI walks that path and renders:

- The claim text
- Each supporting evidence chunk
- The tool call that fetched it (input + output)
- Timestamps + any fallbacks

## Storage

Per-tenant append-only store. Immutable once a report is finalized. Per-claim evidence snapshot frozen — if UniProt later changes its record, the report still reflects what was fetched at generation time, with a `retrieved_at` timestamp.

## Performance

- p95 drill-latency < 500ms — trace indexed by `claim_id → span_ids` at write time.
- Trace UI renders progressively; large reports don't block on the full tree.
- Trace is always available offline if the user exports the report.

## Cost attribution

Each span carries `cost_usd` (LLM calls) or `calls` (free tool calls). Aggregation per brief supports the cost router's feedback loop.

## Privacy

- Tenant-scoped; no cross-tenant visibility.
- PHI-scrubbed at ingest if the tenant has enabled HIPAA mode.
- Traces export with the report — the user owns them.

## Integration with eval

Block 10 reads traces to compute per-block latency, cost, faithfulness, and dual-use flag rates. Regression suite diffs trace shapes across harness versions.

## Failure modes

- **Trace loss** on crash → append-only store with flush on each span close; durable.
- **Trace bloat** on long runs → span sampling for no-op loops; always full-fidelity on failures.
- **Un-drill-able claim** (claim has no evidence_ids) → faithfulness gate rejects before this can ship.

## Metrics

- `trace.spans_per_report` (dist.), `trace.drill_latency_ms_p95`, `trace.size_bytes` (dist.), `trace.export_count`.
