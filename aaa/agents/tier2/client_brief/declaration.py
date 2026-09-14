"""What the provider *claimed* — the half of every finding the customer wrote.

The brief's whole job is the contrast "you told us X, the evidence shows Y".
Y is already all over the audit state; X lives in the intake declaration and in
the CGSA self-assessment, and is what this module hands to the model.
"""
from __future__ import annotations

from typing import Any

#: Stage A fields that are declarations *about the system* rather than
#: engagement bookkeeping. Contact names and assessment ids are not claims
#: anyone can be held to, and they crowd the prompt.
_DECLARATION_FIELDS: tuple[str, ...] = (
    "system_name", "version", "intended_purpose", "declared_modality",
    "declared_risk_tier", "declared_annex_iii_sections", "deployment_context",
    "provider_elects_third_party", "gdpr_overlap", "gpai_general_purpose",
    "special_category_data", "art43_preview", "entity_type",
    "territorial_scope", "art5_prohibited_practices",
    "art50_transparency_triggers", "art6_derogation_claimed",
    "art6_derogation_rationale", "is_public_body_or_public_service",
)


def provider_declaration(state: dict[str, Any]) -> dict[str, Any]:
    """Return the provider's own claims about the system, from intake Stage A.

    :param state: Final ``AuditState``.
    :returns: The declared fields, plus the audit's field-by-field verification
        of them (``match`` / ``mismatch``) so the model never has to guess
        which claims were checked.
    """
    stage_a = (state.get("client_submission") or {}).get("stage_a") or {}
    return {
        "declared_by_provider": {k: stage_a[k] for k in _DECLARATION_FIELDS
                                 if k in stage_a},
        "audit_check_of_each_declaration": state.get("declaration_verification") or {},
    }


def cgsa_controls_for(article: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the governance self-assessment controls bearing on *article*.

    CGSA findings carry a free-text ``eu_ai_act_article`` ("Article 9"), while
    the matrix is keyed "Art.9"; both spellings are matched so a control is not
    silently dropped from the article it was raised against.

    :param article: Matrix article key.
    :param state: Final ``AuditState``.
    :returns: Blocking and positive control findings for that article.
    """
    wanted = {article, article.replace("Art.", "Article "),
              article.replace("Art.", "Article")}
    controls: list[dict[str, Any]] = []
    for entry in (state.get("cgsa_blocking_findings") or []):
        if str(entry.get("eu_ai_act_article", "")).strip() in wanted:
            controls.append({**entry, "kind": "gap"})
    return controls


def cgsa_strengths(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the governance controls the self-assessment scored as strengths."""
    return list(state.get("cgsa_positive_findings") or [])
