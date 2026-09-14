"""Part 1 of the former ``art43_select`` module (auto-split)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aaa.platform.state import Art43Decision


@dataclass
class Art43SelectInput:
    """Minimal inputs required by the selector (both preview and final modes)."""
    risk_tier: str                          # "prohibited" | "high" | "limited" | "minimal" | "gpai"
    annex_iii_mapping: list[dict[str, Any]] # list of AnnexIIIEntry dicts (may be empty at preview)
    harmonised_standards_applied: bool      # set by Phase 5; False at preview time
    provider_elects_third_party: bool       # immutable — from Stage A
    #: Annex I Section A act ids the product falls under (Art. 43 §3). Empty for
    #: an Annex III-only system, which is the ordinary case.
    annex_i_section_a_acts: list[str] = field(default_factory=list)


def _non_high_risk_decision(risk_tier: str) -> Art43Decision | None:
    """Rules 1–2 (+ prohibited): tiers where Art. 43 does not apply.

    :param risk_tier: Verified risk tier.
    :returns: A ``not_applicable`` decision, or ``None`` for high-risk tiers.
    """
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
    return None
