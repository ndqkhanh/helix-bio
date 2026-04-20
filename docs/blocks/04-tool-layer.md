# Helix-Bio Block 04 — Tool Layer

## Responsibility

Expose every external data source as a **typed MCP tool** with a versioned schema, rate limits, auth, health check, and retry policy. Downstream blocks never reach past this layer.

## Core tool set

| Tool | Backend | Key methods |
|---|---|---|
| `uniprot` | UniProt REST | `lookup(accession)`, `search(query, fields, max)` |
| `pdb` | RCSB PDB REST | `search(query)`, `get(pdb_id)`, `interface(pdb_id, chain_a, chain_b)` |
| `alphafold` | AlphaFold DB | `get(uniprot_accession) → {cif_url, pLDDT, PAE_url}` |
| `blast` | NCBI BLAST+ or EBI BLAST | `submit(sequence, database)`, `fetch(job_id)` |
| `chembl` | ChEMBL REST | `compound(chembl_id)`, `target_compounds(target_accession)` |
| `ensembl` | Ensembl REST | `gene(ensembl_id)`, `transcripts(ensembl_id)` |
| `pubmed` | NCBI E-utilities | `search(query, date_range, pubtypes, mesh)`, `fetch(pmid) → {abstract, full_text_url, mesh_terms}` |
| `hpo` | HPO API | `search(phenotype_term) → codes[]` |
| `go` | Gene Ontology | `term(go_id)`, `terms_for_gene(accession)` |
| `mesh` | NLM MeSH | `term(descriptor_ui)` |

All tools registered via the MCP protocol ([docs/07](../../../docs/07-model-context-protocol.md)); harness pins versions at connect time.

## Contract principles

1. **Structured returns.** No "blob of text" outputs. Every method returns typed fields.
2. **Provenance baked in.** Every record has an identifier we can cite: accession, PDB ID, DOI, PMID.
3. **Rate limits respected.** Per-tool token bucket; rejects surface as retry-able errors.
4. **Health check endpoint** per server; orchestrator monitors.
5. **Versioned.** Tool version pinned at session start; drift warnings flagged.

## Example tool call

```yaml
tool: pdb
method: interface
args:
  pdb_id: "6M17"
  chain_a: "A"   # ACE2
  chain_b: "E"   # Spike RBD
→
contacts:
  - { residue_a: "K353", residue_b: "Q498", distance: 3.1 }
  - { residue_a: "D355", residue_b: "T500", distance: 3.0 }
  ...
source: "RCSB PDB, structure 6M17 (Yan et al., 2020)"
retrieved_at: 2026-04-20T12:34:56Z
```

## Parallelism

Independent tool calls fan out concurrently. The MCP client enforces per-server concurrency caps.

## Failure handling

- **Rate limit** → backoff + retry; flag if persistent.
- **Schema drift** → structured error; router falls back if possible.
- **Network error** → retry with jitter; circuit-break after N.
- **Unknown accession / PDB ID** → structured error, not a hallucination.

## Adding a new tool

Standard MCP adapter pattern:
1. Implement the server in any language per the MCP spec.
2. Add to the tenant's tool registry with a version + health-check URL.
3. Register its schema; the harness validates inputs against it.
4. Add a red-team test case to the eval suite.

## Metrics

Per tool: `calls_count`, `latency_ms_p50/p95/p99`, `error_rate`, `fallback_used`, `version_drift_events`.
