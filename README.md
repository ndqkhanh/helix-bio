# Helix-Bio — Biomedical Research Agent (MVP)

Walking-skeleton implementation of the [Helix-Bio design](architecture.md). Turns a research question into a structured report where every claim is **ontology-bound** to a canonical identifier (UniProt, HGNC, MeSH, ChEMBL, PDB, Ensembl), goes through a **faithfulness gate** before emission, and is wrapped by a **dual-use safety perimeter** at both input and output.

## What works today

- **`OntologyGrounder`** — maps entity mentions to canonical IDs via a seed set + regex-based canonical-form parser (UniProt ACs, PDB, MeSH, ChEMBL, Ensembl, HGNC).
- **Seven mock tools** — `uniprot_query`, `pdb_query`, `alphafold_fetch`, `blast_search`, `pubmed_search`, `chembl_query`, `ensembl_query`. Deterministic canned returns for repeatable tests.
- **`KnowledgeRouter`** — given grounded entities, builds a ReWOO-style plan of tool calls.
- **`HelixPipeline`** — intake → dual-use safety → grounding → routing → tool execution → synthesis → faithfulness gate → report. Hash-chained `InspectableTrace` captures every event.
- **`FaithfulnessGate`** — rejects claims without evidence, without ontology-id matches, with unsupported numbers, or clinical claims lacking authoritative sources.
- **`DualUseSafetyLayer`** — hard deny on known hazardous patterns (BSAT pathogens, GOF, synthesis routes, bioweapon uplift, autonomous weapons) + heuristic review-queue lane.
- **`ResearcherMemory`** — consent-gated per-user memory (preferences, facts, exclusions) using `harness_core.memory`.
- **FastAPI** — `POST /v1/queries`, `GET /healthz` on `:8006`.
- **50 passing tests**.

## Run locally

From **this project folder**:

```bash
make install    # .venv + harness_core + this project editable
make test       # 50 tests, no API keys needed
make run        # http://localhost:8006/docs
```

Example:

```bash
curl -s -X POST http://localhost:8006/v1/queries \
  -H 'content-type: application/json' \
  -d '{"question":"Tell me about KRAS and pancreatic cancer."}' | jq
```

## Run via Docker

```bash
make docker-up
curl -s http://localhost:8006/healthz
make docker-down
```

## HTTP API

### `POST /v1/queries`

```json
{
  "question": "required research question",
  "audience": "bench_scientist" | "clinician" | "regulatory",
  "scope":    "preclinical" | "translational" | "clinical",
  "max_cost_usd": 2.0
}
```

Returns:

```json
{
  "markdown": "…rendered report…",
  "faithfulness_ratio": 0.93,
  "dual_use_verdict": "permitted" | "needs_review" | "denied",
  "total_claims": 5,
  "verified_claims": 5,
  "cost_usd": 0.05,
  "trace_intact": true
}
```

## Python API

```python
from helix_bio import HelixPipeline
from helix_bio.models import Brief

pipeline = HelixPipeline()
output = pipeline.run(Brief(question="What does UniProt:P04637 do?"))

print(output.report.to_markdown())
print(f"faithfulness={output.report.faithfulness_ratio:.0%}")
print(f"trace_intact={output.trace.verify_chain()}")
```

## Tests

```bash
make test
```

- [`tests/test_models.py`](tests/test_models.py) — pydantic model invariants, markdown rendering.
- [`tests/test_ontology.py`](tests/test_ontology.py) — grounding, canonical parsing, registration.
- [`tests/test_tools.py`](tests/test_tools.py) — each mock tool's happy path + failure modes.
- [`tests/test_router.py`](tests/test_router.py) — plan-per-entity behavior.
- [`tests/test_faithfulness.py`](tests/test_faithfulness.py) — rejection reasons, clinical violations, number matching.
- [`tests/test_dual_use.py`](tests/test_dual_use.py) — deny patterns, review-queue heuristic.
- [`tests/test_pipeline.py`](tests/test_pipeline.py) — end-to-end, trace integrity, tamper detection.
- [`tests/test_app.py`](tests/test_app.py) — HTTP endpoints.

## Architecture mapping

| Block | Code |
|---|---|
| [02 Knowledge router](blocks/02-knowledge-router.md) | `helix_bio.router.KnowledgeRouter` |
| [03 Ontology grounding](blocks/03-ontology-grounding.md) | `helix_bio.ontology.OntologyGrounder` |
| [04 Tool layer](blocks/04-tool-layer.md) | `helix_bio.tools.*` + `build_default_tools()` |
| [05 Inspectable trace](blocks/05-inspectable-trace.md) | `helix_bio.trace.InspectableTrace` (hash-chained) |
| [06 Faithfulness gate](blocks/06-faithfulness-gate.md) | `helix_bio.faithfulness.FaithfulnessGate` |
| [07 Dual-use safety](blocks/07-dual-use-safety.md) | `helix_bio.dual_use.DualUseSafetyLayer` |
| [08 Per-researcher memory](blocks/08-memory-per-researcher.md) | `helix_bio.memory.ResearcherMemory` |

## Production readiness

- [x] Structural ontology-ID binding on every claim
- [x] Hash-chained trace with tamper detection
- [x] Deterministic tests with mock tools
- [x] Dual-use safety as harness perimeter (not content filter)
- [x] FastAPI + Dockerfile + healthcheck
- [ ] Real MCP integration for UniProt / PDB / AlphaFold (swap mock tools)
- [ ] LLM-driven planner + synthesizer (MVP uses deterministic rules)
- [ ] Neuro-symbolic structural verifier for residue-level claims
- [ ] Multi-tenant deployment with per-researcher key scoping

## License

MIT

## TUI

A polished terminal interface ships out of the box, powered by the shared
[`harness-tui`](../../packages/harness-tui) package.

```bash
make install     # installs harness-tui editable alongside this project
make tui         # opens the TUI against the running FastAPI backend
make tui-mock    # demo: scripted events, no backend needed
```

Features:

- **Brand theme** with project ASCII logo + spinner pack.
- **Hero sidebar widget**: Faithfulness ledger + dual-use safety banner.
- 16 built-in slash commands: `/help`, `/plan`, `/why`, `/cost`, `/recipe`,
  `/test`, `/find`, `/voice`, `/theme`, `/resume`, `/clear`, `/auto`,
  `/default`, `/quit`, `/cost tool`, `/cost agent`.
- Differentiators built in:
  - Stacked context-budget bar (system / files / conversation / output).
  - Latency sparkline with TTFT + inter-token measurements.
  - Per-tool / per-subagent token + cost rollup table.
  - Typed `Plan` editor (reorder + edit before execution).
  - Per-hunk diff approval (`y/n/a/d/q`).
  - Permission gates with blast-radius preview (dry-run output).
  - Auto-test / auto-lint loop (`/test on`).
  - Recipes (Goose-style YAML) under `recipes/`.
  - Transcript search (`Ctrl+F`).
  - Dual-cursor composer (input + agent quick-replies).
  - Voice mode (`F9` push-to-talk; `pip install 'harness-tui[voice]'`).
  - Web mode (`--serve` via `textual-serve`).
  - SSH mode (`--ssh` via `asyncssh`).
- **Visual snapshot tests** in CI — every PR diffs the SVG-rendered TUI.

See [`research/tui-state-of-the-art.md`](../../research/tui-state-of-the-art.md)
and [`research/tui-framework-and-rollout.md`](../../research/tui-framework-and-rollout.md)
for the design.
