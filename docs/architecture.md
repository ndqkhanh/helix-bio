# Helix-Bio — Architecture

## What Helix-Bio is

Helix-Bio is a domain-specialized biomedical research agent. It operates over the canonical life-sciences data surfaces — UniProt, PDB, AlphaFold DB, BLAST, PubMed, ChEMBL, Ensembl — via a typed tool layer, produces an **inspectable reasoning trace** in the style of [RadAgent](../../docs/28-radagent-agentic-radiology.md), and gates every factual claim behind a **faithfulness check** against retrievable primary sources before emitting a report.

Where [Atlas-Research](../atlas-research/architecture.md) is general-purpose research and [GPT-Rosalind](../../docs/30-gpt-rosalind-domain-specialized.md) is a specialist model with baked-in workflows, Helix-Bio is a **specialist harness** around any sufficiently capable LLM plus curated tool servers. The harness — not the model — is the differentiator.

## Honest baselines

Numbers below are measured by others and cited from the research corpus.

| Baseline | Benchmark / finding | Source |
|---|---|---|
| GPT-Rosalind | 0.751 pass rate on BixBench; outperforms GPT-5.4 on 6 of 11 LABBench2 tasks; strong on CloningQA (end-to-end reagent design) | [docs/30](../../docs/30-gpt-rosalind-domain-specialized.md) |
| RadAgent (chest CT) | +6.0 F1 clinical accuracy, +24.7 points robustness over vision-language baselines, introduced faithfulness as new capability | [docs/28](../../docs/28-radagent-agentic-radiology.md) |
| dnaHNet | Tokenizer-free genomic foundation model; ~3× faster than Transformer baselines; beats StripedHyena2 on zero-shot genomics | [docs/33](../../docs/33-dnahnet-genomic-foundation.md) |
| Generalist LLMs over PubMed RAG | Frequent unsupported claims; citation drift; hallucinated DOIs — well-documented failure mode | across survey papers |

## Design targets (hypotheses)

- **Faithfulness:** ≥ 97% of factual claims in every output resolve to a retrievable UniProt/PDB/PubMed/ChEMBL identifier with matching content. **Assumption:** structural citation binding + two-pass verification catch the hallucinated-DOI failure mode that plagues generalist PubMed RAG.
- **BixBench / LABBench2 parity or better at lower cost:** match GPT-Rosalind's 0.751 BixBench and ≥6-of-11 LABBench2 at ≤ 60% of its compute budget. **Assumption:** specialist tool layer closes most of Rosalind's domain gap; harness discipline does the rest.
- **Dual-use safety:** zero cases of the agent producing bench-ready synthesis routes for regulated dual-use agents at 1% FPR against a LaStraj-style biosecurity red team. **Assumption:** hard-deny policy layer + dual-use classifier + HITL on regulated-pathway queries.
- **Inspectability:** every report ships with a side-by-side trace where every finding resolves in < 500 ms to the exact tool call + observation that produced it.

These are **hypotheses**, not measurements. They anchor the architecture.

