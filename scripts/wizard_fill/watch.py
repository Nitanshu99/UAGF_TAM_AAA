"""Waiting for the results dashboard without letting a slow page end the audit.

The watcher read the page with Playwright's 30-second default and let a timeout
escape. On re-run 48afd4 Streamlit was busy rendering mid-audit, one read timed
out, and the exception unwound into the bootstrap's clean-up — which stopped the
API and UI and so killed the audit after 34 successful LLM calls, and closed the
browser the operator had asked to keep (T-20260913-023). An unanswered poll is
"not yet"; only the deadline or a closed page ends the wait.
"""
from __future__ import annotations

import time
from typing import Any

#: Text the results dashboard renders and the running screen does not.
RESULT_MARKERS = ("We found gaps", "Your documents")

#: Upper bound on one read of a busy page; the next poll simply tries again.
READ_TIMEOUT_MS = 10_000


def read_body(page: Any, timeout_ms: int = READ_TIMEOUT_MS) -> str | None:
    """The page's text, or ``None`` when it did not answer in time.

    :param page: The page to read.
    :param timeout_ms: How long this one read may take.
    """
    try:
        return page.locator("body").inner_text(timeout=timeout_ms)
    except Exception:  # noqa: BLE001 - Playwright's TimeoutError/Error: a busy page, not a failed run
        return None


def watch(page: Any, minutes: int = 60, poll_seconds: float = 15.0) -> bool:
    """Hold the browser open until the results dashboard renders.

    Sleeps with :func:`time.sleep`, not ``page.wait_for_timeout``: an interrupt
    landing inside a Playwright call leaves its event loop unusable (see
    ``hold_open``).

    :param page: The page the audit was started from.
    :param minutes: How long to wait before leaving the audit to finish server-side.
    :param poll_seconds: Pause between reads.
    :returns: ``True`` when the dashboard rendered; ``False`` on the deadline or a
        closed page. Never raises for a slow or unresponsive page.
    """
    deadline, misses = time.monotonic() + minutes * 60, 0
    while time.monotonic() < deadline:
        time.sleep(poll_seconds)
        body = read_body(page)
        if body is None:
            if page.is_closed():
                print("  the page was closed; the audit continues server-side.", flush=True)
                return False
            misses += 1
            print(f"  page busy ({misses} unanswered poll(s)); still waiting.", flush=True)
            continue
        misses = 0
        if any(marker in body for marker in RESULT_MARKERS):
            print("  results are on screen.", flush=True)
            return True
    print(f"  still running after {minutes} minutes; leaving it to finish server-side.")
    return False


__all__ = ["READ_TIMEOUT_MS", "RESULT_MARKERS", "read_body", "watch"]
