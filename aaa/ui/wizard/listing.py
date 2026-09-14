"""Splitting a comma-separated form field without breaking what is inside brackets."""
from __future__ import annotations


def split_items(text: str) -> list[str]:
    """Top-level comma-separated items; a comma inside ``()``, ``[]`` or ``{}`` stays in its item.

    The standards fields split on every comma, so a declared "ISO/IEC 42001:2023
    (guidance, uncertified)" reached the dossier as two standards, the second
    "uncertified)" (live run 8a23f5).

    :param text: The field's raw text.
    :returns: The stripped, non-empty items, in order.
    """
    items, current, depth = [], [], 0
    for char in text or "":
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            items.append("".join(current))
            current = []
        else:
            current.append(char)
    items.append("".join(current))
    return [item.strip() for item in items if item.strip()]


__all__ = ["split_items"]
