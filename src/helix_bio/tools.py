"""Typed mock tools for biomedical databases. Swap with real MCP servers in prod.

Each tool follows the harness_core.tools.Tool pattern: pydantic-validated args,
structured returns. Deterministic canned responses keyed on input so tests pass
without network access.
"""
from __future__ import annotations

from typing import Any

from harness_core.tools import Tool, ToolError, ToolRegistry
from pydantic import BaseModel, Field

from .models import OntologyID, SourceRef

# ---- seed data ---------------------------------------------------------------

_UNIPROT_SEED: dict[str, dict[str, Any]] = {
    "P01116": {
        "name": "KRAS",
        "function": (
            "Ras-related GTPase; oncogenic driver when mutated at G12/G13. "
            "Regulates MAPK and PI3K/AKT signaling."
        ),
        "length": 189,
        "organism": "Homo sapiens",
    },
    "P04637": {
        "name": "TP53",
        "function": (
            "Tumor suppressor; DNA-binding transcription factor. "
            "Hotspot mutations at R175, R248, R273, R282 disrupt DBD."
        ),
        "length": 393,
        "organism": "Homo sapiens",
    },
    "P00533": {
        "name": "EGFR",
        "function": "Receptor tyrosine kinase; therapeutic target in NSCLC and glioma.",
        "length": 1210,
        "organism": "Homo sapiens",
    },
}

_PDB_SEED: dict[str, dict[str, Any]] = {
    "2OCJ": {
        "title": "TP53 DNA-binding domain in complex with DNA",
        "resolution_angstrom": 2.05,
        "chains": ["A", "B", "C"],
        "ligands": [],
    },
    "6VJJ": {
        "title": "KRAS G12D in complex with GDP",
        "resolution_angstrom": 1.55,
        "chains": ["A"],
        "ligands": ["GDP", "MG"],
    },
}

_PUBMED_SEED: list[dict[str, Any]] = [
    {
        "pmid": "35678145",
        "title": "KRAS-G12D inhibitors in pancreatic ductal adenocarcinoma: a review.",
        "year": 2024,
        "journal": "Cancer Cell",
        "abstract": (
            "KRAS-G12D is the dominant driver in pancreatic cancer. Recent covalent "
            "inhibitors targeting the switch-II pocket show promise; combinations with "
            "SOS1 and SHP2 inhibitors deepen response."
        ),
    },
    {
        "pmid": "33012345",
        "title": "Tp53 R273H structural basis for DNA-binding loss.",
        "year": 2021,
        "journal": "Structure",
        "abstract": (
            "The R273H mutation disrupts the arginine-phosphate salt bridge to DNA; "
            "PDB 2OCJ captures the wild-type state for comparison."
        ),
    },
]

_CHEMBL_SEED: dict[str, dict[str, Any]] = {
    "CHEMBL941": {
        "name": "IMATINIB",
        "targets": ["ABL1", "KIT", "PDGFRA"],
        "approval_year": 2001,
    },
    "CHEMBL25": {
        "name": "ASPIRIN",
        "targets": ["PTGS1", "PTGS2"],
        "approval_year": None,
    },
}


# ---- tool definitions --------------------------------------------------------


class UniProtArgs(BaseModel):
    accession: str = Field(..., description="UniProt accession (e.g., P01116)")


class MockUniProt(Tool):
    name = "uniprot_query"
    description = "Fetch a UniProt protein record by accession (mock)."
    risk = "low"
    writes = False

    ArgsModel = UniProtArgs

    def run(self, args: UniProtArgs) -> str:
        rec = _UNIPROT_SEED.get(args.accession.upper())
        if rec is None:
            raise ToolError(f"no UniProt record for {args.accession!r}")
        return (
            f"UniProt:{args.accession.upper()} — {rec['name']} ({rec['organism']}, "
            f"{rec['length']} aa). {rec['function']}"
        )


class PDBArgs(BaseModel):
    pdb_id: str = Field(..., description="PDB 4-char ID (e.g., 2OCJ)")


class MockPDB(Tool):
    name = "pdb_query"
    description = "Fetch PDB structure metadata (mock)."
    risk = "low"
    writes = False

    ArgsModel = PDBArgs

    def run(self, args: PDBArgs) -> str:
        rec = _PDB_SEED.get(args.pdb_id.upper())
        if rec is None:
            raise ToolError(f"no PDB record for {args.pdb_id!r}")
        return (
            f"PDB:{args.pdb_id.upper()} — {rec['title']}. "
            f"Resolution {rec['resolution_angstrom']} Å; chains {','.join(rec['chains'])}; "
            f"ligands {','.join(rec['ligands']) if rec['ligands'] else 'none'}."
        )


class AlphaFoldArgs(BaseModel):
    accession: str = Field(..., description="UniProt accession for AlphaFold structure")


