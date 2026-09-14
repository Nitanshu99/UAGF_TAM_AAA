"""The live report and completeness views the wizard polls while a run is in flight."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aaa.tools.intake_completeness_calculator import intake_completeness_calculator

if TYPE_CHECKING:
    from aaa.platform.state import ClientSubmission


def live_report(stage_a: dict, stage_b: dict):
    """Compute the live intake-completeness report for the review form.

    :param stage_a: Current Stage A payload.
    :param stage_b: Current Stage B payload.
    :returns: A ``CompletenessReport``, or ``None`` when it cannot be computed.
    """
    try:
        return intake_completeness_calculator(
            # Preview payloads are intentionally partial; the calculator treats
            # the submission as loosely-typed dicts at runtime.
            submission=cast("ClientSubmission",
                            {"stage_a": stage_a, "stage_b": stage_b, "stage_c": None,
                             "intake_completeness_score": 0.0}),
            declared_modality=str(stage_a.get("declared_modality") or ""),
            engagement_id="preview",
        )
    except Exception:  # noqa: BLE001 — preview must never crash the form
        return None
def live_completeness(stage_a: dict, stage_b: dict) -> float | None:
    """Compute the live intake-completeness preview score.

    :param stage_a: Current Stage A payload.
    :param stage_b: Current Stage B payload.
    :returns: Score in ``[0, 1]`` or ``None`` when it cannot be computed.
    """
    report = live_report(stage_a, stage_b)
    return None if report is None else float(report.score)


__all__ = ["live_completeness", "live_report"]
