# Helix-Bio Block 06 — Faithfulness Gate

## Responsibility

Before the `Report Assembler` emits a finished report, verify that **every claim** resolves to one or more pieces of cited `Evidence` whose content actually supports the claim. Claims that fail either get rewritten into hedges or dropped; whole sections with insufficient evidence are flagged.

Extends [docs/25 Agentic RAG](../../../docs/25-agentic-rag.md) and [docs/18 CoVe](../../../docs/18-chain-of-verification-self-refine.md) with domain-specific structural checks.

## Two-pass verification

### Pass 1 — Structural check (fast, deterministic)

Per claim:

- **Non-empty `evidence_ids`.** Any claim without evidence is auto-rejected.
- **Every evidence resolves.** UniProt accession is valid; PDB ID exists; PMID is known.
- **Entity consistency.** Claim says "ACE2 interface residue K353"; cited PDB record must contain chain A residue K353. Cited UniProt record must be Q9BYF1.
- **Numeric consistency.** Any number in the claim (residue position, affinity, resolution, publication year) appears in or is derivable from the evidence.

Fail any structural check → reject with a specific reason (not a generic "unsupported").

### Pass 2 — Semantic check (LLM, different family)

For claims that pass structural, a different-family LLM evaluator receives:

```
Claim: "ACE2 K353 forms a hydrogen bond with Spike Q498."
Evidence (from PDB 6M17 interface query): 
  - {residue_a: K353, residue_b: Q498, distance: 3.1Å, type: "HB"}
  - {residue_a: D355, residue_b: T500, distance: 3.0Å, type: "HB"}
Question: Does the evidence support the claim?
Return JSON: {supported: true|false, confidence: 0..1, note: "…"}.
Use only the evidence given.
```

Low confidence or unsupported → rewrite or drop.

## Rewrite strategy

- **Strengthen** when a near-miss can be fixed by adding more retrieved evidence (planner re-spawns a tool call).
- **Weaken** when the original claim was overstated ("ACE2 K353 is essential for binding" → "ACE2 K353 is reported as an interface residue").
- **Drop** when no evidence supports any version of the claim.

## Section-level flags

If > 30% of a section's claims fail, the section gets an "insufficient evidence" banner and the Report Assembler marks the report as degraded.

## Number-sensitivity

Numbers that don't match evidence are a **hard reject** at structural stage — no LLM vote needed. This directly addresses the "fabricated distance / fabricated affinity" failure mode in generalist bio chatbots.

## Dual-verifier discipline

Same-family verification rejects fewer errors (known bias). Helix-Bio uses a different-family verifier where available; falls back to same-family with a warning span per [Orion-Code trade-off 5](../../orion-code/architecture-tradeoff.md).

## Output

```yaml
FaithfulnessReport:
  total_claims: 64
  pass1_rejected: 2
  pass2_rejected: 3
  faithfulness_ratio: 0.922
  rejected:
    - claim_id: …
      stage: "pass1"
      reason: "cited PDB ID not found in evidence"
```

## Failure modes

- **Verifier leniency** → mitigated by structural checks first.
- **Rewrite loop** → max rounds per claim = 2, then drop + flag.
- **Stalemate** on a section → surface to user; don't ship a degraded claim silently.
- **Cost creep** → batch verifications where possible; cache per-session evidence embeddings.

## Metrics

- `faithfulness.ratio` (dist.), `faithfulness.pass1_reject_rate`, `faithfulness.pass2_reject_rate`, `faithfulness.section_degraded_count`, `faithfulness.rewrite_rounds` (dist.), `faithfulness.cost_usd` (dist.).
