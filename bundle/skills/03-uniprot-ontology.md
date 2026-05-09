---
name: uniprot-ontology
description: Bind protein claims to UniProt accession entries.
---
# UniProt Ontology

For every protein named in an output:

- Look up by name + species → UniProt accession.
- Resolve ambiguous names via gene-name → cross-reference.
- Bind the claim to the accession (e.g. `P12345`).
- Include the accession inline in the output.

The lookup is cached per-session; cache TTL 24 h.

**Bright line:** ambiguous lookups (≥2 plausible accessions) emit
a `helix.ambiguous` event and require disambiguation before the
claim ships.
