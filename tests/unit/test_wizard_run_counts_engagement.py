"""A wizard run counts towards ``aaa_engagements_total`` like an API run does."""
from __future__ import annotations

import pytest

from aaa.observability.metrics import ENGAGEMENT_COUNTER
from aaa.ui.wizard.step4 import persist as persist_mod


def _count(verdict: str) -> float:
    return ENGAGEMENT_COUNTER.labels(status="completed", final_verdict=verdict)._value.get()  # noqa: SLF001


def test_persist_increments_the_engagement_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(persist_mod, "save_result", lambda eid, final: None)
    monkeypatch.setattr(persist_mod, "save_customer_artefacts", lambda eid, final, store: None)
    before = _count("FAIL")
    persist_mod._persist("eng-test", {"final_verdict": "FAIL"}, store=object())
    assert _count("FAIL") == before + 1


def test_a_failed_write_is_not_counted_as_a_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(eid, final):
        raise OSError("disk full")

    monkeypatch.setattr(persist_mod, "save_result", boom)
    monkeypatch.setattr(persist_mod, "st", type("S", (), {"warning": staticmethod(lambda *a, **k: None)})())
    before = _count("PASS")
    persist_mod._persist("eng-test", {"final_verdict": "PASS"}, store=object())
    assert _count("PASS") == before
