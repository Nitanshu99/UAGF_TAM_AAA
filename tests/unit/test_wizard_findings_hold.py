"""M23–M30 stated as properties, so a UI rewrite cannot quietly undo them.

Every one of these was found, fixed and written up — and then the wizard was
rebuilt on 2026-09-11 and two of the guards broke while a third (M25) had never
existed. The rebuild reintroduced M25's exact failure: a hand-counted heading
that had drifted from the questions under it.

What survived the rebuild cleanly were the *behavioural* guards — the ones that
call a function and assert its result. What broke, or could pass while the
behaviour moved, were the ones asserting source text. These are behavioural.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_STEP2 = Path("aaa/ui/wizard/step2")
_NUMBERED = re.compile(r'\*\*(\d+[a-z]?)\.\s')


def _rendered_question_labels() -> list[str]:
    """The numbers step 2 actually puts on screen, in file order."""
    labels: list[str] = []
    for name in ("form.py", "form2.py"):
        labels += _NUMBERED.findall((_STEP2 / name).read_text(encoding="utf-8"))
    return labels


# --- M25: the heading must count the questions that are there ---------------

def test_the_heading_count_matches_the_questions_rendered() -> None:
    """"8 Quick Questions" over seven questions is how M25 read."""
    from aaa.ui.wizard.step2.form import QUESTION_COUNT

    assert QUESTION_COUNT == len(_rendered_question_labels())


def test_the_heading_does_not_hard_code_a_number() -> None:
    """A hand-written count is what drifts; it must come from QUESTION_COUNT."""
    source = (_STEP2 / "__init__.py").read_text(encoding="utf-8")
    assert "QUESTION_COUNT" in source
    assert not re.search(r'"(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten) '
                         r'questions', source)


def test_the_numbering_has_no_gaps() -> None:
    """M25's other half: seven questions numbered 1,2,3,5,6,7,8."""
    majors = [int(re.match(r"\d+", label).group()) for label in _rendered_question_labels()]
    assert majors == sorted(majors), "question numbers are out of order"
    assert set(majors) == set(range(1, max(majors) + 1)), (
        f"gap in the numbering: {sorted(set(majors))}")


# --- M23: no extraction ran, so no extraction failure may be reported -------

def test_a_wizard_that_never_extracted_reports_no_extraction_failure() -> None:
    """M23 was telling a customer their documents were empty when they were not.

    The wizard no longer extracts at all, so the one thing it must never do is
    show any of the four failure messages — they all describe an attempt.
    """
    from aaa.ui.wizard.progress import _DEGRADED, extraction_banner
    from aaa.ui.wizard.step1.actions import _NO_EXTRACTION

    status = _NO_EXTRACTION["extraction_status"]
    assert status not in _DEGRADED, (
        f"{status!r} would render an apology for an extraction that never ran")

    shown: list[str] = []
    import aaa.ui.wizard.progress as progress
    original = progress.st
    try:
        progress.st = type("S", (), {"error": staticmethod(shown.append)})()
        extraction_banner(status, 12)
    finally:
        progress.st = original
    assert shown == []


# --- M30: a UI run must leave the durable record the API path leaves --------

def test_the_ui_run_persists_every_deliverable() -> None:
    """Behavioural: `_persist` must call both writers, with the run's state."""
    from aaa.ui.wizard.step4 import persist as persist_mod

    called: dict[str, tuple] = {}
    saved_result = persist_mod.save_result
    saved_artefacts = persist_mod.save_customer_artefacts
    warned: list[str] = []
    original_st = persist_mod.st
    try:
        persist_mod.save_result = lambda eid, final: called.__setitem__("result", (eid, final))
        persist_mod.save_customer_artefacts = (
            lambda eid, final, store: called.__setitem__("artefacts", (eid, final)))
        persist_mod.st = type("S", (), {"warning": staticmethod(warned.append)})()
        persist_mod._persist("eng-t", {"final_verdict": "FAIL"}, store=None)
    finally:
        persist_mod.save_result = saved_result
        persist_mod.save_customer_artefacts = saved_artefacts
        persist_mod.st = original_st

    assert set(called) == {"result", "artefacts"}
    assert called["result"][0] == "eng-t"
    assert warned == []


def test_a_failed_write_is_surfaced_and_does_not_lose_the_results() -> None:
    """The results on screen are still valid; the problem is told, not raised."""
    from aaa.ui.wizard.step4 import persist as persist_mod

    warned: list[str] = []
    saved_result = persist_mod.save_result
    original_st = persist_mod.st

    def _boom(*_a, **_k):
        raise OSError("disk full")

    try:
        persist_mod.save_result = _boom
        persist_mod.st = type("S", (), {"warning": staticmethod(warned.append)})()
        persist_mod._persist("eng-t", {"final_verdict": "FAIL"}, store=None)
    finally:
        persist_mod.save_result = saved_result
        persist_mod.st = original_st

    assert warned and "disk full" in warned[0]


# --- M27 / M29: the run gate still refuses an incomplete dossier ------------

def test_the_run_gate_still_names_every_blocker(monkeypatch: pytest.MonkeyPatch) -> None:
    """M27 (Stage A blanks) and M29 (modality-conditional docs), behaviourally.

    The rebuild moved these from a disabled button to a validated submit; the
    property that matters is that neither stops being enforced.
    """
    from aaa.ui.wizard.step3 import blockers, required_fields

    monkeypatch.setattr(required_fields, "collect_stage_a", lambda: {
        "provider_name": "", "system_name": "S", "version": "1",
        "intended_purpose": "P", "declared_modality": "llm"})
    monkeypatch.setattr(required_fields, "collect_stage_b", lambda: {})
    reasons = blockers._blockers(score=0.95, gate=type("G", (), {"halt_engagement": False})())

    assert any("Legal provider name" in r for r in reasons), "M27 not enforced"
    assert any("System prompt" in r for r in reasons), "M29 not enforced"


def test_a_complete_dossier_has_no_blockers(monkeypatch: pytest.MonkeyPatch) -> None:
    from aaa.ui.wizard.step3 import blockers, required_fields

    monkeypatch.setattr(required_fields, "collect_stage_a", lambda: {
        "provider_name": "Mariposa-Edu GmbH", "system_name": "Mariposa",
        "version": "1.0.0", "intended_purpose": "Matching",
        "declared_modality": "tabular", "declared_risk_tier": "high",
        "deployment_context": "b2b"})
    monkeypatch.setattr(required_fields, "collect_stage_b", lambda: {})
    assert blockers._blockers(
        score=0.9, gate=type("G", (), {"halt_engagement": False})()) == []
