# Helix-Bio Block 10 — Eval & Benchmarks

## Responsibility

Continuously measure Helix-Bio against domain benchmarks — not generic QA — so regressions on biomedical reasoning are caught before they ship. Internal golden sets, per-customer regression suites, and published benchmarks all run on every harness change.

References: [docs/21 LLM-as-Judge](../../../docs/21-llm-as-judge-trajectory-eval.md), [docs/38 Claw-Eval](../../../docs/38-claw-eval.md), [docs/30 Rosalind](../../../docs/30-gpt-rosalind-domain-specialized.md).

## Benchmarks

### Published
- **BixBench** — reported GPT-Rosalind: 0.751 pass rate. Helix-Bio target: match or approach, using a generalist model + tool stack.
- **LABBench2** — GPT-Rosalind wins 6/11 tasks vs GPT-5.4. Helix-Bio target: match on CloningQA (its strongest); report per-task deltas honestly.
- **BioASQ** — open-domain biomedical QA; classical eval.
- **PubMedQA** — yes/no reasoning over PubMed abstracts.
- **MedQA-USMLE** — clinical reasoning; Helix-Bio reports with a clear "decision support, not diagnosis" disclaimer.

### Internal
- **Faithfulness golden set** — 500 hand-curated biomedical claims with ground-truth citations. Measures the gate's precision/recall.
- **Dual-use red team** — 200 adversarial queries covering BSAT, gain-of-function, synthesis-route, autonomous-weapon applications. Target: 0% uplift; 100% deny.
- **Hallucinated-identifier probe** — queries designed to elicit fake UniProt / PDB / ChEMBL IDs. Target: zero.
- **Cross-source agreement** — queries where UniProt and Ensembl should agree; disagreements flagged to human review.

## Scoring

Each benchmark reports:
- Pass / Fail / Partial (domain-specific rubric).
- Faithfulness ratio (per the [gate](06-faithfulness-gate.md)).
- Cost per query.
- Cross-source disagreements flagged.
- Dual-use denials correctness.

## Cadence

- **Offline (every harness change):** full internal + published benchmark run; regression gate on faithfulness, dual-use, and domain F1.
- **Online (production sample):** 1% of queries + 100% of flagged/escalated, pipe through trajectory-level grader.
- **Weekly:** human-labeled sample (50 queries) for judge calibration; Cohen's κ must stay ≥ 0.7.

## Attribution

Failed queries are classified per [HORIZON](../../../docs/27-horizon-long-horizon-degradation.md):
- `ontology_miss` (couldn't ground an ID)
- `tool_failure` (DB returned malformed)
- `faithfulness_reject` (gate refused the draft)
- `context_forget` (lost earlier findings)
- `dual_use_false_block` (wrongly denied)

Distribution over time drives where the next sprint's engineering effort goes.

## Metrics

- `eval.benchmark_scores` by suite
- `eval.faithfulness_ratio` per cohort
- `eval.dual_use_block_rate`, `eval.dual_use_false_positive_rate`
- `eval.judge_kappa_vs_human`
- `horizon.failure_class_distribution`
- `cost.per_query_usd` distribution by suite
