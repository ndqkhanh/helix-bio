---
name: 'ontology-bound-claim'
description: 'Emit no biomedical claim without an ontology grounding, a tier-resolved source, a PHI scan, and a dual-use scan.'
version: '0.1.0'
triggers: ['claim', 'biomedical', 'clinical']
tags: ['ontology', 'trust-tier', 'dual-use']
---

# Goal
Surface a biomedical claim only when its entities are grounded in the
ontology, its source resolves to a trust tier, and the dual-use +
PHI gates pass at extraction time.

# Constraints & Style
- Every entity in the claim must resolve to a UMLS / MeSH / GO concept
  ID; unresolved entities block the claim.
- Source resolution: PubMed-indexed → `T1-PEER-REVIEWED`, bioRxiv /
  medRxiv → `T2-PREPRINT`, web / discussion → `T3-DISCUSSION`.
- Clinical claims require `T1-PEER-REVIEWED` AND an ethics-review tag.
- Bright-lines: `BL-HELIX-SKILL-PHI` (regex + entropy reject identifiers,
  DOBs, MRN-shaped tokens), `BL-HELIX-SKILL-CLINICAL-CLAIM` (Tier-1 +
  ethics tag), `BL-HELIX-SKILL-DUAL-USE` (DualUseSafetyLayer runs at
  extraction time, not just at use time).

# Workflow
1. Tokenise the claim; ground each entity via the OntologyGrounder.
2. Resolve the cited source; assign trust tier from the table above.
3. Run the PHI gate over the claim body.
4. Run the dual-use gate; on trip, drop the candidate and log to
   `dual-use-rejections.jsonl`.
5. If clinical, require Tier-1 + ethics tag; otherwise reject.
6. Emit the candidate skill with `trust_tier` populated; the upstream
   `harness_skills.hooks.trust_gate` runs before FaithfulnessGate.
