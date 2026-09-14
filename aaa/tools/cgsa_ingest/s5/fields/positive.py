"""The S5 hand-off's positive findings, stated from the controls that meet their threshold.

The contract defines ``positive_findings`` as the controls that meet or exceed their
threshold. The S5 adapter ships the list empty while its own scores show such
controls meeting their threshold — so T14
reported no strength at all beside ``controls_meeting_threshold: 2`` and the Verifier
flagged the omission (T-20260914-058). Nothing is added that the payload does not state.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.s5.fields.controls import control_summary


def _meets(control: dict[str, Any]) -> bool:
    """Whether a control's final score reaches the threshold it carries."""
    score, threshold = control.get("final_maturity_score"), control.get("threshold_score")
    return (isinstance(score, (int, float)) and isinstance(threshold, (int, float))
            and not isinstance(score, bool) and score >= threshold)


def positive_findings(controls: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """One contract positive finding per control that meets its threshold.

    :param controls: Scored controls by id.
    :returns: ``{control_id, control_name, maturity_score, finding}`` rows, in id order.
    """
    return [{"control_id": cid, "control_name": str(c.get("control_name") or cid),
             "maturity_score": int(c["final_maturity_score"]),
             "finding": control_summary(c) or ""}
            for cid, c in sorted(controls.items()) if _meets(c)]


__all__ = ["positive_findings"]
