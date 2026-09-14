"""Part 3 of the former ``scope_gate`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.scope_gate.fria import fria_reason
from aaa.tools.scope_gate.halt_gates import _halt_gates  # noqa: F401
from aaa.tools.scope_gate.scopeverdict import (  # noqa: F401
    _ART25_TRIGGERS,
    _FULL_EXCLUSIONS,
    _TERRITORIAL_NEXUS,
    ScopeGateResult,
    ScopeVerdict,
    _art25_flag,
    _art50_flag,
)


def scope_gate(stage_a: dict[str, Any]) -> ScopeGateResult:
    """
    Evaluate Art. 2 / Art. 5 / Art. 25 / Art. 27 / Art. 50 / Art. 51 gates
    against the Stage A payload.

    Args:
        stage_a: A schema-valid T01a payload (FLI-derived fields are optional;
            absent values are treated as the safest default).

    Returns:
        ScopeGateResult. ``verdict`` defaults to ``in_scope`` whenever the
        questionnaire fields are absent — this preserves the legacy code path
        for fixtures that pre-date the FLI extension.
    """
    reasoning: list[str] = []

    halted = _halt_gates(stage_a, reasoning)
    if halted is not None:
        return halted

    # ── In-scope path: surface derived flags + advisory reasoning ──
    result = ScopeGateResult(
        verdict="in_scope",
        become_provider_under_art25=_art25_flag(stage_a),
        triggers_art50_transparency=_art50_flag(stage_a),
        is_gpai_systemic=bool(stage_a.get("gpai_systemic_risk")),
    )

    if result.become_provider_under_art25:
        reasoning.append(
            "Art. 25 §§1–2 status change declared; entity assumes provider obligations (FLI-E2)."
        )
    if result.is_gpai_systemic:
        reasoning.append(
            "GPAI model meets Art. 51 §2 systemic-risk threshold; Art. 55 obligations apply (FLI-R1)."
        )
    if result.triggers_art50_transparency:
        reasoning.append(
            "Art. 50 transparency obligation(s) triggered by declared functions (FLI-R4)."
        )
    result.triggers_fria, fria_note = fria_reason(stage_a)
    if fria_note:
        reasoning.append(fria_note)

    if not reasoning:
        reasoning.append("No pre-intake scoping flags raised; proceed to Stage B.")

    result.reasoning = reasoning
    return result
