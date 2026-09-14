"""Engagement-level verdict vocabulary (finding F11).

The audit could say ``PASS``, ``PASS_WITH_OBSERVATIONS`` or ``FAIL`` and nothing
else, so an engagement that could not obtain the evidence to conclude had to
borrow one of the three. It borrowed ``PASS_WITH_OBSERVATIONS`` — a *qualified
pass* — while the same state carried ``auditor_opinion.opinion_type =
disclaimer_of_opinion``. The delivered report therefore asserted a pass and a
refusal to opine simultaneously, and ``final_verdict`` is the field that is
logged, persisted, returned by the API and printed on the PDF cover.

``DISCLAIMER_OF_OPINION`` is ISAE 3000's own term for that position: unable to
obtain sufficient appropriate evidence, therefore no conclusion is expressed.
It ranks *below* ``FAIL`` deliberately — a confirmed non-conformity is a
positive finding supported by evidence, so it outranks "we could not tell".

This is an **engagement-level** token only. Article verdicts keep their own
vocabulary (:data:`aaa.platform.state.findings.Verdict`), where the equivalent
position is ``INSUFFICIENT_EVIDENCE``.
"""
from __future__ import annotations

from typing import Final, Literal

FinalVerdict = Literal["PASS", "PASS_WITH_OBSERVATIONS", "FAIL",
                       "DISCLAIMER_OF_OPINION"]

PASS: Final = "PASS"
PASS_WITH_OBSERVATIONS: Final = "PASS_WITH_OBSERVATIONS"
FAIL: Final = "FAIL"
DISCLAIMER_OF_OPINION: Final = "DISCLAIMER_OF_OPINION"

#: Every legal value of ``state["final_verdict"]``.
FINAL_VERDICTS: Final[frozenset[str]] = frozenset({
    PASS, PASS_WITH_OBSERVATIONS, FAIL, DISCLAIMER_OF_OPINION})

#: Article verdicts that record a conclusion actually reached. KPI 2 counts an
#: article as covered only if its matrix verdict is one of these: an article
#: sitting at ``INSUFFICIENT_EVIDENCE`` is *in* the matrix but was not assessed,
#: and counting it read 80% coverage on an audit that assessed nothing (F13).
ASSESSED_ARTICLE_VERDICTS: Final[frozenset[str]] = frozenset({
    PASS, PASS_WITH_OBSERVATIONS, FAIL})

__all__ = ["FinalVerdict", "FINAL_VERDICTS", "ASSESSED_ARTICLE_VERDICTS",
           "PASS", "PASS_WITH_OBSERVATIONS", "FAIL", "DISCLAIMER_OF_OPINION"]
