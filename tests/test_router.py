from helix_bio.models import Brief, OntologyID
from helix_bio.router import KnowledgeRouter


def test_plan_for_uniprot_adds_protein_and_alphafold():
    decisions = KnowledgeRouter().plan_for_entity(
        OntologyID(namespace="UniProt", value="P01116")
    )
    tools = [d.tool for d in decisions]
    assert "uniprot_query" in tools
    assert "alphafold_fetch" in tools


def test_plan_for_pdb():
    decisions = KnowledgeRouter().plan_for_entity(
        OntologyID(namespace="PDB", value="2OCJ")
    )
    assert decisions[0].tool == "pdb_query"


def test_plan_for_chembl():
    decisions = KnowledgeRouter().plan_for_entity(
        OntologyID(namespace="ChEMBL", value="CHEMBL941")
    )
    assert decisions[0].tool == "chembl_query"


def test_plan_for_ensembl():
    decisions = KnowledgeRouter().plan_for_entity(
        OntologyID(namespace="Ensembl", value="ENSG00000133703")
    )
    assert decisions[0].tool == "ensembl_query"


def test_plan_ignores_hgnc_and_mesh_without_direct_tool():
    assert KnowledgeRouter().plan_for_entity(OntologyID(namespace="HGNC", value="6407")) == []
    assert KnowledgeRouter().plan_for_entity(OntologyID(namespace="MeSH", value="D010190")) == []


def test_build_plan_includes_pubmed_for_question():
    brief = Brief(question="What is KRAS?")
    plan = KnowledgeRouter().build_plan(
        brief,
        [OntologyID(namespace="UniProt", value="P01116")],
    )
    tools = [d.tool for d in plan.decisions]
    assert "uniprot_query" in tools
    assert "alphafold_fetch" in tools
    assert "pubmed_search" in tools


def test_build_plan_empty_entities_still_has_pubmed():
    plan = KnowledgeRouter().build_plan(Brief(question="x"), [])
    assert len(plan.decisions) == 1
    assert plan.decisions[0].tool == "pubmed_search"
