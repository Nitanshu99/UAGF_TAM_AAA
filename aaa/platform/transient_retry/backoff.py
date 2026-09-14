"""How many times a transient failure is retried, and how long each wait is."""
from __future__ import annotations

import random
from typing import Callable

#: Retries after the first attempt. One was set on the premise that "a provider
#: that fails twice in a row is not momentarily busy"; a shared free pool disproves
#: it — on 2026-09-13 the nemotron-3-ultra:free route recovered ten calls on the
#: second attempt, and the five it lost each failed instantly (0.0 s) twice two
#: seconds apart, costing a Verifier critique and a Phase 1 artefact. Four retries
#: with exponential backoff reach about half a minute of spacing.
MAX_TRANSIENT_RETRIES: int = 4

#: Base of the exponential backoff: the n-th retry waits within [b·2ⁿ/2, b·2ⁿ].
TRANSIENT_BACKOFF_SECONDS: float = 2.0
#: Ceiling of any single wait.
TRANSIENT_BACKOFF_CAP_SECONDS: float = 30.0

#: An upstream provider's rate limit gets its own, longer schedule. Its saturation
#: windows on 2026-09-14 lasted one to two minutes (11:30–11:32 and again near 11:45,
#: MiniMax M3 behind OpenRouter), and the transient schedule above gives up after about
#: 18 s. Eight retries from 5 s, each capped at 45 s, wait at least ~2 minutes and at
#: most ~4 in all; the phase budget still ends the ladder first when it is shorter.
MAX_RATE_LIMIT_RETRIES: int = 8
RATE_LIMIT_BACKOFF_SECONDS: float = 5.0
RATE_LIMIT_BACKOFF_CAP_SECONDS: float = 45.0


def backoff_seconds(retry: int, draw: Callable[[], float] = random.random,
                    rate_limited: bool = False) -> float:
    """The wait before retry *retry* (0-based): capped exponential backoff, equal jitter.

    Equal jitter keeps half of each exponential step as a floor, so an upstream that
    answers a 503 instantly still gets real time to recover, and spreads the other
    half so concurrent callers do not retry in lockstep ("Exponential Backoff and
    Jitter", AWS Architecture Blog, 2015; the pattern the OpenAI and Anthropic SDKs
    and Google Cloud's retry guidance use).

    :param retry: Which retry this is, from 0.
    :param draw: A uniform [0, 1) source; injectable for tests.
    :param rate_limited: Use the upstream rate-limit schedule.
    """
    base, cap = ((RATE_LIMIT_BACKOFF_SECONDS, RATE_LIMIT_BACKOFF_CAP_SECONDS) if rate_limited
                 else (TRANSIENT_BACKOFF_SECONDS, TRANSIENT_BACKOFF_CAP_SECONDS))
    step = min(cap, base * 2 ** retry)
    return step / 2 + draw() * step / 2
