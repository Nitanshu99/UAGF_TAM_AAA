"""Nonconformity grading for T15's Art. 12 and Art. 72 statuses.

A declared gap used to cap an article at PASS_WITH_OBSERVATIONS whatever it was, so a
monitoring plan that calls itself "the specification for the monitoring required,
not a description of monitoring already in place" graded the same as one missing a
dashboard (live run bb7837; the Verifier rated it an understatement). Findings are
now graded the way conformity assessment grades them (ISO/IEC 17021-1 §3.12–3.13,
ISO 19011): a required element absent, or not shown operating, is a *major*
nonconformity → FAIL; a partial lapse is *minor* → PASS_WITH_OBSERVATIONS; every
element evidenced → PASS. The grade is computed from the quoted provider statements,
so it is reproducible; the Verifier reviews it and does not decide it.
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15.grading.art12 import grade_art12
from aaa.agents.tier2.governance_agent.t15.grading.art72 import grade_art72
from aaa.agents.tier2.governance_agent.t15.grading.elements import element_questions
from aaa.agents.tier2.governance_agent.t15.grading.grade import Grade

__all__ = ["Grade", "element_questions", "grade_art12", "grade_art72"]
