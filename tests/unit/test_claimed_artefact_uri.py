"""What the model asserts about the evidence is not what the trail records.

Two findings from the 2026-09-09 Mariposa assessment, both about a claim reaching
a consumer that had no basis for it.

**Every tier-2 phase agent invented its own ``artefact_uri``.** The tells across
one run: ``T02_system_card_a1b2c3d4.json`` beside ``_e5f6g7h8`` and ``_i9j0k1l2``
(#004), one hash shared by three separately content-hashed artefacts (#022), a
``_v2`` suffix (#026), a ``_20250115`` stamp in the wrong year (#036), no hash at
all (#043). Tier-3 did not: #048 and #050 extended real hashes they were given.
The Verifier was never fooled — it reads ``phase_artefacts`` — but
``latest_report`` is handed to the Orchestrator every turn, so a URI resolving to
nothing was presented to the planner as its evidence.

**The planner was shown only what *was* admitted.** At #051 it moved to
ASSEMBLE_MATRIX reasoning "all mandatory phases have completed with
Verifier-admitted artefacts" while T05, T09, T11, T13 and T15 had been escalated.
A short list read as a complete one.
"""
from __future__ import annotations

from aaa.agents.tier1.orchestrator.react.summary import build_envelope
from aaa.agents.tier1.phases.verification.phase_outcome import record_phase_outcome

#: Verbatim from call #004 of the assessed run.
FABRICATED = "minio://eng-06_mariposa_edu_gmbh/phase_1/T02_system_card_a1b2c3d4.json"
STORED = "minio://eng-06_mariposa_edu_gmbh/phase_1/T02_system_card_c7114d4b.json"


def _state() -> dict:
    return {"phase_artefacts": {"T02_system_card": {"uri": STORED, "sha256": "c711"}}}


def _record(state: dict, claimed: str | None) -> dict:
    report = {"summary": "Phase 1 done.", "confidence": 0.9}
    if claimed is not None:
        report["artefact_uri"] = claimed
    record_phase_outcome(state, report, ["T02_system_card"], phase_id="P1",
                         phase_label="Phase 1 ScopeAgent", worst="accept", rerun_count=0)
    return state["latest_report"]


def test_the_fabricated_uri_never_reaches_the_planner():
    """The acceptance criterion, stated as an assertion."""
    assert _record(_state(), FABRICATED)["artefact_uri"] == STORED


def test_the_divergence_is_logged_not_silently_corrected(caplog):
    """Same treatment as a claimed report_signed (F15): discarded, never quietly."""
    with caplog.at_level("WARNING"):
        _record(_state(), FABRICATED)
    assert FABRICATED in caplog.text
    assert "never issued" in caplog.text


def test_an_honest_report_is_not_warned_about(caplog):
    """An agent that echoes the real URI must produce no noise."""
    with caplog.at_level("WARNING"):
        assert _record(_state(), STORED)["artefact_uri"] == STORED
    assert "never issued" not in caplog.text


def test_a_report_claiming_nothing_still_gets_the_stored_uri():
    """The field is derived, so it is populated whether or not the model spoke."""
    assert _record(_state(), None)["artefact_uri"] == STORED


def test_nothing_stored_yields_empty_rather_than_the_claim():
    """A phase that stored nothing must not be credited with the model's guess."""
    state = {"phase_artefacts": {}}
    assert _record(state, FABRICATED)["artefact_uri"] == ""


# --------------------------------------------------------------------------
# what the planner is shown about admission
# --------------------------------------------------------------------------
def test_the_planner_is_told_which_artefacts_were_not_admitted():
    """Absence from the admitted list is too weak a signal to sequence on."""
    state = {"engagement_id": "eng-x", "unadmitted_artefacts": [
        {"template_id": "T09_model_card", "verdict": "escalate_hitl",
         "articles": ["Art.13", "Art.15"]}]}
    shown = build_envelope(state, [])["audit_state_summary"]
    assert shown["phase_artefacts_not_admitted"] == [
        {"template_id": "T09_model_card", "verdict": "escalate_hitl",
         "articles_held": ["Art.13", "Art.15"]}]


def test_a_run_with_everything_admitted_shows_an_empty_list():
    """Empty, not absent — the planner should read a fact, not a missing key."""
    shown = build_envelope({"engagement_id": "eng-x"}, [])["audit_state_summary"]
    assert shown["phase_artefacts_not_admitted"] == []


def test_a_claim_naming_another_of_this_phases_artefacts_is_kept():
    """Phase 6 emits T17 then T18 and reports T18 — that is not a fabrication.

    Insisting on ``tids[0]`` replaced a real T18 URI with T17's and logged a
    fabrication warning against an honest report, which is worse than the defect
    the check exists for.
    """
    t17 = "minio://eng/phase_6/T17_compliance_matrix_f7204950.json"
    t18 = "minio://eng/phase_6/T18_audit_report_085df096.json"
    state = {"phase_artefacts": {"T17_compliance_matrix": {"uri": t17},
                                 "T18_audit_report": {"uri": t18}}}
    record_phase_outcome(state, {"summary": "done", "artefact_uri": t18},
                         ["T17_compliance_matrix", "T18_audit_report"],
                         phase_id="P6", phase_label="Phase 6 ReportArchitect",
                         worst="accept", rerun_count=0)
    assert state["latest_report"]["artefact_uri"] == t18


def test_an_honest_multi_artefact_claim_is_not_warned_about(caplog):
    """No warning, because nothing was fabricated."""
    t17 = "minio://eng/phase_6/T17_compliance_matrix_f7204950.json"
    t18 = "minio://eng/phase_6/T18_audit_report_085df096.json"
    state = {"phase_artefacts": {"T17_compliance_matrix": {"uri": t17},
                                 "T18_audit_report": {"uri": t18}}}
    with caplog.at_level("WARNING"):
        record_phase_outcome(state, {"summary": "done", "artefact_uri": t18},
                             ["T17_compliance_matrix", "T18_audit_report"],
                             phase_id="P6", phase_label="Phase 6",
                             worst="accept", rerun_count=0)
    assert "never issued" not in caplog.text
