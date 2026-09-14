"""Grading Art. 72 from the essential elements of post-market monitoring."""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15.grading.elements import ELEMENT_NAMES
from aaa.agents.tier2.governance_agent.t15.grading.grade import Grade
from aaa.agents.tier2.governance_agent.t15.grading.states import Found, essential_states, quote_for

_MAJOR = ("absent", "not_shown_operating")
_READ = {"operating": "operating", "documented": "documented", "not_evidenced": "not evidenced",
         "not_shown_operating": "not shown operating — the provider declares its monitoring "
                                "largely unbuilt", "absent": "declared absent"}


def _line(found: Found, element: str, state: str) -> str:
    evidence = quote_for(found, element) if state in ("absent", "operating") else None
    return f"{ELEMENT_NAMES[element]}: {_READ[state]}" + (f" — {evidence.cite()}" if evidence else "")


def grade_art72(plan_present: bool, found: Found) -> Grade:
    """FAIL on a missing plan or a missing essential element; PASS when all are established.

    :param plan_present: A plan URI or documented monitoring measures exist.
    :param found: Grounded answers to the T15 questions.
    """
    if not plan_present:
        return Grade("FAIL", "Major nonconformity: no post-market monitoring plan or measures "
                             "documented (Annex IV §9, Art. 72(3)).",
                     ["No post-market monitoring plan URI in Annex IV §9."])
    states = essential_states(found)
    lines = [_line(found, element, state) for element, state in states.items()]
    major = [ELEMENT_NAMES[e] for e, s in states.items() if s in _MAJOR]
    if major:
        return Grade("FAIL", "Major nonconformity — required monitoring elements not in place: "
                             f"{'; '.join(major)}. Elements: {' | '.join(lines)}",
                     [f"Art. 72: {line}" for e, line in zip(states, lines) if states[e] in _MAJOR])
    if all(s in ("operating", "documented") for s in states.values()):
        return Grade("PASS", f"Every essential monitoring element is evidenced. Elements: {' | '.join(lines)}")
    missing = [ELEMENT_NAMES[e] for e, s in states.items() if s == "not_evidenced"]
    return Grade("PASS_WITH_OBSERVATIONS",
                 f"Minor nonconformity — not evidenced in the documents: {'; '.join(missing)}. "
                 f"Elements: {' | '.join(lines)}",
                 [f"Art. 72: {name} not evidenced in the provider's documents." for name in missing])


__all__ = ["grade_art72"]
