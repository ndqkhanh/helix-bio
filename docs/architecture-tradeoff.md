# Helix-Bio — Architecture Trade-offs

## Trade-off 1: Native tool servers vs PubMed-chunk RAG

**Chosen:** Native MCP servers for UniProt, PDB, ChEMBL, AlphaFold, BLAST, Ensembl. PubMed chunks are a *fallback* source, not the primary surface.

**Alternative:** Universal PubMed RAG as a single surface, rely on the LLM to compose.

**Why:** RAG over abstract chunks loses structured metadata (accession IDs, DOIs, publication year, author). Citation drift and hallucinated DOIs are the dominant failure mode of generalist bio-research agents. Typed API calls preserve the structure the downstream faithfulness gate depends on.

**Cost:** Maintain MCP adapters per source; handle rate limits and API drift. Mitigated by pinned versions and health monitoring per [docs/24](../../docs/24-observability-tracing.md).

## Trade-off 2: Faithfulness gate as blocker vs faithfulness as soft score

**Chosen:** Blocker. No report emits until every claim resolves.

**Alternative:** Soft score; ship the report with a confidence badge.

**Why:** Bio consumers (clinicians, PIs, bench scientists) act on statements as fact. Soft scores are discounted by readers who skim. Hard blocking plus rewriting unsupported claims into hedges ("limited evidence supports…") raises the floor.

**Cost:** ~20–30% latency and cost overhead per [docs/18 CoVe](../../docs/18-chain-of-verification-self-refine.md). Mitigated by batching verification across claims and by caching tool results.

## Trade-off 3: Dual-use safety in the harness vs in the model

**Chosen:** Harness-level classifier + HITL for regulated pathways. Policy defined as code, not prompt.

**Alternative:** Train the model to refuse regulated topics.

**Why:** Model-level refusal is inconsistent and prompt-injectable. A deterministic, auditable classifier over a published list of regulated pathways is a defense in depth. It also satisfies compliance teams who need to point at a policy file, not at "the model said no."

**Cost:** Classifier maintenance; some legitimate research is slowed by HITL. Published lists (Australia Group, schedule-I agents, HHS select agents) change slowly and are an auditable reference.

## Trade-off 4: Ontology grounding vs free-text biology

**Chosen:** Every entity resolves to a stable ID (UniProt, ChEBI, GO, HPO, Ensembl, MeSH). Prose synonyms allowed only when linked.

**Alternative:** Free-text biology with occasional citations.

**Why:** Bio has a synonym crisis ("ACE2" vs "angiotensin-converting enzyme 2" vs "ACEH"). Free-text conflates and mis-attributes. Stable IDs make the faithfulness gate tractable and the downstream trace auditable.

**Cost:** Intake and resolution latency; sometimes users get told "did you mean UniProt:Q9BYF1?" Mitigated by caching the resolution per session.

## Trade-off 5: Generalist model + specialist harness vs specialist model (Rosalind-style)

**Chosen:** Generalist frontier model plus a specialist harness. Swap models as better ones appear.

**Alternative:** Own a trained specialist model (Rosalind's posture).

**Why:** Frontier generalists now meet most domain-vocab needs; most of the quality gap is harness-driven (tool access, faithfulness gate, safety). Keeping the model swappable prevents lock-in and rides the frontier-model curve.

**Cost:** No IP moat on the weights. Real moat is: curated MCP servers, the ontology graph, the dual-use policy, the eval suite.

## Trade-off 6: Per-researcher memory opt-in vs shared team memory by default

**Chosen:** Opt-in per researcher; per-tenant shared memory requires explicit org-admin configuration.

**Alternative:** Shared team memory by default.

**Why:** Research is competitive and often confidential pre-publication. Defaulting to "everyone on the team sees what everyone asks" is the wrong default for academic labs and pharma. Per-researcher + explicit sharing aligns with lab culture.

**Cost:** Some collaboration friction; some duplicate retrievals. The trust posture is worth it.

## Trade-off 7: Inspectable trace vs log-only

**Chosen:** Click-through trace UI. Every finding resolves to the exact tool call + observation within 500ms.

**Alternative:** Logs; researcher grep if they care.

**Why:** Researcher trust accrues via "I can see why the system said that." RadAgent found faithfulness itself is a capability; the UI is how faithfulness becomes a product feature.

**Cost:** UI work. Worth it — the UI is the product surface researchers actually use.

## Trade-off 8: Include experimental data agents vs literature-only

**Chosen:** MVP is literature + databases + computational tools. Lab-data ingest (wet-lab CSVs, mass-spec, images) is v0.2.

**Alternative:** Ship with everything.

**Why:** Lab data is messy and per-instrument; getting literature/DB right first gives us an evaluable baseline.

## Trade-off 9: Cite-DOI vs cite-whole-paper

**Chosen:** Cite DOI + page/section where possible; prefer figures/tables over prose.

**Alternative:** Cite the whole paper, let the reader find the claim.

**Why:** Whole-paper citation is where drift happens — the paper does say X (somewhere) but not the specific claim. Fine-grained provenance forces the system to be honest about where the claim actually lives.

**Cost:** Parsing full-text papers to find the anchor is harder. Mitigated by structured sources (PubMed Central XML) for the high-value literature subset.

## Trade-off 10: Structured outputs vs free-prose reports

**Chosen:** Every report has both a canonical structured JSON representation and a rendered markdown view. Downstream tools (ELNs, REDCap, dashboards) consume the JSON.

**Alternative:** Free-prose only.

**Why:** Researchers paste results into ELNs; automation needs structure. Two surfaces from one source of truth is cheap.

**Cost:** Template maintenance.

## Rejected alternatives

- **LLM-only reasoning over structured biology.** Models reason poorly about PDB coordinates, atomic distances, phylogenetic trees. Route those to symbolic/numerical tools.
- **Open public chatbot.** Dual-use and IP concerns; Helix-Bio is team- or tenant-scoped.
- **Autonomous experimental design executor.** Robotic lab integration is a different product; Helix-Bio advises humans.
- **"Just use Rosalind."** Fine posture, different product — Rosalind is a model; Helix-Bio is a harness swap-in.

## What breaks outside design envelope

- **Novel-modality biology** (single-cell spatial omics pipelines) — tool adapters don't exist yet; Helix-Bio will hedge.
- **Gray-market preprints** — if a researcher demands bioRxiv-only evidence, Helix-Bio flags lower-confidence.
- **Regulated pathways without HITL** — hard deny; no escape hatch in MVP.
- **Non-English literature at scale** — MVP covers English + top-language abstracts; full-text multilingual is v0.2.
