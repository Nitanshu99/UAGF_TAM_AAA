"""Whether a run from this bundle would be comparable with the case's baseline."""
from __future__ import annotations

import pathlib

#: The document this case's runs are compared against.
CASE_DOC = ("local/assessments/run_2026-09-10/"
            "case_06_mariposa_edu_gmbh.md")


def preflight(case_dir: pathlib.Path) -> bool:
    """Report whether a run from this bundle would be comparable.

    :param case_dir: The intake bundle.
    :returns: ``False`` when a blocking check fails or the baseline cannot be read.
    """
    from aaa.tools.run_preflight import BaselineError, render
    from aaa.tools.run_preflight import preflight as run_preflight
    from scripts.wizard_fill.mariposa import load_case

    stage_a, stage_b = load_case(case_dir)
    try:
        reference, checks = run_preflight(CASE_DOC, stage_a, stage_b)
    except BaselineError as exc:
        print(f"preflight could not resolve the baseline: {exc}")
        return False
    print(render(reference, checks))
    return not any(c.blocking and not c.ok for c in checks)


__all__ = ["CASE_DOC", "preflight"]