class MockAlphaFold(Tool):
    name = "alphafold_fetch"
    description = "Fetch AlphaFold predicted structure metadata (mock)."
    risk = "low"
    writes = False

    ArgsModel = AlphaFoldArgs

    def run(self, args: AlphaFoldArgs) -> str:
        if args.accession.upper() not in _UNIPROT_SEED:
            raise ToolError(f"no AlphaFold prediction for {args.accession!r}")
        return (
            f"AlphaFold:{args.accession.upper()} — high-confidence (mean pLDDT 88.3) "
            f"predicted structure available; mock download URL omitted."
        )


class BLASTArgs(BaseModel):
    sequence: str = Field(..., min_length=10, max_length=2000)
    e_value_cap: float = Field(default=1e-5, gt=0.0)


class MockBLAST(Tool):
    name = "blast_search"
    description = "Submit a sequence to BLAST (mock; returns a canned hit list)."
    risk = "low"
    writes = False

    ArgsModel = BLASTArgs

    def run(self, args: BLASTArgs) -> str:
        first_10 = args.sequence[:10].upper()
        # Deterministic-ish mock hits
        return (
            f"BLAST hits for sequence starting with {first_10}...: "
            f"[(P04637, e=2.1e-08, id=98%), (P01116, e=3.4e-07, id=76%)]"
        )


class PubMedArgs(BaseModel):
    query: str = Field(..., min_length=2)
    max_results: int = Field(default=3, ge=1, le=20)


class MockPubMed(Tool):
    name = "pubmed_search"
    description = "Search PubMed abstracts (mock; returns canned records)."
    risk = "low"
    writes = False

    ArgsModel = PubMedArgs

    def run(self, args: PubMedArgs) -> str:
        q = args.query.lower()
        hits = [r for r in _PUBMED_SEED if any(w in r["abstract"].lower() or w in r["title"].lower() for w in q.split())]
        if not hits:
            hits = _PUBMED_SEED[: args.max_results]
        out = []
        for r in hits[: args.max_results]:
            out.append(
                f"PMID:{r['pmid']} — {r['title']} ({r['journal']}, {r['year']}). "
                f"Abstract: {r['abstract']}"
            )
        return "\n\n".join(out)


class ChEMBLArgs(BaseModel):
    chembl_id: str = Field(..., description="ChEMBL compound ID")


class MockChEMBL(Tool):
    name = "chembl_query"
    description = "Fetch ChEMBL compound record (mock)."
    risk = "low"
    writes = False

    ArgsModel = ChEMBLArgs

    def run(self, args: ChEMBLArgs) -> str:
        rec = _CHEMBL_SEED.get(args.chembl_id.upper())
        if rec is None:
            raise ToolError(f"no ChEMBL record for {args.chembl_id!r}")
        targets = ", ".join(rec["targets"])
        yr = rec["approval_year"] if rec["approval_year"] else "not approved"
        return f"ChEMBL:{args.chembl_id.upper()} — {rec['name']} targets {targets}; approval {yr}."


class EnsemblArgs(BaseModel):
    ensembl_id: str = Field(..., description="Ensembl gene / transcript ID")


class MockEnsembl(Tool):
    name = "ensembl_query"
    description = "Fetch Ensembl gene metadata (mock)."
    risk = "low"
    writes = False

    ArgsModel = EnsemblArgs

    def run(self, args: EnsemblArgs) -> str:
        ref = args.ensembl_id.upper()
        if not ref.startswith("ENS"):
            raise ToolError(f"not an Ensembl ID: {args.ensembl_id!r}")
        return f"Ensembl:{ref} — gene metadata (mock): chromosome, strand, biotype=protein_coding."


# ---- public helpers ----------------------------------------------------------


def build_default_tools() -> ToolRegistry:
    """Return a ToolRegistry preloaded with all mock biomedical tools."""
    registry = ToolRegistry()
    registry.register(MockUniProt())
    registry.register(MockPDB())
    registry.register(MockAlphaFold())
    registry.register(MockBLAST())
    registry.register(MockPubMed())
    registry.register(MockChEMBL())
    registry.register(MockEnsembl())
    return registry


def source_ref_for(tool_name: str, identifier: str) -> SourceRef:
    """Map a tool name + identifier to a SourceRef with correct trust tier."""
    kind_map = {
        "uniprot_query": ("uniprot", "authoritative"),
        "pdb_query": ("pdb", "authoritative"),
        "alphafold_fetch": ("alphafold", "authoritative"),
        "blast_search": ("blast", "authoritative"),
        "pubmed_search": ("pubmed", "peer_reviewed"),
        "chembl_query": ("chembl", "authoritative"),
        "ensembl_query": ("ensembl", "authoritative"),
    }
    kind, tier = kind_map.get(tool_name, ("mock", "web"))
    return SourceRef(
        kind=kind,
        identifier=f"mock://{kind}/{identifier}",
        title=f"{kind}:{identifier}",
        trust_tier=tier,
    )


def ids_in_content(content: str) -> list[OntologyID]:
    """Quick scan for canonical IDs in tool output so we can bind evidence."""
    from .ontology import OntologyGrounder

    return OntologyGrounder().parse_canonical(content)
