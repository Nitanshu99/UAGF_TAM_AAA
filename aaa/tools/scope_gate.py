"""
scope_gate — deterministic MCP-style tool (§4.5).

Pre-Stage-A scoping gate derived from the Future of Life Institute
"EU AI Act Compliance Checker" (v1.0, 2025-07-28; CC-BY-SA, source:
https://artificialintelligenceact.eu/assessment/eu-ai-act-compliance-checker/).

Runs over the optional FLI-derived fields on a Stage A (T01a) payload
and returns a single verdict plus a list of reasoning strings each
citing the controlling Article. Designed to fail fast before the
IntakeValidator triggers Phase 1.

Verdict semantics:
  in_scope     – continue to Stage B / Phase 1 (default safe verdict).
  prohibited   – Art. 5 practice declared; engagement halts immediately.
  excluded     – Art. 2 full exclusion (military / third-country LEA).
  out_of_scope – no Art. 2 territorial nexus to the Union.

Derived flags (always populated, used by the Orchestrator / T17):
  become_provider_under_art25 – any Art. 25 §§1–2 status change declared.
  triggers_fria               – public body / public service + high risk.
  triggers_art50_transparency – any Art. 50 trigger declared.
  is_gpai_systemic            – GPAI model meeting Art. 51 §2 threshold.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ScopeVerdict = Literal["in_scope", "prohibited", "excluded", "out_of_scope"]

_FULL_EXCLUSIONS: set[str] = {"military", "third_country_law_enforcement"}
_TERRITORIAL_NEXUS: set[str] = {
    "placed_on_eu_market",
    "gpai_placed_on_eu_market",
    "established_in_eu",
    "importer_in_eu",
    "output_used_in_eu",
}
_ART25_TRIGGERS: set[str] = {
    "name_trademark",
    "intended_purpose_change",
    "substantial_modification",
}


@dataclass
class ScopeGateResult:
    """Output contract for scope_gate."""
    verdict: ScopeVerdict
    reasoning: list[str] = field(default_factory=list)
    become_provider_under_art25: bool = False
    triggers_fria: bool = False
    triggers_art50_transparency: bool = False
    is_gpai_systemic: bool = False
    halt_engagement: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reasoning": list(self.reasoning),
            "become_provider_under_art25": self.become_provider_under_art25,
            "triggers_fria": self.triggers_fria,
            "triggers_art50_transparency": self.triggers_art50_transparency,
            "is_gpai_systemic": self.is_gpai_systemic,
            "halt_engagement": self.halt_engagement,
        }


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
    if territorial is not None and not (set(territorial) & _TERRITORIAL_NEXUS):
        reasoning.append(
            "No Art. 2 territorial nexus to the Union declared; system out of scope (FLI-S1)."
        )
        return ScopeGateResult(
            verdict="out_of_scope",
            reasoning=reasoning,
            halt_engagement=True,
        )

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
    if (
        stage_a.get("is_public_body_or_public_service")
        and stage_a.get("declared_risk_tier") == "high"
    ):
        result.triggers_fria = True
        reasoning.append(
            "Public-law body / public service + high-risk system → Art. 27 FRIA required (FLI-R5)."
        )

    if not reasoning:
        reasoning.append("No pre-intake scoping flags raised; proceed to Stage B.")

    result.reasoning = reasoning
    return result


def _art25_flag(stage_a: dict[str, Any]) -> bool:
    return bool(set(stage_a.get("art25_status_change") or []) & _ART25_TRIGGERS)


def _art50_flag(stage_a: dict[str, Any]) -> bool:
    triggers = stage_a.get("art50_transparency_triggers") or []
    return any(t != "none" for t in triggers)
