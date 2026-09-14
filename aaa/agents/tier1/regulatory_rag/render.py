"""Rendering one retrieved passage as citable text."""
from __future__ import annotations

from typing import Any


def render_hit(hit: dict[str, Any]) -> str:
    """Render one hit with the pinpoint that makes it citable.

    :param hit: A ``search`` result.
    :type hit: dict[str, Any]
    :returns: ``"EU AI Act Article 10 [euaiact://Article_10]: <text>"``.
    :rtype: str
    """
    source = str(hit.get("source") or hit.get("article") or "").strip()
    locator = str(hit.get("locator") or hit.get("source_uri") or "").strip()
    head = f"{source} [{locator}]" if source and locator else source or locator
    text = str(hit.get("text") or "").strip()
    return f"{head}: {text}" if head else text


__all__ = ["render_hit"]
