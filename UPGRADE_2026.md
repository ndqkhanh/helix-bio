# Helix-Bio — May-2026 Upgrade Stub

> Companion to [`../CROSS_PROJECT_UPGRADE_PLAN_2026.md`](../CROSS_PROJECT_UPGRADE_PLAN_2026.md).
> Per the cross-project matrix, Helix-Bio is **W3** — biomedical
> domain; ontology-grounding and dual-use safety are first-class.

## Headline gap (vs 2026 SOTA)

- **No `bundle/`** — faithfulness gate + dual-use safety + ontology
  bindings not packaged.
- **Dual-use safety must stay project-local** — under Lyra v3.11
  `LBL-BUNDLE-DUAL-USE`, helix-bio bundles require explicit
  authorization at install. The bundle's MCP server enforces the
  authorization step; Lyra core does not see clinical claims.
- **Verifier-coverage gap** — biomed has high pass-rate but few
  verifiers; the L311-6 coverage index would surface this honestly
  and feed back into routing.

## Smallest upgrade

```text
helix-bio/bundle/
├── bundle.yaml                # dual_use: true
├── persona.md
├── skills/
│   ├── 01-faithfulness-gate.md
│   ├── 02-dual-use-safety.md
│   ├── 03-uniprot-ontology.md
│   ├── 04-mesh-ontology.md
│   ├── 05-chembl-ontology.md
│   └── 06-clinical-claim-router.md
├── tools/
│   └── mcp_server.py          # ontology lookup + authoritative-source check
├── memory/
│   └── seed.md                # default ontology bindings + safety rules
├── evals/
│   ├── golden.jsonl           # BixBench / LABBench2 / CloningQA probes
│   └── rubric.md
└── verifier/
    └── checker.py             # citation + ontology-binding verifier
```

## Bright lines

- `LBL-HELIX-DUAL` — the `dual_use: true` manifest flag is enforced
  at install via Lyra's L311-5 authorization step. Without explicit
  authorization, install fails closed.
- `LBL-HELIX-AUTH` — clinical claims must cite UniProt / PDB /
  AlphaFold / authoritative literature; the verifier rejects anything
  else.
- `LBL-HELIX-LOCAL` — dual-use safety logic runs in helix-bio's MCP
  server, not in Lyra core. Lyra never sees the un-gated claims.

## Test plan

- 8+ tests covering bundle validation (incl. dual-use flag), ontology
  binding stub, faithfulness gate, and authorization-failure path.

## Sequencing

W3 — depends on Lyra v3.11 L311-4 + L311-5 (`LBL-BUNDLE-DUAL-USE`).

## Related Lyra phases

- L311-5 AgentInstaller — `LBL-BUNDLE-DUAL-USE` enforcement.
- L311-6 Verifier coverage — biomed-domain coverage score.
