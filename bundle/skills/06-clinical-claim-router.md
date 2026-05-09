---
name: clinical-claim-router
description: Route clinical claims through the authoritative-source check.
---
# Clinical Claim Router

Every clinical claim (efficacy, safety, dosing, indication) routes
through:

1. Authoritative-source check — must cite peer-reviewed primary
   literature (PubMed) or an authoritative DB entry (FDA label,
   ClinicalTrials.gov).
2. Tier-down for blog / tweet / undocumented sources — those mark
   the claim as `tier: speculative` and demand a primary citation
   before promotion.
3. Confidence floor — clinical claims start at confidence ≤ 0.6
   regardless of strength of language; promotion requires a
   primary citation.

`LBL-HELIX-AUTH-SOURCE`: clinical claims without primary citations
fail.
