# Helix-Bio Block 02 — Knowledge Router

## Responsibility

Decide which data sources each portion of the query should hit. Turns the `Brief` into a DAG of tool calls across native sources (UniProt / PDB / AlphaFold / BLAST / ChEMBL / Ensembl / PubMed / HPO / GO / MeSH). Based on ReWOO's planned-parallel-retrieval pattern ([docs/17](../../../docs/17-rewoo.md)).

## Routing rules (fnmatch + entity type)

| Query signal | Route |
|---|---|
| Entity is UniProt accession | UniProt lookup + AlphaFold (if structure requested) + PDB (experimental) |
| Entity is PDB ID or "structure" keyword | PDB direct + AlphaFold as fallback |
| "Binding", "interface", "complex" | PDB interface query + PubMed scan |
| Entity is ChEMBL compound | ChEMBL + PubMed + BLAST if target sequence is available |
| "Phenotype", "disease" | HPO + OMIM + literature |
| Sequence provided | BLAST first, then top hits → UniProt |
| Broad review question | PubMed systematic search with MeSH filters |

## DAG emission

```yaml
tasks:
  - id: E1
    source: uniprot
    op: lookup
    args: { accession: "Q9BYF1" }
  - id: E2
    source: uniprot
    op: lookup
    args: { accession: "P0DTC2" }
  - id: E3
    source: pdb
    op: search
    args: { query: "ACE2 spike RBD" }
    depends_on: [E1, E2]
  - id: E4
    source: pubmed
    op: search
    args: { query: "ACE2 spike interface residues", date_range: "2020-2023" }
    depends_on: []
  - id: E5
    source: pdb
    op: interface
    args: { pdb_id: "{E3[0].pdb_id}", chain_a: "A", chain_b: "E" }
    depends_on: [E3]
```

Independent nodes fan out in parallel; dependent nodes wait on prerequisites. Budget enforced before dispatch per [block 09 Cost Router](09-cost-router.md).

## Fallback behavior

- PDB search empty → AlphaFold DB.
- PubMed hits < N → relax MeSH; then try bioRxiv.
- UniProt lookup fails → try alternate taxonomic variant, flag ambiguity.
- Everything fails → return "no authoritative source found" with reasons.

## Source trust tiers

| Source | Trust |
|---|---|
| UniProt, PDB, ChEMBL, Ensembl, AlphaFold DB (EBI), HPO, MeSH, GO | authoritative |
| PubMed (peer-reviewed) | credible |
| bioRxiv / medRxiv | preprint (flagged in output) |
| Web (Wikipedia etc.) | disallowed by default |

Trust tier affects display (preprint → "preprint" badge) and the faithfulness gate's strictness.

## Failure modes

- **Over-routing** (every query hits every source) → cost blow-up. Mitigated by budget and by hard caps per query.
- **Stale cache** (lookups from minutes ago differ now) → bound TTL per source; short for fast-moving databases (ChEMBL), long for stable ones (PDB historical).
- **API drift** — MCP schema pinning + health checks.

## Metrics

- `router.dispatches_per_brief`, `router.source_mix`, `router.parallel_fanout_max`, `router.fallback_count`, `router.cost_usd`.
