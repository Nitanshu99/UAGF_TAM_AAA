"""Every stored artefact is checked against its template, and the run says which failed.

Only T17/T18 were validated; case 06's T14 reached the deliverable with 108 schema
errors and nothing in the run recorded it (T-20260913-018).
"""
from __future__ import annotations

from typing import Any

from aaa.data.writer.schema_stamp import stamp_schema_violations
from aaa.platform.evidence.backend.memory import MemoryBackend
from aaa.platform.evidence.contract import MAX_RECORDED_ERRORS, artefact_schema_errors
from aaa.platform.evidence.store import EvidenceStore
from aaa.platform.state.artefact_keys import namespaced_key


def _store_one(content: Any, artefact_type: str = "T14_governance_findings") -> tuple:
    store = EvidenceStore(MemoryBackend())
    uri = store.store_artefact("eng-t", "phase_5", artefact_type, content, "GovernanceAgent")
    return store, uri, store.get_index("eng-t")[-1]


def test_an_invalid_artefact_is_stored_with_its_errors() -> None:
    """Stored, not refused; the index entry carries the count and the first errors."""
    _store, uri, entry = _store_one({"engagement_id": "eng-t", "unexpected": 1})
    assert uri.startswith("minio://eng-t/phase_5/T14_governance_findings_")
    assert entry["schema_error_count"] > 0
    assert 0 < len(entry["schema_errors"]) <= MAX_RECORDED_ERRORS
    assert any("unexpected" in e or "required" in e for e in entry["schema_errors"])


def test_an_artefact_without_a_template_carries_no_contract_fields() -> None:
    """No template, no claim either way."""
    _store, _uri, entry = _store_one({"anything": True}, "hitl_review_packet")
    assert "schema_error_count" not in entry


def test_a_spawn_namespaced_artefact_is_checked_against_its_base_template() -> None:
    """Tier-3 artefacts validate against the template they are an instance of."""
    key = namespaced_key("T08_special_category_data_log", "privacy")
    assert artefact_schema_errors(key, {}) is not None


def test_the_deliverable_lists_the_failing_artefacts() -> None:
    """``run_integrity`` names each artefact key with its error count."""
    store, uri, entry = _store_one({"engagement_id": "eng-t"})
    integrity: dict[str, Any] = {}
    state = {"phase_artefacts": {"T14_governance_findings": {"uri": uri}}}
    stamp_schema_violations(integrity, state, "eng-t", store)
    assert integrity["schema_invalid_artefacts"] == {
        "T14_governance_findings": entry["schema_error_count"]}


def test_an_unreadable_index_is_unknown_not_clean() -> None:
    """``None`` says the check could not run; ``{}`` would claim nothing failed."""
    class _Broken:
        def get_index(self, _engagement_id: str) -> list:
            """Fail the way an unreachable backend does."""
            raise RuntimeError("backend down")

    integrity: dict[str, Any] = {}
    stamp_schema_violations(integrity, {"phase_artefacts": {}}, "eng-t", _Broken())
    assert integrity["schema_invalid_artefacts"] is None
