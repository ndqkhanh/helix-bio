from helix_bio.models import (
    Brief,
    Claim,
    Evidence,
    OntologyID,
    Report,
    Section,
    SourceRef,
)


def test_ontology_id_canonical():
    oid = OntologyID(namespace="UniProt", value="P01116")
    assert oid.canonical() == "UniProt:P01116"
    assert str(oid) == "UniProt:P01116"


def test_brief_defaults():
    b = Brief(question="What is KRAS?")
    assert b.audience == "bench_scientist"
    assert b.scope == "preclinical"
    assert b.max_cost_usd == 2.0


def test_source_ref_defaults_authoritative_tier():
    ref = SourceRef(kind="uniprot", identifier="mock://uniprot/P01116")
    assert ref.trust_tier == "authoritative"


def test_report_markdown_includes_citations_and_ontology_ids():
    brief = Brief(question="KRAS?")
    ev = Evidence(
        id="e1",
        source=SourceRef(kind="uniprot", identifier="mock://u/P01116", title="UniProt P01116"),
        content="KRAS record",
        ontology_ids=[OntologyID(namespace="UniProt", value="P01116")],
    )
    claim = Claim(
        text="KRAS is a GTPase",
        evidence_ids=["e1"],
        cited_ontology_ids=[OntologyID(namespace="UniProt", value="P01116")],
        verified=True,
    )
    report = Report(
        brief=brief,
        sections=[Section(title="Findings", claims=[claim])],
        references=[ev.source],
        faithfulness_ratio=1.0,
    )
    md = report.to_markdown()
    assert "KRAS is a GTPase" in md
    assert "[1]" in md
    assert "UniProt:P01116" in md
    assert "References" in md


def test_unverified_claim_marked_in_markdown():
    brief = Brief(question="x")
    claim = Claim(text="orphan", evidence_ids=["missing"], verified=False)
    report = Report(
        brief=brief,
        sections=[Section(title="x", claims=[claim])],
        references=[],
    )
    md = report.to_markdown()
    assert "*(unverified)*" in md
