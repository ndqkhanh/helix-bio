from harness_core.messages import ToolCall
from helix_bio.tools import build_default_tools


def _call(name: str, **args) -> ToolCall:
    return ToolCall(id="c1", name=name, args=args)


def test_uniprot_known_accession():
    r = build_default_tools().execute(_call("uniprot_query", accession="P01116"))
    assert not r.is_error
    assert "KRAS" in r.content
    assert "UniProt:P01116" in r.content


def test_uniprot_unknown_accession_returns_error():
    r = build_default_tools().execute(_call("uniprot_query", accession="X00000"))
    assert r.is_error
    assert "no UniProt" in r.content


def test_pdb_returns_resolution():
    r = build_default_tools().execute(_call("pdb_query", pdb_id="2OCJ"))
    assert not r.is_error
    assert "PDB:2OCJ" in r.content
    assert "2.05" in r.content


def test_alphafold_requires_known_accession():
    r = build_default_tools().execute(_call("alphafold_fetch", accession="P01116"))
    assert not r.is_error
    assert "pLDDT" in r.content


def test_blast_returns_hits_for_sequence():
    r = build_default_tools().execute(
        _call("blast_search", sequence="MTEYKLVVVGAGGVGKSAL")
    )
    assert not r.is_error
    assert "BLAST hits" in r.content


def test_blast_rejects_short_sequence():
    r = build_default_tools().execute(_call("blast_search", sequence="MT"))
    assert r.is_error
    assert "validation" in r.content


def test_pubmed_returns_hits():
    r = build_default_tools().execute(
        _call("pubmed_search", query="kras pancreatic")
    )
    assert not r.is_error
    assert "PMID:" in r.content


def test_chembl_known_compound():
    r = build_default_tools().execute(_call("chembl_query", chembl_id="CHEMBL941"))
    assert not r.is_error
    assert "IMATINIB" in r.content


def test_ensembl_known_id():
    r = build_default_tools().execute(_call("ensembl_query", ensembl_id="ENSG00000133703"))
    assert not r.is_error
    assert "Ensembl:ENSG00000133703" in r.content


def test_ensembl_wrong_prefix():
    r = build_default_tools().execute(_call("ensembl_query", ensembl_id="ABC123"))
    assert r.is_error
    assert "not an Ensembl ID" in r.content
