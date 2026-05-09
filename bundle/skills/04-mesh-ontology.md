---
name: mesh-ontology
description: Bind disease / clinical claims to MeSH descriptors.
---
# MeSH Ontology

For every disease, condition, or clinical concept:

- Look up the canonical MeSH descriptor.
- Resolve ambiguous terms via tree-number → preferred descriptor.
- Bind the claim to the MeSH descriptor (e.g. `D000086382`).

Clinical claims cited by a generalist source (blog, tweet,
undocumented training data) without a corresponding MeSH binding
fail the faithfulness gate (`LBL-HELIX-FAITHFUL`).
