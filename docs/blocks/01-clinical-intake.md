# Helix-Bio Block 01 — Clinical / Research Intake

## Responsibility

Convert an open-ended biomedical question into a scoped `Brief` before any retrieval cost is paid. Identify audience, confidentiality, time/cost budget, required depth, and specific entities to resolve.

## Why it matters

Bio queries have a huge variance in scope. *"What does ACE2 do?"* is a 30-second answer; *"Map all reported ACE2 interactors in SARS-CoV-2 literature, prioritized by structural evidence"* is a multi-minute, multi-tool traversal. Without an intake step, the system over- or under-spends compute, and the faithfulness gate has no target to measure against.

## Workflow

1. **Classify audience.** Clinician / bench scientist / computational / translational. Style adjusts accordingly.
2. **Detect confidentiality.** Does the question reference confidential compound series, patient cohorts, embargoed preprints? If yes, memory write is disabled by default.
3. **Entity extraction + early resolution.** Named entities (proteins, compounds, phenotypes, genes) are extracted and resolved to stable IDs via [block 03 Ontology Grounding](03-ontology-grounding.md). Ambiguities trigger a clarification question ("did you mean UniProt:Q9BYF1 or UniProt:P00799?").
4. **Scope check.** Does this require wet-lab data Helix doesn't have access to? Is this a regulated-pathway query flagged by [block 07](07-dual-use-safety.md)?
5. **Budget.** Propose a time and cost budget; let the user override.

## Clarifying-question budget

Hard cap: 3 questions. Most queries need ≤1. Research shows more than that annoys users and still rarely improves scope.

## Brief shape

```yaml
question: "Which PDB structures of human ACE2 show binding to SARS-CoV-2 spike RBD..."
audience: computational
confidentiality: open
resolved_entities:
  - UniProt:Q9BYF1 (ACE2, Homo sapiens)
  - UniProt:P0DTC2 (Spike glycoprotein, SARS-CoV-2)
priorities:
  - structural_evidence
  - interface_residues
time_budget_s: 300
cost_budget_usd: 2.0
dual_use_preflight: pass
```

## Failure modes

- **Vague scope** — fall through to a bounded "survey" default rather than refuse.
- **Unresolvable entity** — prompt for an alternate name or ID.
- **Dual-use preflight flag** — pause, hand off to [block 07](07-dual-use-safety.md).
- **User fatigue** — 3-question cap; prefer defaults over interrogation.

## Metrics

- `intake.latency_ms`, `intake.clarifications_count` (dist.), `intake.entity_resolve_rate`, `intake.dual_use_pretriggers`.
