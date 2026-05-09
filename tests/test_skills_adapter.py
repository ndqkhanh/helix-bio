"""Helix-Bio skills-adapter smoke test."""
from __future__ import annotations

from harness_skills import Skill, SkillRecord, TrustTier
from helix_bio.skills_adapter import (
    HelixDocumentExtractor,
    HelixResearcherPrefExtractor,
    HelixSkillBank,
    phi_gate,
    resolve_trust_tier,
)

PROTOCOL = """
Title: Sample Protocol

Procedure:
1. Choose the buffer concentration.
2. Initialize the apparatus at 25C.
3. Apply the reagent over 30 minutes.
4. Verify the reading against the calibration curve.
5. Record the timestamped output.
"""


def test_phi_gate_blocks_identifiers() -> None:
    assert not phi_gate("DOB 01/02/1990")
    assert not phi_gate("MRN 123456")
    assert not phi_gate("SSN 123-45-6789")
    assert phi_gate("Apply reagent for 30 minutes")


def test_trust_tier_resolution() -> None:
    assert resolve_trust_tier("https://pubmed.ncbi.nlm.nih.gov/12345") is TrustTier.T1_PEER_REVIEWED
    assert resolve_trust_tier("https://www.biorxiv.org/...") is TrustTier.T2_PREPRINT
    assert resolve_trust_tier("https://random.blog/post") is TrustTier.T3_DISCUSSION


def test_protocol_extracts_with_t1_when_pubmed() -> None:
    ext = HelixDocumentExtractor.default()
    out = ext.from_protocol(
        source="https://pubmed.ncbi.nlm.nih.gov/12345",
        title="Sample Protocol",
        body=PROTOCOL,
        session_id="prog-1",
    )
    assert out
    assert all(r.trust_tier is TrustTier.T1_PEER_REVIEWED for r in out)


def test_phi_in_body_blocks_extraction() -> None:
    ext = HelixDocumentExtractor.default()
    out = ext.from_protocol(
        source="https://pubmed.ncbi.nlm.nih.gov/12345",
        title="Sample",
        body=PROTOCOL + "\nMRN 998877 patient observed.\n",
        session_id="prog-2",
    )
    assert out == []


def test_researcher_pref_namespace_isolation(tmp_path) -> None:
    a = HelixSkillBank.for_researcher(tmp_path, researcher_id="alice")
    b = HelixSkillBank.for_researcher(tmp_path, researcher_id="bob")
    assert a.bank.active_dir != b.bank.active_dir


def test_trust_gate_refuses_red_tier() -> None:
    bank = HelixSkillBank.for_researcher("/tmp/helix-bank", researcher_id="x")
    rec = SkillRecord(
        skill=Skill(name="x", description="x", prompt="x"),
        trust_tier=TrustTier.RED_RETRACTED,
    )
    ok, msg = bank.admit(rec)
    assert not ok
    assert "RED" in msg
