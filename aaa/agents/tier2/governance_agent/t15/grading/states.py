"""The state of each essential monitoring element, from grounded document answers."""
from __future__ import annotations

from typing import Mapping

from aaa.tools.document_evidence import Evidence

Found = Mapping[str, Evidence | None]

#: How sources combine into one element: any positive evidence establishes it, and
#: otherwise a statement of absence outweighs silence — an unmentioned drift monitor
#: cannot rescue a performance review the provider says is not operational.
RANK = ("operating", "documented", "absent", "not_shown_operating", "not_evidenced")


def element_state(found: Found, key: str) -> str:
    """``operating``, ``absent``, ``not_shown_operating``, ``documented`` or ``not_evidenced``.

    Where the provider declares its monitoring largely unbuilt, a merely documented
    element is not shown operating — the plan is a specification, not the system.
    """
    if found.get(f"{key}_operating"):
        return "operating"
    if found.get(f"{key}_absent"):
        return "absent"
    if found.get("monitoring_gap"):
        return "not_shown_operating"
    return "documented" if found.get(key) else "not_evidenced"


#: Essential element → the question keys whose evidence can establish it (best one counts).
SOURCES = {"performance": ("accuracy", "drift"), "fairness": ("fairness",),
           "field_data": ("field_data", "complaints"),
           "incidents": ("incidents", "incident_reporting", "incident_threshold")}


def essential_states(found: Found) -> dict[str, str]:
    """The four essential elements' states, each the best state any of its sources shows.

    An incident process is established by being documented: it acts on events, so no
    "operating" statement is expected of it before one occurs.
    """
    states = {element: min((element_state(found, key) for key in keys), key=RANK.index)
              for element, keys in SOURCES.items()}
    if states["incidents"] == "not_shown_operating" and any(
            found.get(k) for k in SOURCES["incidents"]):
        states["incidents"] = "documented"
    return states


def quote_for(found: Found, element: str) -> Evidence | None:
    """The passage behind an element's absence or operation, for the rationale."""
    for suffix in ("_absent", "_operating", ""):
        for key in SOURCES[element]:
            if found.get(f"{key}{suffix}"):
                return found[f"{key}{suffix}"]
    return None


__all__ = ["RANK", "SOURCES", "element_state", "essential_states", "quote_for"]
