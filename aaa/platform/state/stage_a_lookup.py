"""Read a Stage A declaration field whatever shape the caller holds.

The declaration reaches different consumers in three different shapes, and a
lookup written against one of them silently returns nothing for the other two:

* the audit state nests it at ``client_submission.stage_a``;
* the Phase 6 declaration summary carries it at ``stage_a``;
* some nodes mirror individual fields onto the top level.

Three separate defects on the Mariposa engagement traced to that split. The
composite phase plan fell back to the scalar modality and skipped Phases 3 and
4; the GPAI obligations stayed in scope for a provider that had declared it
places no GPAI model on the market. In both cases the declaration was present
and correct — the reader was looking in the wrong place.
"""
from __future__ import annotations

from typing import Any, Mapping

_SENTINEL = object()


def stage_a_field(state: Mapping[str, Any], name: str, default: Any = None) -> Any:
    """Return Stage A field *name* from whichever shape *state* carries.

    Lookup order is most-specific first: an explicit top-level mirror wins, then
    the declaration summary's ``stage_a``, then the audit state's
    ``client_submission.stage_a``.

    :param state: Audit state, declaration summary, or Stage A mapping.
    :param name: Stage A field name, e.g. ``"gpai_general_purpose"``.
    :param default: Returned when no shape carries the field.
    :returns: The declared value, or *default*.
    :rtype: Any
    """
    found = state.get(name, _SENTINEL)
    if found is not _SENTINEL and found is not None:
        return found
    for holder in (state.get("stage_a"),
                   (state.get("client_submission") or {}).get("stage_a")
                   if isinstance(state.get("client_submission"), Mapping) else None):
        if isinstance(holder, Mapping):
            found = holder.get(name, _SENTINEL)
            if found is not _SENTINEL and found is not None:
                return found
    return default
