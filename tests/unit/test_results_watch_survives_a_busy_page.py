"""A slow page read must not end the audit it is watching.

Re-run 48afd4: one 30-second read timeout escaped the watcher, unwound into the
bootstrap's clean-up, stopped the API and UI mid-audit and closed the browser
(T-20260913-023).
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from scripts.wizard_fill import watch as watch_mod


class _Page:
    """Answers with the queued bodies; ``None`` means the read timed out."""

    def __init__(self, bodies: list[str | None], closed: bool = False) -> None:
        self.bodies, self.closed = list(bodies), closed

    def locator(self, _selector: str) -> Any:
        """The body element, whose read may time out."""
        body = self.bodies.pop(0) if self.bodies else "still running"

        def inner_text(timeout: int) -> str:
            assert timeout == watch_mod.READ_TIMEOUT_MS
            if body is None:
                raise TimeoutError("Locator.inner_text: Timeout exceeded")
            return body
        return SimpleNamespace(inner_text=inner_text)

    def is_closed(self) -> bool:
        """Whether the window was closed."""
        return self.closed


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(watch_mod.time, "sleep", lambda _s: None)


def test_unanswered_polls_are_not_yet() -> None:
    """Three timed-out reads, then the dashboard: the watch still succeeds."""
    page = _Page([None, None, None, "running", "We found gaps in 4 areas"])
    assert watch_mod.watch(page, minutes=1) is True


def test_a_closed_page_ends_the_watch_without_raising() -> None:
    """The operator closed the window; the audit is not the watcher's to stop."""
    assert watch_mod.watch(_Page([None], closed=True), minutes=1) is False


def test_the_deadline_ends_the_watch_without_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    """Out of time: report and leave the audit to finish server-side."""
    ticks = iter([0.0, 30.0, 120.0])
    monkeypatch.setattr(watch_mod.time, "monotonic", lambda: next(ticks))
    assert watch_mod.watch(_Page([None, None]), minutes=1) is False
