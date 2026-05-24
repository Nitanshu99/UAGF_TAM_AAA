"""
art43_select — deterministic MCP-style tool (§3.5, §4.5).

Implements the Article 43 conformity-assessment procedure selector.
Runs TWICE per engagement:

  1. **Preview** — at Stage A submission, from *declared* values.
     Written to T01a.art43_preview.
  2. **Final**   — after Phase 1 verification, from *verified* values.
     Written to T05_art43_decision and AuditState.art43_decision.

Any difference between preview and final is recorded in T01c and raised
as a HITL "declaration mismatch" trigger (§8.4).

Reference implementation of the rule table from §3.5 of ARCHITECTURE.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aaa.platform.state import Art43Decision, AnnexIIIEntry


@dataclass
class Art43SelectInput:
    """Minimal inputs required by the selector (both preview and final modes)."""
    risk_tier: str                          # "prohibited" | "high" | "limited" | "minimal" | "gpai"
    annex_iii_mapping: list[dict[str, Any]] # list of AnnexIIIEntry dicts (may be empty at preview)
    harmonised_standards_applied: bool      # set by Phase 5; False at preview time
    provider_elects_third_party: bool       # immutable — from Stage A


def art43_select(inputs: Art43SelectInput) -> Art43Decision:
    """
    Deterministic Article 43 procedure selector.

    Rule precedence (§3.5):
      1. Non-high-risk → not_applicable
      2. GPAI → not_applicable (Arts. 51–55 govern)
      3. High-risk + Annex III §1 (biometric) + no harmonised standards → notified body
      4. High-risk + provider elects third party → notified body
      5. High-risk (remaining) → internal control

    Args:
        inputs: Art43SelectInput with risk tier, Annex III mapping, and flags.

    Returns:
        Art43Decision with procedure enum and human-readable rationale.
    """
    risk_tier = inputs.risk_tier

    # Rule 1 — non-high-risk systems
    if risk_tier in {"minimal", "limited"}:
        return Art43Decision(
            procedure="not_applicable",
            rationale=(
                "System is not high-risk per Art. 6 / Annex III; "
                "Art. 43 conformity assessment is not required."
            ),
        )

    # Rule 2 — GPAI models governed by Arts. 51–55
    if risk_tier == "gpai":
        return Art43Decision(
            procedure="not_applicable",
            rationale=(
                "GPAI model obligations are governed by Arts. 51–55 of Regulation (EU) 2024/1689; "
                "Art. 43 does not apply."
            ),
        )

    # Prohibited tier — no conformity assessment; workflow halts at Phase 1
    if risk_tier == "prohibited":
        return Art43Decision(
            procedure="not_applicable",
            rationale=(
                "System falls under Art. 5 prohibition; Art. 43 conformity assessment "
                "is not applicable — engagement halted."
            ),
        )

    # High-risk path
    is_annex_iii_biometric = any(
        e.get("annex_iii_section") == "1" for e in inputs.annex_iii_mapping
    )

    # Rule 3 — Annex III §1 biometric without harmonised standards
    if is_annex_iii_biometric and not inputs.harmonised_standards_applied:
        return Art43Decision(
            procedure="annex_vii_notified_body",
            rationale=(
                "Annex III §1 biometric identification system without full application of "
                "harmonised standards — notified-body review required per Art. 43 §1(a)."
            ),
        )

    # Rule 4 — provider elects third-party
    if inputs.provider_elects_third_party:
        return Art43Decision(
            procedure="annex_vii_notified_body",
            rationale=(
                "Provider has elected third-party notified-body assessment per Art. 43 §1(b)."
            ),
        )

    # Rule 5 — high-risk, harmonised standards applied, no third-party election
    return Art43Decision(
        procedure="annex_vi_internal_control",
        rationale=(
            "High-risk AI system with harmonised standards applied in full; "
            "internal control procedure permitted by Art. 43 §2."
        ),
    )


def art43_select_from_state(state: dict[str, Any], *, use_declared: bool = False) -> Art43Decision:
    """
    Convenience wrapper that reads from an AuditState dict.

    Args:
        state: AuditState dict.
        use_declared: If True, use declared_* fields (preview mode).
                      If False, use verified fields (final mode).
    """
    if use_declared:
        # Preview: build a minimal mapping from declared sections (no confidence / provenance)
        annex_iii_mapping = [
            {"annex_iii_section": s}
            for s in state.get("declared_annex_iii_sections", [])
        ]
        risk_tier = state["declared_risk_tier"]
        harmonised = False  # not yet assessed
    else:
        annex_iii_mapping = state.get("annex_iii_mapping", [])
        risk_tier = state["risk_tier"]
        harmonised = state.get("harmonised_standards_applied", False)

    return art43_select(
        Art43SelectInput(
            risk_tier=risk_tier,
            annex_iii_mapping=annex_iii_mapping,
            harmonised_standards_applied=harmonised,
            provider_elects_third_party=state.get("provider_elects_third_party", False),
        )
    )
