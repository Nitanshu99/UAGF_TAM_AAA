"""Fix 23 — T18's manifest says which artefacts its own schema admits.

``embedded_artefacts`` is documented as holding "every **admitted** T01a–T17
artefact" and held every artefact, admitted or not: 7 of the 17 entries in the
run's delivered T18 were rejected or uncritiqued.  The block is the report's
manifest, so the remedy is to label them, not to drop them — a reader must be
able to tell a model card that was produced and sent back from one that was
never produced at all.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.agents.tier2.report_architect.t18 import build_t18
from aaa.agents.tier2.report_architect.t18.sections import embedded_artefacts
from aaa.platform.state.admission import admitted_artefacts
from aaa.tools.report_render.text.sections import artefact_lines

_SCHEMAS = ("templates/T18_audit_report.json",
            "packages/uagf_tam_templates/src/uagf_tam_templates/schemas/T18_audit_report.json")

_CRITIQUES = {
    "T02_system_card": {"verdict": "accept_with_notes"},
    "T06_datasheet_for_datasets": {"verdict": "escalate_hitl"},
    "T09_model_card": {"verdict": "rerun"},
    "T14_governance_findings": {"verdict": "accept"},
    "T15_monitoring_logging_review": {"verdict": "unverified"},
}

_ARTEFACTS = ("T01a_stage_a_triage", "T01b_annex_iv_dossier",
              "T01c_intake_completeness_report", "T02_system_card",
              "T06_datasheet_for_datasets", "T09_model_card",
              "T14_governance_findings", "T15_monitoring_logging_review")


def _state(**over: object) -> dict:
    state: dict = {
        "verifier_critiques": {k: dict(v) for k, v in _CRITIQUES.items()},
        "phase_artefacts": {tid: {"uri": f"minio://e/p/{tid}.json", "sha256": "a" * 64}
                            for tid in _ARTEFACTS},
    }
    state.update(over)
    return state


# --------------------------------------------------------------------------
# nothing is dropped
# --------------------------------------------------------------------------
def test_a_rejected_artefact_stays_in_the_manifest():
    """Filtering would delete the reader's only pointer to it."""
    assert "T09_model_card" in embedded_artefacts(_state())


def test_the_manifest_holds_every_non_stub_artefact():
    """It is an inventory of what was produced, not a list of what was accepted."""
    assert set(embedded_artefacts(_state())) == set(_ARTEFACTS)


def test_a_stub_uri_is_still_dropped():
    """Regression guard: the one filter this block always had."""
    state = _state()
    state["phase_artefacts"]["T13_output_sampling_log"] = {"uri": "minio://e/p/stub.json"}
    assert "T13_output_sampling_log" not in embedded_artefacts(state)


def test_the_reference_fields_are_untouched():
    """Fix 23 adds; it does not rewrite what a consumer already reads."""
    ref = embedded_artefacts(_state())["T02_system_card"]
    assert ref["uri"] == "minio://e/p/T02_system_card.json"
    assert ref["sha256"] == "a" * 64
    assert ref["template_id"] == "T02_system_card"


# --------------------------------------------------------------------------
# every entry says what the Verifier made of it
# --------------------------------------------------------------------------
@pytest.mark.parametrize("tid, verdict, admitted", [
    ("T02_system_card", "accept_with_notes", True),
    ("T14_governance_findings", "accept", True),
    ("T06_datasheet_for_datasets", "escalate_hitl", False),
    ("T09_model_card", "rerun", False),
    ("T15_monitoring_logging_review", "unverified", False),
    ("T01a_stage_a_triage", "not critiqued", False),
    ("T01b_annex_iv_dossier", "not critiqued", True),
])
def test_each_entry_carries_its_verdict_and_whether_it_admits(tid, verdict, admitted):
    """Including fix 20's ``unverified``, which is a check that did not run."""
    ref = embedded_artefacts(_state())[tid]

    assert (ref["verifier_verdict"], ref["admitted"]) == (verdict, admitted)


def test_uncritiqued_is_not_reported_as_rejected():
    """'not critiqued' and 'rerun' are different findings about an artefact."""
    verdicts = {tid: ref["verifier_verdict"]
                for tid, ref in embedded_artefacts(_state()).items()}

    assert verdicts["T01c_intake_completeness_report"] == "not critiqued"
    assert verdicts["T09_model_card"] == "rerun"


def test_the_manifest_and_the_matrix_agree_on_every_artefact():
    """One predicate: T17's evidence list and T18's manifest cannot disagree."""
    state = _state()
    admitted = admitted_artefacts(state)

    assert {tid for tid, ref in embedded_artefacts(state).items()
            if ref["admitted"]} == admitted & set(_ARTEFACTS)


def test_a_tier3_spawn_is_listed_uncritiqued_under_its_real_template():
    """Fix 19 left the spawns uncritiqued; the manifest now shows that it did."""
    state = _state()
    state["phase_artefacts"]["T11_robustness_report@Cyber"] = {
        "uri": "minio://e/cyber/T11.json", "template_id": "T11_robustness_report"}
    ref = embedded_artefacts(state)["T11_robustness_report@Cyber"]

    assert ref["template_id"] == "T11_robustness_report"
    assert (ref["verifier_verdict"], ref["admitted"]) == ("not critiqued", False)


# --------------------------------------------------------------------------
# it reaches the reader
# --------------------------------------------------------------------------
def test_the_text_report_prints_the_verdict_beside_the_uri():
    """A URI on its own does not say whether the artefact behind it was admitted."""
    lines = artefact_lines({"embedded_artefacts": embedded_artefacts(_state())})

    assert any("T09_model_card" in ln and "[rerun]" in ln for ln in lines)


def test_the_text_report_tolerates_a_manifest_without_the_field():
    """A T18 written before this fix still renders."""
    lines = artefact_lines({"embedded_artefacts": {"T02_system_card": {"uri": "minio://x"}}})

    assert any("minio://x" in ln and "[" not in ln.split("→")[1] for ln in lines)


@pytest.mark.parametrize("schema_path", _SCHEMAS)
def test_both_schema_copies_declare_the_two_fields(schema_path):
    """`additionalProperties: true` allowed them; the contract should still say so."""
    block = json.loads(Path(schema_path).read_text(encoding="utf-8")
                       )["properties"]["embedded_artefacts"]
    props = block["additionalProperties"]["properties"]

    assert props["verifier_verdict"]["type"] == "string"
    assert props["admitted"]["type"] == "boolean"


@pytest.mark.parametrize("schema_path", _SCHEMAS)
def test_neither_schema_copy_still_claims_every_entry_is_admitted(schema_path):
    """The description was the false claim; the code was only following it."""
    block = json.loads(Path(schema_path).read_text(encoding="utf-8")
                       )["properties"]["embedded_artefacts"]

    assert "for every admitted" not in block["description"]
    assert "admitted=true" in block["description"]


def test_an_annotated_t18_validates_through_the_real_loader():
    """The schema the renderer actually loads is `templates/`, not the packaged copy."""
    from aaa.tools.template_render.logger import _load_schema, _validate_payload

    ref = {"template_id": "T17_compliance_matrix", "uri": "minio://eng/t17.json",
           "sha256": "0" * 64, "created_at": "2026-08-21T00:00:00+00:00"}
    t18 = build_t18("eng-01", {**_state(), "stage_a": {}, "hitl_required": False}, ref,
                    "2026-08-21T00:00:00+00:00")

    assert t18["embedded_artefacts"]["T09_model_card"]["admitted"] is False
    assert not _validate_payload(t18, _load_schema("T18_audit_report"), "T18_audit_report")
