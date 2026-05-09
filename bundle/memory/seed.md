# Helix-Bio seed memory

## Default ontologies

- `UniProt` — protein database; canonical accession format `[OPQ][0-9][A-Z0-9]{3}[0-9]`.
- `MeSH` — Medical Subject Headings; descriptor format `D[0-9]{6}`.
- `ChEMBL` — bioactive molecule database; ID format `CHEMBL\d+`.
- `PDB` — Protein Data Bank; ID format `[0-9][A-Z0-9]{3}`.
- `AlphaFold` — predicted structures; ID derived from UniProt accession.

## Default tier mapping

| Tier | Usage |
|---|---|
| `informational` | descriptive — function, structure, family |
| `mechanistic` | mechanism — pathway, MoA, kinetics |
| `procedural` | how-to — protocol, assay, dosing |
| `synthesis-route` | end-to-end production / weaponization |

## Default Select Agent list

The bundle ships with the federal Select Agent list as a deny-list
input to the dual-use review skill. The list is updated on
`helix.bright_lines.refresh` and persisted to
`~/.helix-bio/select_agents.json`.

`LBL-HELIX-NO-SYNTHESIS-INSTRUCTIONS`: outputs naming a Select Agent
in `synthesis-route` tier are blocked, not warned.
