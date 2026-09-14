"""Which phases a declaration can cause the plan to skip, and what each would have examined."""
from __future__ import annotations

#: Phase → (what it would have examined, the articles that go unevidenced).
_AT_STAKE: dict[str, tuple[str, tuple[str, ...]]] = {
    "P3": ("model validation — explainability and robustness",
           ("Art.15", "Art.13")),
    "P4": ("output fairness testing", ("Art.10§2(f)", "Art.15")),
}

#: Only a high-risk system earns this finding. At limited or minimal risk the
#: catalogue skips these phases by design, and saying so on every such run would
#: be noise that trains the reader to ignore the one case that matters.
_TIERS_AT_STAKE = frozenset({"high"})


def declaration_skipped_phases(state: dict) -> list[str]:
    """Phases the plan skipped that a discriminative component would have run.

    :param state: The AuditState dict.
    :returns: Sorted phase ids, or ``[]`` when none apply.
    """
    tier = state.get("risk_tier") or state.get("declared_risk_tier")
    if tier not in _TIERS_AT_STAKE:
        return []
    plan = state.get("phase_plan") or {}
    return sorted(p for p in _AT_STAKE if plan.get(p) == "S")


__all__ = ["_AT_STAKE", "_TIERS_AT_STAKE", "declaration_skipped_phases"]
