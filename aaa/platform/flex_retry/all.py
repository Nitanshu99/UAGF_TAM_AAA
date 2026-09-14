"""Part 3 of the former ``flex_retry`` module (auto-split)."""
from __future__ import annotations

from aaa.platform.flex_retry.flex_acompletion import flex_acompletion  # noqa: F401
from aaa.platform.flex_retry.logger import (  # noqa: F401
    DEFAULT_TIMEOUT_SECONDS,
    FLEX_BACKOFF_BASE,
    FLEX_MAX_RETRIES,
    FLEX_TIMEOUT_SECONDS,
    _is_rate_limit,
    _strip_flex,
    logger,
)

__all__ = [
    "flex_acompletion",
    "FLEX_TIMEOUT_SECONDS",
    "DEFAULT_TIMEOUT_SECONDS",
    "FLEX_MAX_RETRIES",
    "FLEX_BACKOFF_BASE",
]
