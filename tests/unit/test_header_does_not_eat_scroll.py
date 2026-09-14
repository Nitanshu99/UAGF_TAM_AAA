"""The page must scroll wherever the pointer is, including the top strip.

Streamlit pins its header as a transparent 60px band at ``z-index: 999990``,
outside ``stMain`` — which is the only scrollable element on the page, because
``stAppViewContainer`` is ``overflow: hidden``. A wheel anywhere in that strip
reaches an element whose ancestors are all ``overflow: hidden``, so it is
swallowed. The customer sees their own hero and stepper through the transparent
band, scrolls there, and nothing moves: reported as "unable to scroll
sometimes", the *sometimes* being wherever the pointer happened to land.

Nothing in the band is visible in this product — the toolbar, menu and status
widget are all hidden — so it is an empty overlay that only ever intercepts.
"""
from __future__ import annotations

import re

from aaa.ui.styles.css import STYLESHEET


def _rule(selector: str) -> str:
    """The declaration block for *selector*, or an empty string."""
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", STYLESHEET)
    return match.group(1) if match else ""


def test_the_header_does_not_intercept_the_wheel() -> None:
    """The exact regression: the band must be transparent to input."""
    assert "pointer-events: none" in _rule('.stApp [data-testid="stHeader"]')


def test_the_rule_outranks_streamlits_own() -> None:
    """A bare `[data-testid=…]` ties with the emotion rule and loses.

    The pre-existing `height: 0` in this same block is the proof: unprefixed it
    never applied, and the band stayed 60px tall.
    """
    assert '.stApp [data-testid="stHeader"]' in STYLESHEET
    assert not re.search(r'(?<!\.stApp )\[data-testid="stHeader"\]\s*\{', STYLESHEET)


def test_the_toolbar_keeps_its_clicks() -> None:
    """`pointer-events: none` inherits, so the toolbar must opt back in.

    It is hidden today, but a header that is un-hidden and unclickable would be
    a worse bug than the one being fixed.
    """
    assert "pointer-events: auto" in _rule(
        '.stApp [data-testid="stHeader"] [data-testid="stToolbar"]')


def test_nothing_else_pins_an_overlay_over_the_scroller() -> None:
    """No first-party rule may fix an element across the viewport.

    The header is Streamlit's; this guards against us adding our own. A fixed
    overlay outside `stMain` reproduces the same dead zone.
    """
    fixed = re.findall(r"([^{}]+)\{[^}]*position:\s*fixed[^}]*\}", STYLESHEET)
    offenders = [s.strip() for s in fixed
                 if "aaa-" in s and "pointer-events: none" not in _rule(s.strip())]
    assert not offenders, f"fixed overlays that could swallow the wheel: {offenders}"
