"""Which protected attributes divide the same rows into the same groups.

An evaluation set can record one attribute identically to
``nationality`` — every German national was educated in Germany, and so on for all
ten countries — so the two attributes' label rates, ratios and intervals are the same
numbers. The Verifier, seeing them repeated, escalated T07 as a copying defect
(MiniMax run, 2026-09-14). The repetition is a fact about the data, and the artefact
now states it.
"""
from __future__ import annotations

from typing import Any, Sequence


def _partition(index: Sequence[Any], labels: Sequence[str]) -> frozenset[frozenset[Any]]:
    """The groups as sets of row ids, independent of what each group is called."""
    groups: dict[str, set[Any]] = {}
    for row, label in zip(index, labels):
        groups.setdefault(label, set()).add(row)
    return frozenset(frozenset(rows) for rows in groups.values())


def same_groupings(grouped: dict[str, tuple[Sequence[Any], Sequence[str]]]) -> dict[str, str]:
    """Map each attribute to the first earlier one that splits the same rows identically.

    :param grouped: ``{attribute: (row ids, group label per row)}`` in examination order.
    :returns: ``{attribute: earlier attribute}`` for each repeat; attributes with a
        grouping of their own are absent.
    """
    seen: list[tuple[str, frozenset[frozenset[Any]]]] = []
    repeats: dict[str, str] = {}
    for attribute, (index, labels) in grouped.items():
        partition = _partition(index, labels)
        match = next((name for name, earlier in seen if earlier == partition), None)
        if match is None:
            seen.append((attribute, partition))
        else:
            repeats[attribute] = match
    return repeats


__all__ = ["same_groupings"]
