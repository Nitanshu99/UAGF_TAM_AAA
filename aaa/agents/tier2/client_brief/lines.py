"""Coerce whatever the model returned into Markdown lines.

A prose key is asked for as a list of points, and comes back as a list, a
paragraph, or a list of little objects depending on the reply. Rendering has to
survive all three without dropping content, so normalisation happens once here
rather than at each of the renderer's call sites.
"""
from __future__ import annotations

from typing import Any


def as_lines(value: Any) -> list[str]:
    """Return *value* as a list of non-empty single-line strings.

    :param value: A string, a sequence, a mapping, or ``None``.
    :returns: Renderable lines; empty when there is nothing to say.
    """
    if value is None or value == "" or value == [] or value == {}:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, dict):
        return [f"**{key}** — {' '.join(as_lines(item))}"
                for key, item in value.items() if as_lines(item)]
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            out.extend(as_lines(item))
        return out
    return [str(value)]


def bullets(value: Any) -> str:
    """Render *value* as a Markdown bullet list, or ``""`` when empty."""
    return "\n".join(f"- {line}" for line in as_lines(value))


def paragraph(value: Any) -> str:
    """Render *value* as prose, joining multiple points into one block."""
    return "\n\n".join(as_lines(value))
