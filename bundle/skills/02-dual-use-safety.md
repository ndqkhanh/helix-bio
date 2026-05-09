---
name: dual-use-safety
description: Block synthesis instructions for Select Agents; require dual-use review.
---
# Dual-Use Safety

Every output that names a target with weaponization potential
(Select Agents, dual-use pathways, certain virus families)
passes through the dual-use review skill. The review:

1. Classifies the output by risk tier (informational / mechanistic /
   procedural / synthesis-route).
2. Blocks at the rubric level for synthesis-route outputs naming
   Select Agents (`LBL-HELIX-NO-SYNTHESIS-INSTRUCTIONS`).
3. Routes mechanistic / procedural outputs to a HITL approver if
   the Lyra runtime has one wired.
4. Records every review decision in a hash-chained audit log.

**Bright line `LBL-HELIX-LOCAL`:** the review runs in *this
bundle's* MCP server. Lyra core never sees the un-gated output.
