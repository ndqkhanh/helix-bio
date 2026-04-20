# Helix-Bio Block 08 — Per-Researcher Memory

## Responsibility

Persist opt-in, consent-gated memory per researcher: preferred ontologies, typical audience, prior queries, accepted/rejected sources, standing exclusion lists (competitor patents, redacted targets). Off by default — activated only after explicit consent.

References: [docs/09 memory files](../../../docs/09-memory-files.md), [docs/47 adaptation survey T2](../../../docs/47-adaptation-of-agentic-ai-survey.md).

## Scope model

- **session** — cleared at end of query; holds entity IDs and partial draft.
- **researcher** — persistent per-user after explicit opt-in. Holds prefs, source ratings, prior briefs.
- **tenant / lab** — shared canonical facts across researchers in the same institution (e.g. "our internal KRAS mouse model is strain KC-1").
- **global** — public ontology caches only.

Cross-researcher memory sharing requires explicit authorization from both parties; cross-tenant is not supported.

## What is persisted (with consent)

- **Preferred identifier systems** — HGNC symbols vs UniProt ACs vs Ensembl IDs.
- **Audience defaults** — "bench scientist" vs "clinician" vs "regulatory reviewer".
- **Source trust adjustments** — per-user overrides ("I trust bioRxiv for structural biology; I do not trust it for clinical claims").
- **Exclusion lists** — competitor patents, un-publishable pathways, tenant-redacted targets.
- **Query history** — scoped-down questions with their briefs, so "similar to last month's KRAS query" warm-starts.

## What is explicitly NOT persisted

- Patient-identifiable information (HIPAA; automatically redacted at ingest).
- Raw experimental data the user uploaded (one-shot per session unless user commits).
- Dual-use flagged queries (purged at end of session regardless of consent).

## Hygiene

- Staleness decay: source-rating confidence drops with age.
- Right to erasure: researcher can purge entire memory scope via dashboard; audit log records purge event.
- Encryption at rest; per-tenant keys.

## Failure modes

| Mode | Defense |
|---|---|
| Stale memory misinforms | Decay + re-confirm on first use per session |
| Cross-researcher leak | Strict scope tags at query time |
| Consent bypass | Memory layer refuses writes when consent flag is off |
| PII infiltration | Ingest-path redactor; periodic sweep for regex-matching values |

## Metrics

- `memory.writes_per_researcher`
- `memory.prefs_applied_per_query`
- `memory.purge_events` by reason
- `memory.staleness_decay_events`
