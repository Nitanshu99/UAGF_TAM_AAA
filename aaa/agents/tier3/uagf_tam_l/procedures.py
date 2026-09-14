"""What the L-branch performed, in audit-programme terms."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.uagf_tam_l.injection import _injection_result
from aaa.platform.audit_programme import outcome


def l_branch_outcomes(golden_set: dict[str, Any], injection: dict[str, Any]) -> dict[str, dict]:
    """Outcomes of the golden-set evaluation and the prompt-injection suite.

    :param golden_set: T16 ``golden_set_results``.
    :param injection: T16 ``prompt_injection_results``.
    """
    return {**outcome("golden_set_evaluation", bool(golden_set.get("scored")),
                      golden_set.get("unscored_reason")),
            **outcome("prompt_injection_suite", injection.get("vulnerability_rate") is not None,
                      _injection_result(injection))}


__all__ = ["l_branch_outcomes"]
