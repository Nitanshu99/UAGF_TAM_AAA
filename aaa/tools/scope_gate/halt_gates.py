"""Part 2 of the former ``scope_gate`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.scope_gate.scopeverdict import (  # noqa: F401
    _ART25_TRIGGERS,
    _FULL_EXCLUSIONS,
    _TERRITORIAL_NEXUS,
    ScopeGateResult,
    ScopeVerdict,
    _art25_flag,
    _art50_flag,
)


def _halt_gates(stage_a: dict[str, Any], reasoning: list[str]) -> "ScopeGateResult | None":
    """Evaluate the halting gates (Art. 5, Art. 2 exclusion, territorial nexus).

    :param stage_a: The Stage A payload.
    :param reasoning: Mutable reasoning log (appended in place).
    :returns: A halting :class:`ScopeGateResult`, or ``None`` when in scope.
    """
    # ── R3 — Art. 5 prohibitions (highest precedence; halts engagement) ──
    prohibited = [
        p for p in (stage_a.get("art5_prohibited_practices") or [])
        if p != "none"
    ]
    if prohibited:
        reasoning.append(
            f"Art. 5 prohibited practice declared ({', '.join(prohibited)}); "
            "engagement halted (FLI-R3)."
        )
        return ScopeGateResult(
            verdict="prohibited",
            reasoning=reasoning,
            halt_engagement=True,
            become_provider_under_art25=_art25_flag(stage_a),
            triggers_art50_transparency=_art50_flag(stage_a),
            is_gpai_systemic=bool(stage_a.get("gpai_systemic_risk")),
        )

    # ── R2 — Art. 2 full exclusions ──
    exclusion = stage_a.get("art2_exclusion")
    if exclusion in _FULL_EXCLUSIONS:
        reasoning.append(
            f"Art. 2 full exclusion declared ({exclusion}); system out of scope (FLI-R2)."
        )
        return ScopeGateResult(
            verdict="excluded",
            reasoning=reasoning,
            halt_engagement=True,
        )

    # ── S1 — territorial scope (Art. 2) ──
    territorial = stage_a.get("territorial_scope")
    if territorial is not None and not set(territorial) & _TERRITORIAL_NEXUS:
        reasoning.append(
            "No Art. 2 territorial nexus to the Union declared; system out of scope (FLI-S1)."
        )
        return ScopeGateResult(
            verdict="out_of_scope",
            reasoning=reasoning,
            halt_engagement=True,
        )
    return None
