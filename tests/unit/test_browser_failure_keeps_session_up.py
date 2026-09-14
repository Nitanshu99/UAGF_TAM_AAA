"""A failure in the browser driver does not stop the stack that runs the audit.

Headed sessions report and stay open, as the operator asked; headless runs (CI)
still fail loudly (T-20260913-023).
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from scripts.bootstrap.browser import session


def _args(headless: bool) -> Any:
    return SimpleNamespace(headless=headless, no_run=False, watch_minutes=1, screenshots=None)


def _boom(*_a: Any, **_k: Any) -> None:
    raise TimeoutError("Locator.inner_text: Timeout 30000ms exceeded")


def test_a_headed_session_reports_and_returns(monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    """No exception reaches main's clean-up, so the API and UI stay up."""
    monkeypatch.setattr(session, "drive_wizard", _boom)
    session.drive_or_report(object(), "http://ui", None, _args(headless=False))  # type: ignore[arg-type]
    assert "the audit continues server-side" in capsys.readouterr().out


def test_a_headless_run_still_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """CI has no window to keep; the failure must be visible."""
    monkeypatch.setattr(session, "drive_wizard", _boom)
    with pytest.raises(TimeoutError):
        session.drive_or_report(object(), "http://ui", None, _args(headless=True))  # type: ignore[arg-type]
