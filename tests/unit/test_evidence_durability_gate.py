"""Fix 22 — a deliverable may not cite an address that dies with the process (P9).

The post-fix run issued a T17 and a T18 addressing nineteen artefacts by
``minio://`` URI over the in-memory backend.  Both backends issue the same URIs
— that is the seam's point — so nothing downstream could tell, and only the
store knows.
"""
from __future__ import annotations

import logging

import pytest

from aaa.agents.tier2.report_architect.signing import signing_status
from aaa.data.writer.customer import save_customer_artefacts
from aaa.platform.evidence import EvidenceStore
from aaa.platform.evidence.backend.memory import MemoryBackend
from aaa.platform.evidence.backend.minio import MinioBackend
from tests.unit.support.fake_minio import FakeMinio


def _t18(**over: object) -> dict:
    base = {"executive_summary": "Two material fairness non-conformities.",
            "report_status": "FINAL"}
    return {**base, **over}


class _Opaque:
    """A backend double that says nothing about durability."""

    def put_payload(self, uri, payload):  # noqa: ARG002
        """Accept and discard."""

    def get_payload(self, uri):  # noqa: ARG002
        """Return nothing."""
        return None

    def put_index_entry(self, entry):  # noqa: ARG002
        """Accept and discard."""

    def list_index(self, engagement_id):  # noqa: ARG002
        """Return no entries."""
        return []


# --------------------------------------------------------------------------
# the backends state the fact
# --------------------------------------------------------------------------
def test_the_memory_backend_is_not_durable():
    """Nothing it holds survives the interpreter, so nothing it addresses does."""
    assert MemoryBackend.durable is False
    assert EvidenceStore(MemoryBackend()).is_durable is False


def test_the_minio_backend_is_durable():
    """Objects outlive the process, so a delivered URI still resolves."""
    assert MinioBackend.durable is True
    assert EvidenceStore(MinioBackend(FakeMinio(), "aaa-evidence")).is_durable is True


def test_a_backend_that_does_not_claim_durability_is_not_credited_with_it():
    """The conservative reading is the one that cannot mislabel a deliverable."""
    assert EvidenceStore(_Opaque()).is_durable is False


def test_the_unit_suite_never_reaches_the_live_object_store():
    """The conftest pin, asserted.

    ``.env`` now says ``minio`` — that is what fix 22 makes it — and a unit test
    must still get a process-local store.  Without the pin one suite run left 77
    objects in the developer's ``aaa-evidence`` bucket.
    """
    assert EvidenceStore().is_durable is False


def test_both_backends_issue_indistinguishable_uris():
    """P9's root: the URI carries no clue, which is why the store has to be asked."""
    kwargs = {"engagement_id": "eng-01", "phase": "phase_6",
              "artefact_type": "T18_audit_report", "content": {"a": 1},
              "agent_name": "ReportArchitect"}
    volatile = EvidenceStore(MemoryBackend()).store_artefact(**kwargs)
    durable = EvidenceStore(MinioBackend(FakeMinio(), "b")).store_artefact(**kwargs)

    assert volatile == durable
    assert volatile.startswith("minio://")


# --------------------------------------------------------------------------
# the signature reads it
# --------------------------------------------------------------------------
def test_a_report_over_a_volatile_store_is_not_signed():
    """The strongest claim the system makes needs an evidence chain that resolves."""
    signed, withheld = signing_status(_t18(), "minio://t18.json", "narrative", False)

    assert signed is False
    assert any("will not resolve" in reason for reason in withheld)


def test_the_same_report_over_a_durable_store_is_signed():
    """The condition is the only difference between the two calls."""
    assert signing_status(_t18(), "minio://t18.json", "narrative", True) == (True, [])


def test_the_reason_joins_the_others_rather_than_replacing_them():
    """A run can fail this and the human-review gate at once, as this one did."""
    _, withheld = signing_status(
        _t18(report_status="PROVISIONAL_PENDING_HITL"), "minio://t18.json", "narrative", False)

    assert len(withheld) == 2
    assert any("pending human review" in r for r in withheld)


def test_the_durability_argument_is_required():
    """A signature must not be granted by a caller that forgot to say."""
    with pytest.raises(TypeError):
        # The omission is the test.
        # pylint: disable=no-value-for-parameter
        signing_status(_t18(), "minio://t18.json", "narrative")  # type: ignore[call-arg]


# --------------------------------------------------------------------------
# the delivery boundary
# --------------------------------------------------------------------------
def _state() -> dict:
    return {"client_submission": {"stage_a": {"provider_name": "FinClear GmbH"}},
            "phase_artefacts": {}, "verifier_critiques": {}}


