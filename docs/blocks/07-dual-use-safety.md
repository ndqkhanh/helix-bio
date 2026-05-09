# Helix-Bio Block 07 — Dual-Use Safety

## Responsibility

Detect queries or outputs that touch regulated or dual-use pathways — select agents, schedule-I synthesis, gain-of-function-adjacent work, bioweapon precursor chemistry — and route them through a hard-deny list + HITL + audit log. Aligned in posture with [docs/22 Guardrails](../../../docs/22-guardrails-prompt-injection.md) and [docs/23 HITL](../../../docs/23-human-in-the-loop.md).

## Why a dedicated block

Bio is one of very few domains where the cost of a well-intentioned helpful answer can be catastrophic (synthesis of a regulated pathogen). Generic LLM refusals are inconsistent and bypassable via prompt injection. A dedicated, auditable, policy-file-backed layer is required.

## Policy sources (code-reviewed)

- **US HHS Select Agents & Toxins** list (federal)
- **Australia Group** controlled items
- **DEA Schedule I / II** chemicals
- **WHO List of Priority Pathogens**
- **Tenant-specific** add-ons (e.g., a pharma may block a specific compound family)

Policy lives as code in a git repo; changes go through CI + review + signed commits.

## Detection

Two-tier:

1. **Deterministic list matching.** Entity-ID lookup against the regulated lists (UniProt accessions of select agent toxins, ChEMBL compounds on controlled lists, specific species taxonomy IDs).
2. **ML classifier (fine-tuned).** For queries that discuss synthesis pathways, uplift, enhancement, or transmission enhancement — a small classifier trained on a red-team corpus.

Both signals combine. Hit → **pause + HITL + audit**.

## HITL flow

- Query halted.
- Notification to org's designated biosafety officer (per tenant config).
- Notification includes: brief, matched policy, classifier confidence, researcher identity.
- Reviewer either approves (with rationale, logged), denies (terminal), or asks for scope narrowing.

## Hard-deny paths

Certain queries have no legitimate answer the tenant has pre-authorized; e.g., "synthesize VX", "enhance airborne transmissibility of