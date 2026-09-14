"""Unit tests for stamping ``s6_fields`` into the delivered file (fix F16, finding S24).

``build_s6_fields`` has been correct since F8-F15, but until this fix it was
only ever passed to ``build_handoff`` for the mid-pipeline external XAI /
security evaluate-API call — no code wrote it into
``<engagement_id>_audit_state.json``, the file a human (or S6's own tooling)
actually opens under ``data/customer/``. A raw-file re-verification against the
spreadsheet's own "Source field(s) in S5 JSON" column, run independently of
this package, is what surfaced the gap: ``client_submission.stage_b.
sensitive_feature_columns`` was genuinely **absent** — not merely ``null`` — on
three of five delivered engagements, because nothing had ever normalised it in
the file itself.
"""
from __future__ import annotations

import json
from pathlib import Path

from aaa.data.writer import save_customer_artefacts
from aaa.integrations.s6_contract import S6_CONTRACT_WARNINGS_KEY, S6_FIELDS_KEY

_DIR = Path("tests/fixtures/customer_finclear")


class _NullStore:
    """No T17/T18 payloads; exercises the stamp without a PDF build."""

    is_durable = True

    def get_artefact(self, uri: str | None) -> dict | None:  # noqa: ARG002
        return None


def _write_and_reload(engagement_id: str, state: dict, tmp_path, monkeypatch) -> dict:
    """Round-trip *state* through the real writer and read the file back."""
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path))
    cdir = save_customer_artefacts(engagement_id, state, _NullStore())
    assert cdir is not None
    return json.loads((cdir / f"{engagement_id}_audit_state.json").read_text("utf-8"))


def test_delivered_file_carries_s6_fields(tmp_path, monkeypatch) -> None:
    """The persisted JSON — not a return value — carries the projection."""
    state = json.loads((_DIR / "eng-01_finclear_gmbh_audit_state.json").read_text("utf-8"))
    delivered = _write_and_reload("eng-01_finclear_gmbh", state, tmp_path, monkeypatch)
    assert S6_FIELDS_KEY in delivered
    assert delivered[S6_FIELDS_KEY]["provider_name"] == "FinClear GmbH"
    assert S6_CONTRACT_WARNINGS_KEY in delivered


def test_sensitive_feature_columns_is_a_list_never_absent(tmp_path, monkeypatch) -> None:
    """The exact defect the raw-file re-check found: a genuinely missing key.

    An engagement with nothing declared previously wrote no
    ``sensitive_feature_columns`` key into ``s6_fields`` at all. It must now be
    an explicit ``[]`` with a reason, per the sheet's own contract.
    """
    state = {"client_submission": {"stage_b": {}}, "phase_artefacts": {},
            "phase_plan": {"P4": "O"}}
    delivered = _write_and_reload("eng-no-sensitive", state, tmp_path, monkeypatch)
    fields = delivered[S6_FIELDS_KEY]
    assert "sensitive_feature_columns" in fields
    assert fields["sensitive_feature_columns"] == []
    assert fields["sensitive_feature_columns_skip_reason"]


def test_stamp_reflects_the_state_at_write_time_not_a_stale_copy(tmp_path, monkeypatch) -> None:
    """Two different states, written back to back, must not share a stamp.

    Guards against the class of bug this whole gap belongs to: a projection
    computed once and reused, rather than derived from the file being written.
    """
    first = {"cgsa_payload": {"domains": [
        {"domain_name": "Risk Management", "domain_score": 4.0}]}}
    second = {"cgsa_payload": None}
    delivered_1 = _write_and_reload("eng-first", first, tmp_path, monkeypatch)
    delivered_2 = _write_and_reload("eng-second", second, tmp_path, monkeypatch)
    assert delivered_1[S6_FIELDS_KEY]["domain_scores"] == {"Risk Management": 4.0}
    assert delivered_2[S6_FIELDS_KEY]["domain_scores"] == {}


def test_stamp_is_json_round_trippable(tmp_path, monkeypatch) -> None:
    """The whole point is a file on disk; it must actually parse back."""
    state = json.loads((_DIR / "eng-01_finclear_gmbh_audit_state.json").read_text("utf-8"))
    delivered = _write_and_reload("eng-01_finclear_gmbh", state, tmp_path, monkeypatch)
    assert isinstance(delivered[S6_FIELDS_KEY]["domain_scores"], dict)
    assert isinstance(delivered[S6_FIELDS_KEY]["blocking_findings"], list)