## Component diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                           Helix-Bio Pipeline                          │
│                                                                       │
│  Scientist ──▶ [Clinical/Research Intake]                             │
│                         │                                             │
│                         ▼                                             │
│                  [Knowledge Router]                                   │
│          ┌──────────────┼──────────────┬─────────────┐                │
│          ▼              ▼              ▼             ▼                │
│    [UniProt MCP]   [PDB/AlphaFold]  [BLAST]     [PubMed/ChEMBL]       │
│                         │                                             │
│                         ▼                                             │
│                [Ontology Grounding] ← MeSH / GO / ChEBI / HPO         │
│                         │                                             │
│                         ▼                                             │
│          [Inspectable Trace (RadAgent-style)]                         │
│                         │                                             │
│                         ▼                                             │
│             [Faithfulness Gate]  ── unsupported → reject/rewrite      │
│                         │                                             │
│                         ▼                                             │
│              [Dual-Use Safety Classifier]                             │
│                         │                                             │
│                         ▼                                             │
│                  [Report Assembler]                                   │
│                                                                       │
│  ↕  Memory per researcher (opt-in)                                    │
│  ↕  Cost router (strong plan/verify; cheap retrieval/summarize)       │
│  ↕  Observability (OpenTelemetry, Claw-Eval trace shape)              │
└───────────────────────────────────────────────────────────────────────┘
```

## The ten architectural commitments

1. **Ontology-grounded identifiers, not prose.** Every biological entity in a claim is resolved to a stable ID (UniProt, ChEBI, GO term, HPO code). Prose synonyms are allowed only when linked to an ID. See [blocks/03-ontology-grounding.md](blocks/03-ontology-grounding.md).
2. **Tool layer over native databases, not web search.** PubMed RAG chunks are a fallback. The primary surface is typed API calls against authoritative databases. See [blocks/04-tool-layer.md](blocks/04-tool-layer.md).
3. **Inspectable trace by default.** Every decision emits a structured span; the output ships with a UI that lets a reviewer click any finding and jump to its trace. See [blocks/05-inspectable-trace.md](blocks/05-inspectable-trace.md).
4. **Faithfulness gate is non-optional.** No report leaves the system without a claim-level support check against cited evidence. See [blocks/06-faithfulness-gate.md](blocks/06-faithfulness-gate.md).
5. **Dual-use safety is a first-class block, not a wrapper.** Regulated pathways (select agents, schedule-I synthesis, gain-of-function adjacent topics) are gated by a classifier + HITL per [blocks/07-dual-use-safety.md](blocks/07-dual-use-safety.md).
6. **Per-researcher memory is opt-in, per-organization by default isolated.** Ethics and privacy are designed in, not retrofitted. See [blocks/08-memory-per-researcher.md](blocks/08-memory-per-researcher.md).
7. **Knowledge Router, not one-shot RAG.** Queries are classified by domain class and routed to the right tool, then merged. See [blocks/02-knowledge-router.md](blocks/02-knowledge-router.md).
8. **Clinical/research intake is a distinct phase.** The system asks clarifying questions before spending compute. See [blocks/01-clinical-intake.md](blocks/01-clinical-intake.md).
9. **Cost routing across model tiers.** Strong models for planning + faithfulness; cheap models for retrieval summarization. See [blocks/09-cost-router.md](blocks/09-cost-router.md).
10. **Continuous evaluation on published benchmarks + private suites.** BixBench, LABBench2, and per-tenant regression suites run on every harness release. See [blocks/10-eval-benchmarks.md](blocks/10-eval-benchmarks.md).

## Data flow for a typical query

1. *"Which PDB structures of human ACE2 show binding to SARS-CoV-2 spike RBD, and what are the key interface residues?"* → Clinical Intake confirms scope; asks if computational or experimental priority.
2. **Knowledge Router** dispatches: UniProt lookup (ACE2 accession), PDB search, PubMed review for interface studies.
3. Results flow through **Ontology Grounding** so residues are anchored to SEQRES coordinates with position numbers.
4. The **Inspectable Trace** records every tool call, input, output.
5. **Synthesis** produces claim-bound findings.
6. **Faithfulness Gate** verifies each claim against its cited tool result.
7. **Dual-Use Safety Classifier** checks the query + output; for this benign query, passes.
8. Report Assembler emits markdown + JSON trace; researcher can click any finding to see provenance.

## What distinguishes Helix-Bio

- **Database-native, not web-native.** Most generalist bio research agents chunk PubMed abstracts and hope. Helix-Bio treats UniProt/PDB/ChEMBL as typed tools with structured returns.
- **Faithfulness as gate.** Generalist pipelines ship unsupported claims. Helix-Bio refuses to.
- **Dual-use safety lives in the harness.** Regulated-pathway detection is code-enforced, not prompt-enforced.
- **Neuro-symbolic posture.** For structural biology, Helix-Bio can route residue-level claims to a symbolic checker against PDB coordinates rather than "asking the LLM if the interface makes sense" — see [neuro-symbolic](../../docs/37-neuro-symbolic-ai.md).

## Novel contributions (not present in cited systems)

Helix-Bio's value case rests on four inventive combinations drawn from the research corpus, not on any single reimplementation:

1. **Ontology-identifier-bound outputs.** Citations are not metadata; they are a structural *output constraint*. Every emitted entity mention must bind to `UniProt:P01116` / `HGNC:6407` / `MeSH:D021103`-shaped tokens, validated by the faithfulness gate against the trace. This tightens [RadAgent's faithfulness pattern](../../docs/28-radagent-agentic-radiology.md) by fusing it with [Atlas-Research's citation binding](../atlas-research/blocks/06-synthesis-writer.md).
2. **Neuro-symbolic residue-level verifier.** Structural claims ("R273 in p53 DBD makes a hydrogen bond to DNA phosphate") route to a Lean-style symbolic checker against PDB coordinates rather than LLM self-critique. Direct application of the [neuro-symbolic design pattern](../../docs/37-neuro-symbolic-ai.md) to structural biology — novel niche.
3. **ReBalance confidence steering on the retrieval DAG.** Easy identifier lookups run at shallow reasoning depth; hard compositional reasoning (pathway + variant + drug) steers deeper via [ReBalance](../../docs/51-rebalance-efficient-reasoning.md). First application of training-free reasoning-depth control to biomedical RAG.
4. **Dual-use safety as a harness perimeter** (not a content filter). A deterministic deny-list (BSAT pathogens, Schedule-I synthesis routes, gain-of-function enabling queries) + an institutional-review routing lane for ambiguous cases. See [blocks/07-dual-use-safety.md](blocks/07-dual-use-safety.md).

## Non-goals

- Not a drug-design decision engine. Outputs are evidence; humans decide.
- Not a clinical decision support system. Regulatory pathway for CDS is separate.
- Not a replacement for wet-lab validation. "Strong computational prior" at best.
- Not a general chatbot.

## Cross-references

- Trade-offs: [architecture-tradeoff.md](architecture-tradeoff.md)
- Operations: [system-design.md](system-design.md)
- Blocks: [blocks/](blocks/)
- Research base: [docs/28 RadAgent](../../docs/28-radagent-agentic-radiology.md), [docs/30 Rosalind](../../docs/30-gpt-rosalind-domain-specialized.md), [docs/33 dnaHNet](../../docs/33-dnahnet-genomic-foundation.md), [docs/25 Agentic RAG](../../docs/25-agentic-rag.md), [docs/37 Neuro-Symbolic](../../docs/37-neuro-symbolic-ai.md).

## Status

Design specification, April 2026. Not implemented. Target environment: cloud-hosted MCP servers for public DBs + per-tenant workspace; air-gapped deployment possible with a bio-data mirror.
