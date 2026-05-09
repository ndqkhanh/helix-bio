# Helix-Bio — System Design

Operational specification.

## Topology

```
Browser / CLI / notebook kernel
       │
       ▼
┌────────────┐
│  Gateway   │ authn / tenant resolution / rate / audit
└─────┬──────┘
      │
      ▼
┌────────────────┐       ┌────────────────┐
│  Orchestrator  │◀────▶│  Cost Router   │
└──────┬─────────┘       └────────────────┘
       │
       ▼
 ┌─────┴─────┬──────────┬──────────┬───────────┐
 ▼           ▼          ▼          ▼           ▼
Intake    Ontology  Faithfulness  Dual-Use   Report
                    Gate          Safety     Assembler
       │
       ▼
 ┌──────── MCP Tool Bus ────────┐
 │                              │
 ▼   ▼    ▼   ▼   ▼   ▼   ▼   ▼
UniProt PDB AlphaFold BLAST ChEMBL Ensembl PubMed HPO
```

## Data model

```python
class Brief:
    question: str
    audience: Literal["clinician", "bench", "computational", "translational"]
    confidentiality: Literal["open", "tenant", "embargoed"]
    time_budget_s: int = 600
    cost_budget_usd: float = 3.0

class EntityRef:
    ontology: Literal["uniprot", "pdb", "chebi", "go", "hpo", "mesh", "ensembl"]
    identifier: str        # e.g. "UniProt:Q9BYF1"
    display_name: str

class Evidence:
    id: UUID
    tool: str              # MCP tool name
    args_hash: str
    content: str
    source_doi: Optional[str]
    retrieved_at: datetime

class Claim:
    id: UUID
    text: str
    entities: list[EntityRef]
    evidence_ids: list[UUID]     # mandatory; non-empty
    verified: bool
    verification_note: str

class Report:
    brief: Brief
    sections: list[Section]
    references: list[Citation]
    faithfulness_ratio: float
    dual_use_flag: bool
    cost_usd: float
    trace_id: UUID
```

## Public HTTP API

```
POST /v1/reports
  body: Brief JSON
  202 Accepted + Location: /v1/reports/{id}

GET  /v1/reports/{id}
  returns status, progress, partial JSON

GET  /v1/reports/{id}/markdown
GET  /v1/reports/{id}/json
GET  /v1/reports/{id}/trace

POST /v1/reports/{id}/drill/{claim_id}
  returns the exact tool calls that produced a claim

POST /v1/memory            (consent-gated)
DELETE /v1/memory/{id}
```

Authentication: per-tenant API keys + optional OIDC for enterprise SSO. Audit log per request.

## MCP tool contracts (versioned)

```
uniprot:
  lookup(accession) → {name, gene, organism, sequence, features}
  search(query, fields, max_results)
pdb:
  search(query, entity_id)
  get(pdb_id) → {method, resolution, chains, residues, seqres}
  interface(pdb_id, chain_a, chain_b) → residue-residue contacts
alphafold:
  get(uniprot_accession) → {model_cif, pLDDT, PAE}
blast:
  submit(sequence, database) → job_id
  fetch(job_id) → hits[]
chembl:
  compound(chembl_id)
  target_compounds(target_accession)
ensembl:
  gene(ensembl_id)
  transcripts(ensembl_id)
pubmed:
  search(query, date_range, publication_types)
  fetch(pmid) → {abstract, full_text_url, mesh_terms}
hpo:
  search(phenotype_term) → codes
go:
  term(go_id)
```

Every call is traced; every response includes a DOI / accession where possible.

## Deployment

- Containerized; per-tenant deployment.
- MCP servers run either colocated or as managed services (shared UniProt/PDB mirror across tenants is acceptable; PubMed may be per-tenant if full-text license differs).
- Per-tenant isolation: data and memory never cross.
- Optional air-gapped: run against a local bio-data mirror.

## SLOs

| Metric | Target |
|---|---|
| Time to first finding | p50 < 45s |
| Full report completion | p50 < 6 min, p95 < 12 min |
| Cost per report | p50 ≤ $2, p95 ≤ $3 |
| Faithfulness ratio | ≥ 97% |
| Drill-through latency (claim → trace) | p95 < 500ms |
| Dual-use FPR | ≤ 1% (weekly red-team) |
| Tool-server availability | ≥ 99.5% per source |

## Failure handling

| Failure | Response |
|---|---|
| Tool source down | Router tries alternate (PDB → AlphaFold fallback for structure); report flags coverage gap |
| Faithfulness reject (repeated) | Claim rewritten as hedge; if whole section unsupported, section is flagged "insufficient evidence" |
| Dual-use flag | Pause, notify org-admin HITL; escalate per policy |
| PubMed paywall | Use abstract + MeSH; mark full-text unavailable |
| Hallucinated accession | Ontology resolver rejects; planner re-plans with a search instead of direct lookup |

## Security & compliance

- Per-tenant KMS-managed keys for data at rest.
- Audit log for every query + every tool call, hash-chained per [Aegis-Ops audit pattern](../aegis-ops/blocks/07-audit-observability.md).
- HIPAA option: BAA + deidentification gate on any clinician-facing patient data.
- PHI never enters prompts without consent flags.
- Dual-use policy file under CI — change review required.

## Scaling

- Horizontal orchestrator.
- Per-tenant memory shards.
- MCP tool bus can fan out in parallel for independent lookups (e.g., simultaneous UniProt + PDB + PubMed on a novel query).
- Cost-ceiling enforced before fan-out to avoid budget blow-through.

## Roadmap (post-v1)

- Wet-lab data ingest (instrument CSVs, images).
- Active-learning loop: researcher feedback sharpens per-tenant routing.
- Domain packs: oncology, infectious disease, immunology, neurology.
- Full-text multilingual.
- Robotics / ELN bridges.

## Anti-scope

- No coding → Orion-Code.
- No prod ops → Aegis-Ops.
- No voice → Harmony-Voice.
- No generic research → Atlas-Research.
