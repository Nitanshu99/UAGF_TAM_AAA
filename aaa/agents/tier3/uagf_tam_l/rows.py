"""Normalise a client-supplied JSON evidence file into row dicts.

Clients do not export bare arrays. Case 04 happened to
(``[{question, answer, expected, …}, …]``) and parsed; case 06 ships the shape
an export tool actually produces —

    {"name": …, "version": …, "count": 55, "items": [ …55 rows… ]}

— and every one of its 55 rows was dropped, because the loader tested for a
``list`` and then for a DataFrame's ``.to_dict`` and gave up. The audit then
scored Art. 15 §1 on two hardcoded demo questions about the EU AI Act, reported
``pass_rate=0.0 from n=2``, and escalated. The customer's file was counted as
supplied and never read — the same class of defect as a placeholder artefact
behind a confident verdict.

Shared by the golden set and the trace sample, which had the identical blind
spot.
"""
from __future__ import annotations

from typing import Any, cast

#: Keys an export wrapper conventionally puts its rows under. Tried in order
#: before falling back to "the only list of objects in the file".
_WRAPPER_KEYS = ("items", "rows", "records", "data", "entries", "samples", "examples")


def unwrap_rows(content: Any) -> list[dict[str, Any]]:
    """Return the row dicts in *content*, whatever shape it arrived in.

    Handles a bare list, a pandas DataFrame, and a dict wrapper — either under
    a conventional key or, failing that, as the single list-of-objects value in
    the file.

    :param content: Parsed JSON, or an object exposing ``to_dict("records")``.
    :returns: Row dicts; empty when there are none to find.
    """
    if isinstance(content, list):
        return [row for row in content if isinstance(row, dict)]
    if isinstance(content, dict):
        for key in _WRAPPER_KEYS:
            value = content.get(key)
            if isinstance(value, list) and any(isinstance(r, dict) for r in value):
                return [row for row in value if isinstance(row, dict)]
        # No conventional key: accept an unambiguous single list of objects
        # rather than guessing between several.
        lists = [v for v in content.values()
                 if isinstance(v, list) and v and all(isinstance(r, dict) for r in v)]
        return lists[0] if len(lists) == 1 else []
    to_dict = getattr(content, "to_dict", None)
    if callable(to_dict):
        return cast("list[dict[str, Any]]", to_dict("records"))
    return []


def first_present(row: dict[str, Any], names: tuple[str, ...]) -> str:
    """The first non-empty value among *names*, as a string.

    :param row: One row of a client export.
    :param names: Field names to try, most specific first.
    :returns: The value, or ``""`` when none is present.
    """
    for name in names:
        value = row.get(name)
        if value:
            return str(value)
    return ""
