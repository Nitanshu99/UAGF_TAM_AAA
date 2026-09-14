"""Part 1 of the former ``scope_gate`` module (auto-split)."""
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
        """Return the ScopeGateResult as a plain dict."""
        return {
            "verdict": self.verdict,
            "reasoning": list(self.reasoning),
            "become_provider_under_art25": self.become_provider_under_art25,
            "triggers_fria": self.triggers_fria,
            "triggers_art50_transparency": self.triggers_art50_transparency,
            "is_gpai_systemic": self.is_gpai_systemic,
            "halt_engagement": self.halt_engagement,
        }


def _art25_flag(stage_a: dict[str, Any]) -> bool:
    return bool(set(stage_a.get("art25_status_change") or []) & _ART25_TRIGGERS)


def _art50_flag(stage_a: dict[str, Any]) -> bool:
    triggers = stage_a.get("art50_transparency_triggers") or []
    return any(t != "none" for t in triggers)
