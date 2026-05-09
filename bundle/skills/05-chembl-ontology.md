---
name: chembl-ontology
description: Bind drug / compound claims to ChEMBL entries.
---
# ChEMBL Ontology

For every drug or compound named in an output:

- Look up by name → ChEMBL ID (e.g. `CHEMBL25`).
- Resolve via InChIKey when name is ambiguous.
- Bind the claim to the ChEMBL ID, plus mechanism-of-action and
  target list when relevant.

Mechanism claims that don't match ChEMBL's recorded MoA emit a
`helix.moa_mismatch` event; resolution is human-in-the-loop.
