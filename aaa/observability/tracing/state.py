"""Process-wide latch: has :func:`configure_llm_tracing` switched tracing on?

Kept apart from the package root so :mod:`~aaa.observability.tracing.flush`
can read it without importing the package that imports it.
"""
from __future__ import annotations

_CONFIGURED = False


def is_llm_tracing_configured() -> bool:
    """Return whether tracing was configured in this process.

    :returns: ``True`` after a successful :func:`configure_llm_tracing`.
    :rtype: bool
    """
    return _CONFIGURED


def set_llm_tracing_configured(value: bool) -> None:
    """Set the latch (``True`` on configure, ``False`` from the test reset).

    :param value: New latch value.
    :type value: bool
    """
    global _CONFIGURED  # pylint: disable=global-statement
    _CONFIGURED = value
