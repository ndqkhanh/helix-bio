---
name: faithfulness-gate
description: Every claim binds to an ontology entry; no binding = fail.
---
# Faithfulness Gate

For every claim in the output:

1. Identify the named entity (protein, gene, drug, pathway, disease).
2. Look up the entity in the relevant ontology
   (UniProt for proteins, ChEMBL for drugs, MeSH for diseases,
   PDB for structures).
3. Bind the claim to the ontology entry with the entry's permanent
   identifier.

A claim with no ontology binding fails the gate
(`LBL-HELIX-FAITHFUL`). The gate is **non-bypassable** — it is the
substrate, not a feature flag.