def test_delivery_over_a_volatile_store_records_that_the_uris_are_dangling(caplog, tmp_path,
                                                                          monkeypatch):
    """The files are still written; what changes is that the run says what they are."""
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path))
    with caplog.at_level(logging.ERROR, logger="aaa.data.writer.customer"):
        save_customer_artefacts("eng-01", _state(), EvidenceStore(MemoryBackend()))

    assert any("unresolvable" in r.getMessage() for r in caplog.records)


def test_delivery_over_a_durable_store_is_silent(caplog, tmp_path, monkeypatch):
    """Silence on the healthy path — the line appears only when it is true."""
    monkeypatch.setenv("AAA_DATA_DIR", str(tmp_path))
    with caplog.at_level(logging.ERROR, logger="aaa.data.writer.customer"):
        save_customer_artefacts("eng-01", _state(),
                                EvidenceStore(MinioBackend(FakeMinio(), "b")))

    assert not [r for r in caplog.records if "unresolvable" in r.getMessage()]


# --------------------------------------------------------------------------
# the run refuses to start
# --------------------------------------------------------------------------
def test_a_real_run_defaults_to_a_durable_backend(tmp_path, monkeypatch):
    """``bootstrap`` removes the silent default; it does not remove the choice."""
    from scripts.run_mock_case.env import bootstrap

    monkeypatch.delenv("EVIDENCE_BACKEND", raising=False)
    monkeypatch.setattr("scripts.run_mock_case.env.load_dotenv_file", lambda _p: None)
    bootstrap(tmp_path)

    assert __import__("os").environ["EVIDENCE_BACKEND"] == "minio"


def test_an_explicit_backend_choice_still_wins(tmp_path, monkeypatch):
    """An operator who set ``memory`` meant it; the deliverable declares it instead."""
    from scripts.run_mock_case.env import bootstrap

    monkeypatch.setenv("EVIDENCE_BACKEND", "memory")
    monkeypatch.setattr("scripts.run_mock_case.env.load_dotenv_file", lambda _p: None)
    bootstrap(tmp_path)

    assert __import__("os").environ["EVIDENCE_BACKEND"] == "memory"


def test_an_unusable_configured_backend_stops_the_run_before_it_spends_anything(monkeypatch,
                                                                               capsys):
    """Failing at the first artefact would cost minutes; failing here costs nothing."""
    from scripts.run_mock_case.evidence import preflight_evidence_backend

    def _raise() -> None:
        raise RuntimeError("MinIO at localhost:9000 is unusable")

    monkeypatch.setattr("aaa.platform.evidence.EvidenceStore", lambda *a, **k: _raise())
    assert preflight_evidence_backend() == 3
    assert "unusable" in capsys.readouterr().err


def test_a_volatile_backend_is_announced_but_not_fatal(monkeypatch, capsys):
    """The operator's call, made visible; the T18 withholds its signature anyway."""
    from scripts.run_mock_case.evidence import preflight_evidence_backend

    monkeypatch.setattr("aaa.platform.evidence.EvidenceStore",
                        lambda *a, **k: EvidenceStore(MemoryBackend()))
    assert preflight_evidence_backend() == 0
    assert "unresolvable" in capsys.readouterr().err


# --------------------------------------------------------------------------
# the report CLI asks the store rather than keeping its own copy of the rule
# --------------------------------------------------------------------------
def test_the_report_cli_declines_a_volatile_store(monkeypatch, capsys):
    """The case its own ``EVIDENCE_BACKEND`` read got wrong: env says minio, store is not.

    Reading the setting answered "was minio asked for?"; the figures depend on
    "does this store persist?", and only the second question is the store's.
    """
    from aaa.cli.cmd.report import store as report_store
    from aaa.settings import settings

    monkeypatch.setattr(settings, "evidence_backend", "minio", raising=False)
    monkeypatch.setattr("aaa.platform.evidence.EvidenceStore",
                        lambda *a, **k: EvidenceStore(MemoryBackend()))

    assert report_store.try_store() is None
    assert "does not persist across processes" in capsys.readouterr().err


def test_the_report_cli_returns_a_durable_store(monkeypatch):
    """A durable store is handed back so figures resolve."""
    from aaa.cli.cmd.report import store as report_store

    durable = EvidenceStore(MinioBackend(FakeMinio(), "b"))
    monkeypatch.setattr("aaa.platform.evidence.EvidenceStore", lambda *a, **k: durable)

    assert report_store.try_store() is durable
