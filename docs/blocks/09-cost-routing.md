# Helix-Bio Block 09 — Cost Routing

## Responsibility

Keep a per-query budget while spending tokens where they matter — planner and faithfulness-gate on strong models, ontology lookups + drafting on cheap models. Use [ReBalance](../../../docs/51-rebalance-efficient-reasoning.md) to steer reasoning depth per call rather than uniform verbosity.

## Tier table (April 2026 illustrative)

| Tier | Models | Purpose |
|---|---|---|
| strong | Opus-class / o-class | Query planner, faithfulness gate, dual-use router |
| medium | Sonnet-class | Section synthesis, neuro-symbolic residue check |
| cheap | Haiku-class | Relevance grading, ontology lookup, summarization |
| nano | Nano-class | Intent classifier, PII scan, router |

Every LLM call declares `purpose` and `importance`; the router picks the tier.

## Budget enforcement

- Per-query ceiling (default $2). Planner's pre-flight estimate must fit.
- On 70 % spend → preservation mode: downgrade medium → cheap where `importance=normal`.
- On 90 % → cut optional sections; planner signals the user.
- On 100 % → finalize partial report with explicit "budget exhausted" notice.

## ReBalance confidence-steering

For the faithfulness gate's structural checks, confidence signals drive iteration depth:

- **High variance token stream** during evidence reasoning → push toward deeper reasoning (more iterations).
- **Consistent overconfidence** on a brittle domain like variant fitness → push toward more tool use, not more text.

This is the training-free application of the ReBalance pattern to a specific reasoning shape.

## Caching

Ontology-ID resolutions cached aggressively (365-day TTL, invalidate on HGNC/UniProt version bump). Literature searches cached per 24 h. Anthropic/OpenAI prompt caching used on the stable system prompt + tool schemas.

## Failure modes

| Mode | Defense |
|---|---|
| Over-downgrade hurts quality | Faithfulness gate still strong; regression eval catches cliffs |
| Cache staleness on ontology updates | Invalidate on publisher version bump |
| Budget starvation mid-query | Graceful truncation; explicit note |
| Provider outage | Failover to secondary (Anthropic → OpenAI → cached-only) |

## Metrics

- `cost.spend_usd_per_query` p50/p95
- `cost.by_tier` distribution
- `cache.hit_rate` per source
- `cost.preservation_mode_trips`
- `rebalance.depth_distribution`
