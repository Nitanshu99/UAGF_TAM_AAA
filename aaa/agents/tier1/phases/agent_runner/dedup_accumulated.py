"""De-duplicating the lists a re-dispatched phase emits again."""
from __future__ import annotations

import json
from typing import Any

_FINDING_FIELDS = ("finding_id", "description", "source_phase")

#: What identifies an item, per accumulator. Findings key on their id, text and
#: phase. Roadmap rows carry none of those: keyed like findings, every row shared
#: the key ``(None, None, None)`` and 36 CGSA rows collapsed to one in state — the
#: list T18, the PDF, the client brief and the results writer read (T-20260913-030).
_IDENTITY_FIELDS: dict[str, tuple[str, ...]] = {
    "remediation_roadmap": ("control_id", "rank"),
}


def _identity(item: Any, fields: tuple[str, ...]) -> Any:
    """The de-duplication key for *item*.

    A dict whose identifying fields are all absent is keyed by its whole content,
    so it can only ever match an identical dict — never an unrelated one.
    """
    if not isinstance(item, dict):
        return item
    key = tuple(item.get(field) for field in fields)
    if any(part is not None for part in key):
        return key
    return json.dumps(item, sort_keys=True, default=str)


def _dedup_accumulated(items: list, accumulator: str = "") -> list:
    """De-duplicate an accumulator list, preserving first-seen order.

    A phase that the Verifier sends back for ``rerun`` is re-dispatched and emits its
    delta again; without this, identical findings accumulate (e.g. the same
    P5-CGSA-COUNT three times after two reruns).

    :param items: Existing entries followed by the delta's.
    :param accumulator: The state key being merged, which selects the identity
        fields; findings' fields when it has none of its own.
    :returns: The list with later duplicates removed.
    """
    fields = _IDENTITY_FIELDS.get(accumulator, _FINDING_FIELDS)
    seen: set = set()
    out: list = []
    for item in items:
        key = _identity(item, fields)
        try:
            if key in seen:
                continue
            seen.add(key)
        except TypeError:  # unhashable payload — fall back to repr identity
            key = repr(item)
            if key in seen:
                continue
            seen.add(key)
        out.append(item)
    return out


__all__ = ["_dedup_accumulated"]
