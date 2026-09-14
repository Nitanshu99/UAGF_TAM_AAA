"""Recording that a call was recovered rather than delivered first time.

A retry that leaves no trace turns the audit trail into a worse record than the
one it replaces: every row would read ``status: "ok"`` and a reader could no
longer tell a provider that answered from a provider that had to be asked
twice.  Fix 39's acceptance criterion is exactly that distinction, so the
retry writes it down.

The channel is a context variable, following
:mod:`aaa.platform.phase_budget` and :mod:`aaa.observability.trace_context`:
the retry happens four frames below the audit writer, and threading a return
value back through ``flex_acompletion`` would change a signature every agent
calls.  There is no thread hop between the two — both run in the one coroutine
``BaseAgent.acompletion`` awaits — so the plain contextvar suffices here where
the phase deadline needed ``run_coro_blocking``'s context copy.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

#: Repr of each transient failure retried inside the current recording block.
_retried: ContextVar[list[str] | None] = ContextVar("transient_retried", default=None)
#: Each fallback model a call inside the block moved to (the last one answered).
_fallbacks: ContextVar[list[str] | None] = ContextVar("transient_fallbacks", default=None)


@contextmanager
def record_attempts() -> Iterator[list[str]]:
    """Collect the transient failures retried inside this block.

    :returns: A list, appended to by :func:`note_retry`, holding one ``repr``
        per swallowed transient failure. Empty means the call was delivered on
        its first attempt.
    :rtype: Iterator[list[str]]
    """
    retried: list[str] = []
    token, fallback_token = _retried.set(retried), _fallbacks.set([])
    try:
        yield retried
    finally:
        _retried.reset(token)
        _fallbacks.reset(fallback_token)


def note_retry(exc: BaseException) -> None:
    """Record that *exc* was swallowed and the call retried.

    A no-op when nothing is recording — a direct ``flex_acompletion`` call in a
    test still retries, it simply has no trail to write to.

    :param exc: The transient failure being retried past.
    :type exc: BaseException
    """
    retried = _retried.get()
    if retried is not None:
        retried.append(repr(exc))


def note_fallback(model: str) -> None:
    """Record that the call moved to *model* after its own retries were spent."""
    fallbacks = _fallbacks.get()
    if fallbacks is not None:
        fallbacks.append(model)


def served_model_so_far() -> str | None:
    """The fallback model that took over the current call, or ``None`` if none did."""
    fallbacks = _fallbacks.get()
    return fallbacks[-1] if fallbacks else None


def retried_so_far() -> list[str]:
    """The transient failures retried inside the current recording block.

    A reader, for a writer that did not open the block itself — the second audit
    writer records the same ``attempts`` field from the same source rather than
    taking a parameter it could be constructed without.

    :returns: A copy, empty when nothing is recording or nothing was retried.
    """
    return list(_retried.get() or [])


__all__ = ["record_attempts", "note_retry", "note_fallback", "retried_so_far",
           "served_model_so_far"]
