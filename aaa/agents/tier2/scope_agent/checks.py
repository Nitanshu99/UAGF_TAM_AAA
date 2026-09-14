"""Deterministic verification rules for Phase 1 (description → verdicts)."""
from __future__ import annotations

from aaa.agents.tier2.scope_agent.errors import _ART5_MARKERS


def build_description(t01a: dict, t01b: dict) -> str:
    """Concatenate key text fields for classifier / RAG queries."""
    parts = [
        t01a.get("intended_purpose", ""),
        t01b.get("general_description", ""),
        t01b.get("training_data_description", ""),
        t01b.get("design_process", ""),
    ]
    return " ".join(p for p in parts if p).lower()


def check_art5(description: str) -> tuple[bool, str]:
    """Check for Art. 5 prohibited practice markers in the description."""
    for marker in _ART5_MARKERS:
        if marker in description.lower():
            return True, marker
    return False, ""


def gpai_screen(t01a: dict, description: str) -> str | None:
    """Return a GPAI screening note if applicable, else ``None``."""
    if t01a.get("gpai_general_purpose") or "general purpose" in description:
        return (
            "System declared as / detected to be a GPAI model. "
            "Arts. 51–55 obligations apply. "
            "UAGF-TAM-L branch activated."
        )
    return None


def verify_modality(t01a: dict, t01b: dict) -> str:
    """Verify the declared modality using a keyword rule over ``model_type``."""
    declared = t01a.get("declared_modality", "tabular")
    model_type = t01b.get("model_type", "").lower()
    if "llm" in model_type or "language model" in model_type or "gpt" in model_type:
        return "llm"
    if "agentic" in model_type or "agent" in model_type:
        return "agentic"
    if "image" in model_type or "vision" in model_type or "cnn" in model_type:
        return "cv"
    if "time series" in model_type or "forecasting" in model_type:
        return "time_series"
    if "nlp" in model_type or "bert" in model_type or "text" in model_type:
        return "nlp"
    return declared


def determine_risk_tier(declared_risk_tier: str, verified_sections: list[str],
                        is_llm_or_agentic: bool, art50_triggered: bool | None = None) -> str:
    """Determine the verified risk tier.

    Rule: any confirmed Annex III section (without derogation) → ``high``;
    GPAI modality with a declared ``gpai`` tier → ``gpai``; a declared ``limited``
    or ``minimal`` tier follows the declared Art. 50 transparency triggers —
    ``limited`` only with one, ``minimal`` without (T-20260913-075: case 02 declared
    ``limited`` with triggers ``['none']``, and the declaration stood unchecked);
    otherwise the declared tier stands.

    :param art50_triggered: Whether an Art. 50 trigger is declared; ``None`` when
        the intake does not carry the triggers, which leaves the tier as declared.
    """
    if verified_sections:
        return "high"
    if is_llm_or_agentic and declared_risk_tier == "gpai":
        return "gpai"
    if declared_risk_tier in {"limited", "minimal"} and art50_triggered is not None:
        return "limited" if art50_triggered else "minimal"
    return declared_risk_tier
