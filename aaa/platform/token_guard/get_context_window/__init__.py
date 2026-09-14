"""Context-window resolution and the budget formula built on top of it.

Split from a single ``get_context_window.py`` that grew past the 50-executable-
line cap. ``window`` answers "how large is this model's input window"; ``budget``
turns that into an allowance and enforces it. Re-exported here so the historic
import path ``aaa.platform.token_guard.get_context_window`` keeps resolving for
:mod:`aaa.platform.token_guard` and :mod:`aaa.platform.token_guard.all`.
"""
from aaa.platform.token_guard.get_context_window.budget import (  # noqa: F401
    compute_budget,
    ensure_within_budget,
)
from aaa.platform.token_guard.get_context_window.window import (  # noqa: F401
    _declared_window,
    get_context_window,
)

__all__ = [
    '_declared_window',
    'get_context_window',
    'compute_budget',
    'ensure_within_budget',
]
