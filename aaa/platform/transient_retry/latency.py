"""What a successful attempt on each model has recently cost, for pricing its next attempt.

A fallback attempt was priced at the failed primary attempt's elapsed time. On the
free route that is the upstream's time-to-error — nemotron-3-ultra:free answered
"Service temporarily overloaded" after ~96 s — and says nothing about the fallback
model (T-20260913-082). Only successes are recorded: a fast failure is not what
the attempt costs when it delivers. With nothing measured, the caller keeps its
conservative estimate.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Deque

#: Recent successes kept per model; the estimate is their maximum.
WINDOW = 10

_lock = threading.Lock()
_by_model: dict[str, Deque[float]] = {}


def record_success(model: str, seconds: float) -> None:
    """Record one successful attempt's wall-clock on *model*."""
    if not model or seconds <= 0:
        return
    with _lock:
        _by_model.setdefault(model, deque(maxlen=WINDOW)).append(seconds)


def attempt_estimate(model: str | None) -> float | None:
    """The slowest recent successful attempt on *model*, or ``None`` when none is measured."""
    with _lock:
        seen = _by_model.get(model or "")
        return max(seen) if seen else None


def reset() -> None:
    """Forget every measurement. For tests."""
    with _lock:
        _by_model.clear()


__all__ = ["WINDOW", "attempt_estimate", "record_success", "reset"]
