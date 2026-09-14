"""Grading Art. 12 record-keeping from the logging declaration and any declared gap."""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15.grading.grade import Grade
from aaa.agents.tier2.governance_agent.t15.grading.states import Found
from aaa.tools.term_match import match_term

#: A gap in recording what the system output makes risk situations unreconstructable
#: (Art. 12(2)(a)–(c)); a gap elsewhere in the logs is partial.
_OUTPUT_EVENTS = ("inference*", "output*", "prediction*", "recommendation*", "decision*",
                  "surfaced", "rank*", "score*")


def grade_art12(logging_text: str, found: Found) -> Grade:
    """FAIL with no logging or an output-event gap; PASS_WITH_OBSERVATIONS for other gaps or no retention.

    A declared gap was the only minor finding, so a provider that documented neither
    a retention period nor integrity controls graded PASS with "no logging gap
    declared" (case 03, 2026-09-13; T-20260913-072).

    :param logging_text: The declared Annex IV logging capabilities.
    :param found: Grounded answers to the T15 questions.
    """
    if not logging_text:
        return Grade("FAIL", "Major nonconformity: no logging capabilities documented in Annex IV "
                             "§3; Art. 12(1) requires automatic recording of events.",
                     ["No logging capabilities documented in Annex IV §3."])
    gap = found.get("logging_gap")
    if gap is not None and any(match_term(term, gap.quote.lower()) for term in _OUTPUT_EVENTS):
        return Grade("FAIL", "Major nonconformity — the provider declares that the system's outputs "
                             "are not recorded, so situations presenting a risk cannot be "
                             f"reconstructed (Art. 12(2)): {gap.cite()}",
                     [f"Art. 12: output events not logged — {gap.cite()}"])
    minor = [f"declared logging gap — {gap.cite()}"] if gap is not None else []
    if found.get("log_retention") is None:
        minor.append("no log retention period evidenced; Art. 19(1) requires automatically "
                     "generated logs to be kept for at least six months")
    integrity = ("" if found.get("log_integrity") is not None
                 else " No log integrity (tamper-evidence) control is documented.")
    if not minor:
        return Grade("PASS", "Annex IV §3 logging capabilities documented, with a retention period "
                             "and no declared logging gap." + integrity)
    return Grade("PASS_WITH_OBSERVATIONS",
                 "Minor nonconformity — logging documented, but " + "; ".join(minor) + "." + integrity,
                 [f"Art. 12: {item}" for item in minor])


__all__ = ["grade_art12"]
