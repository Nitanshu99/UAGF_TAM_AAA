"""limiter.py — asyncio-safe fixed-window rate limiter.

Implements exactly NVIDIA build.nvidia.com's free-tier shape: 40 requests
per rolling-reset 60s window. Strategy: record the window's start time and
a request count; once the count reaches the cap, check how much of the
window has actually elapsed — if the window isn't over yet, sleep the
remainder, then start a fresh window and let the caller through.
"""
from __future__ import annotations

import asyncio
import time
from typing import Callable

MAX_REQUESTS_PER_WINDOW: int = 40
WINDOW_SECONDS: float = 60.0


class FixedWindowLimiter:
    """Blocks the caller once ``max_requests`` is hit inside one window.

    :param max_requests: Requests allowed per window.
    :type max_requests: int
    :param window_seconds: Window length in seconds.
    :type window_seconds: float
    :param clock: Monotonic time source; injectable so tests can supply a
        deterministic clock instead of patching the real ``time`` module
        (which the asyncio event loop also relies on internally).
    :type clock: Callable[[], float]
    """

    def __init__(self, max_requests: int = MAX_REQUESTS_PER_WINDOW,
                 window_seconds: float = WINDOW_SECONDS,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._window_start = clock()
        self._count = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Register one request, waiting out the window if the cap is hit.

        :returns: None
        """
        async with self._lock:
            self._count += 1
            if self._count < self._max_requests:
                return
            elapsed = self._clock() - self._window_start
            remaining = self._window_seconds - elapsed
            if remaining > 0:
                await asyncio.sleep(remaining)
            self._window_start = self._clock()
            self._count = 0
