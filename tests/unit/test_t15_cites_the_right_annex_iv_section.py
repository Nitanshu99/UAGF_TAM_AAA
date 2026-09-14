"""T15 cites the Annex IV section that holds each field it reads (T-20260913-073).

It said "Annex IV §7 logging capabilities" and "monitoring measures … §6"; the
intake mapping places both fields in §3 (§6 is lifecycle changes, §7 standards).
"""
from __future__ import annotations

import re

from aaa.agents.tier2.governance_agent.t15.grading.art12 import grade_art12
from aaa.tools.intake_completeness_calculator.section_weights import _SECTION_FIELDS


def _section_of(field: str) -> int:
    return next(n for n, fields in _SECTION_FIELDS.items() if field in fields)


def test_the_logging_grade_cites_the_logging_section() -> None:
    grade = grade_art12("", {})
    cited = {int(n) for n in re.findall(r"Annex IV\s*§(\d)", grade.rationale + " ".join(grade.observations))}
    assert cited == {_section_of("logging_capabilities")}


def test_the_monitoring_note_cites_the_monitoring_section() -> None:
    import inspect

    from aaa.agents.tier2.governance_agent import t15

    source = inspect.getsource(t15)
    note = re.search(r"No monitoring measures documented in Annex IV §(\d)", source)
    assert note and int(note.group(1)) == _section_of("monitoring_measures")
