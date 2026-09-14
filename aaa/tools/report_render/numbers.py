"""Numbers as a reader should see them — finding Q15.

The delivered report carried six figures like ``diff=0.16352201257861637``
inside its compliance-matrix Basis column: a float's ``repr`` reaching a client
document through an f-string. Seventeen significant figures assert a precision
the measurement does not have, and they are unreadable besides.

Rounding at the *presentation* boundary rather than at the source is deliberate:
the stored artefacts keep full precision, because a later re-computation should
compare against what was actually measured. Only the rendering is shortened —
and ``shorten`` catches the case the typed formatter cannot, a number already
embedded in a sentence some agent composed.
"""
from __future__ import annotations

import re
from typing import Any

#: Decimal places for a rendered metric. Three separates 0.660 from 0.661 and
#: stops well short of implying the fourth is meaningful.
PLACES = 3

#: A decimal with more precision than any measurement here supports.
_LONG_DECIMAL = re.compile(r"(\d+\.\d{" + str(PLACES + 1) + r",})")


def fmt(value: Any, places: int = PLACES) -> str:
    """Render *value* for a reader, leaving non-numbers untouched.

    :param value: Any value; numbers are rounded, everything else is stringified.
    :param places: Decimal places.
    :returns: The display string, or ``"—"`` for ``None``.
    """
    if value is None:
        return "—"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, int):
        return str(value)
    # Fixed width, not stripped: a column reading 0.933 / 1 / 0.875 looks like
    # three different kinds of number, and 1 does not read as a measurement.
    return f"{value:.{places}f}"


def shorten(text: str, places: int = PLACES) -> str:
    """Round every over-precise decimal already embedded in *text*.

    Agent-composed descriptions interpolate raw floats, so the number reaches
    the renderer inside a sentence rather than as a value it can format.

    :param text: Prose that may contain long decimals.
    :param places: Decimal places to keep.
    :returns: The same prose with long decimals rounded.
    """
    return _LONG_DECIMAL.sub(
        lambda m: f"{float(m.group(1)):.{places}f}".rstrip("0").rstrip("."), text or "")


__all__ = ["PLACES", "fmt", "shorten"]
