"""Part 3 of the former ``art43_select`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.platform.state import Art43Decision
from aaa.tools.art43_select.art43selectinput import (  # noqa: F401
    Art43SelectInput,
    _non_high_risk_decision,
)
from aaa.tools.art43_select.core import art43_select  # noqa: F401


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
            annex_i_section_a_acts=list(state.get("annex_i_section_a_acts", []) or []),
        )
    )
