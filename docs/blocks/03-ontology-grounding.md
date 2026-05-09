# Helix-Bio Block 03 — Ontology Grounding

## Responsibility

Every biological entity in the system's working state is identified by a stable ontology ID: UniProt / PDB / ChEBI / ChEMBL / Ensembl / HPO / GO / MeSH. Prose synonyms exist but always map back to an ID.

## Why this is not optional

Biology has a synonym crisis. "ACE2" / "ACEH" / "angiotensin-converting enzyme 2" / "ACE-2" / "UniProt:Q9BYF1" are all the same thing; "TP53" / "p53" / "trp53" (mouse) look nearly identical and are not. Free-text biology conflates and mis-attributes, then the faithfulness gate has no way to check "is this claim about the protein they meant?".

## Resolver design

Three-stage resolver:

1. **Exact match.** Input is already a stable ID (`UniProt:Q9BYF1`, `PDB:6M17`, `ChEBI:15365`). Pass through.
2. **Canonical-name lookup.** HGNC for human gene symbols; OMIM for diseases; MeSH for concepts; taxonomic ID for organisms.
3. **Fuzzy + context.** Levenshtein + context-aware. Ambiguous results trigger a clarifying question rather than silent selection.

## Resolution record

Every resolved entity carries a record:

```yaml
id: "UniProt:Q9BYF1"
display_name: "ACE2"
full_name: "Angiotensin-converting enzyme 2"
organism: "Homo sapiens (9606)"
synonyms: ["ACEH", "ACE-2"]
resolution_method: "exact" | "canonical" | "fuzzy"
confidence: 0.0 .. 1.0
```

Confidence propagates into claim-level trust; low-confidence entities trigger clarifying questions at intake.

## Cross-ontology links

When a user asks about "a protein and its associated disease", we link UniProt ↔ OMIM ↔ HPO automatically via curated crosswalks. The trace records every hop.

## Claim-level grounding

Every `Claim` must carry `entities: list[EntityRef]`. The faithfulness gate ([block 06](06-faithfulness-gate.md)) cross-checks that the claim's evidence is about the same entity — preventing the "paper mentions ACE2, claim is about TP53" failure mode.

## Failure modes

- **Ambiguous input.** Resolver asks rather than guesses.
- **Stale taxonomy / ID renaming** (UniProt does occasionally merge or retire accessions). Cached crosswalks refreshed weekly; retired IDs redirect with a warning.
- **Cross-species confusion** ("p53" in mouse vs human). Resolver includes organism; answer keeps it in prose.

## Metrics

- `ontology.resolve_count`, `ontology.resolution_method_mix`, `ontology.ambiguous_clarifications`, `ontology.low_confidence_drop_count`.
