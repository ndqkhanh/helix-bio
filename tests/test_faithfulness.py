from helix_bio.faithfulness import FaithfulnessGate
from helix_bio.models import Brief, Claim, Evidence, OntologyID, Report, Section, SourceRef


def _evidence(content: str, tier: str = "authoritative", oids=None, eid: str = "e1") -> Evidence:
    return Evidence(
        id=eid,
        source=SourceRef(kind="uniprot", identifier=f"mock://u/{eid}", trust_tier=tier),
        content=content,
        ontology_ids=oids or [],
    )


def test_claim_without_evidence_rejected():
    brief = Brief(question="x")
    report = Report(
        brief=brief,
        sections=[Section(title="s", claims=[Claim(text="orphan", evidence_ids=[])])],
        references=[],
    )
    fr = FaithfulnessGate().verify(report, [])
    assert fr.verified_claims == 0
    assert any("no evidence bound" in r for _, r in fr.rejected)


def test_claim_with_missing_evidence_id_rejected():
    brief = Brief(question="x")
    report = Report(
        brief=brief,
        sections=[Section(title="s", claims=[Claim(text="x", evidence_ids=["ghost"])])],
        references=[],
    )
    fr = FaithfulnessGate().verify(report, [])
    assert fr.verified_claims == 0
    assert any("not found" in r for _, r in fr.rejected)


def test_claim_with_ontology_mismatch_rejected():
    ev = _evidence("KRAS is a GTPase", oids=[OntologyID(namespace="UniProt", value="P01116")])
    brief = Brief(question="x")
    claim = Claim(
        text="Something about EGFR",
        evidence_ids=["e1"],
        cited_ontology_ids=[OntologyID(namespace="UniProt", value="P00533")],
    )
    report = Report(
        brief=brief, sections=[Section(title="s", claims=[claim])], references=[]
    )
    fr = FaithfulnessGate().verify(report, [ev])
    assert fr.verified_claims == 0
    assert any("ontology id" in r for _, r in fr.rejected)


def test_claim_with_number_not_in_evidence_rejected():
    ev = _evidence("Resolution of the structure is reported.")
    claim = Claim(text="Resolution is 2.05 angstrom", evidence_ids=["e1"])
    report = Report(
        brief=Brief(question="x"),
        sections=[Section(title="s", claims=[claim])],
        references=[],
    )
    fr = FaithfulnessGate().verify(report, [ev])
    assert fr.verified_claims == 0
    assert any("numeric" in r for _, r in fr.rejected)


def test_clinical_claim_with_weak_source_violates():
    ev = _evidence(
        "Some weak preprint signal about dosing.",
        tier="preprint",
    )
    claim = Claim(
        text="Standard dose",
        evidence_ids=["e1"],
        blocking_clinical=True,
    )
    report = Report(
        brief=Brief(question="x", scope="clinical"),
        sections=[Section(title="s", claims=[claim])],
        references=[],
    )
    fr = FaithfulnessGate().verify(report, [ev])
    assert fr.verified_claims == 0
    assert fr.clinical_violations == [claim.id]


def test_valid_claim_passes():
    ev = _evidence(
        "KRAS is a Ras-related GTPase.",
        oids=[OntologyID(namespace="UniProt", value="P01116")],
    )
    claim = Claim(
        text="KRAS is a Ras-related GTPase.",
        evidence_ids=["e1"],
        cited_ontology_ids=[OntologyID(namespace="UniProt", value="P01116")],
    )
    report = Report(
        brief=Brief(question="x"),
        sections=[Section(title="s", claims=[claim])],
        references=[],
    )
    fr = FaithfulnessGate().verify(report, [ev])
    assert fr.verified_claims == 1
    assert fr.ratio == 1.0


def test_ratio_computed_correctly():
    ev = _evidence("KRAS function statement.", oids=[OntologyID(namespace="UniProt", value="P01116")])
    good = Claim(
        text="KRAS function statement.",
        evidence_ids=["e1"],
        cited_ontology_ids=[OntologyID(namespace="UniProt", value="P01116")],
    )
    bad = Claim(text="unsupported claim with 999", evidence_ids=["e1"])
    report = Report(
        brief=Brief(question="x"),
        sections=[Section(title="s", claims=[good, bad])],
        references=[],
    )
    fr = FaithfulnessGate().verify(report, [ev])
    assert fr.total_claims == 2
    assert fr.verified_claims == 1
    assert fr.ratio == 0.5
