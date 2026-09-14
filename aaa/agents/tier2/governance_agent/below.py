"""Whether a CGSA control misses a hard-constraint threshold it actually has."""
from __future__ import annotations


def _below(ctrl: dict) -> bool:
    """True when a control scores under a hard-constraint threshold it actually has.

    The schema leaves ``threshold_score`` null when no constraint applies; an
    assumed ``or 3`` judged such controls against a threshold that does not exist
    (T-20260913-078).
    """
    score = ctrl.get("maturity_score")
    constraint = ctrl.get("hard_constraint", {}) or {}
    threshold = constraint.get("threshold_score")
    return (constraint.get("applicable") is not False and isinstance(threshold, (int, float))
            and isinstance(score, (int, float)) and score < threshold)


def below_own_threshold(ctrl: dict) -> bool:
    """True when a control scores under the threshold it carries itself, constraint or not.

    ``controls_below_threshold`` counts every such control; :func:`_below` counts only
    hard-constraint breaches, so reconciling one against the other reported ten of an
    evaluated export's 36 below-threshold controls as unidentified although each
    states its score and threshold (T-20260914-059). A self-assessment export carries
    no control threshold, and its unscored controls stay unidentified.
    """
    score = ctrl.get("final_maturity_score", ctrl.get("maturity_score"))
    threshold = ctrl.get("threshold_score")
    return (isinstance(threshold, (int, float)) and isinstance(score, (int, float))
            and not isinstance(score, bool) and score < threshold)
