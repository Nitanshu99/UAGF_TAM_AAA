"""The flat S6 field projection: every value its contract names, in its vocabulary."""
from __future__ import annotations

from typing import Any

from aaa.integrations.s6_contract import vocabulary as vocab
from aaa.integrations.s6_contract.columns import _domain_scores, _sensitive_feature_columns
from aaa.integrations.s6_contract.passthrough import _CHECKED, _STAGE_B_PASSTHROUGH
from aaa.integrations.s6_contract.translate import (
    annex_iii_sections,
    application_domain,
    split_modality,
)


def build_s6_fields(state: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Project *state* onto the S6 contract, and report what will not fit.

    :param state: The audit state.
    :returns: ``(fields, warnings)`` — the flat S6 view, and one warning per
        value outside S6's accepted vocabulary or per ambiguity S6's field
        shape cannot carry.
    """
    stage_a = (state.get("client_submission") or {}).get("stage_a") or {}
    stage_b = (state.get("client_submission") or {}).get("stage_b") or {}
    modality, system_type = split_modality(state)
    sections = annex_iii_sections(state)
    sensitive_columns, sensitive_skip_reason = _sensitive_feature_columns(state, stage_b)
    fields: dict[str, Any] = {
        "provider_name": stage_a.get("provider_name"),
        "system_type": system_type,
        "modality": modality,
        "application_domain": application_domain(state),
        "annex_iii_sections": sections,
        "risk_tier": state.get("risk_tier") or state.get("declared_risk_tier"),
        "applicable_articles": sorted(state.get("compliance_matrix") or {}),
        "blocking_findings": list(state.get("blocking_findings") or [])
                             + list(state.get("cgsa_blocking_findings") or []),
        "csp_satisfied": state.get("cgsa_csp_satisfiable"),
        # F15 (S19): `[]` per the sheet's own contract, plus why — never a bare
        # `null` a reader has to go find the reason for elsewhere.
        "sensitive_feature_columns": sensitive_columns,
        "sensitive_feature_columns_skip_reason": sensitive_skip_reason,
        # F11 (S18): the cohorts each fairness metric was computed over. Ships
        # beside `sensitive_feature_columns` so a consumer reads how an attribute
        # was grouped rather than inferring from its name whether it may be one.
        "sensitive_feature_groups": state.get("sensitive_feature_groups") or [],
        "governance_score": state.get("cgsa_composite_maturity_score"),
        "governance_verdict": state.get("cgsa_governance_verdict"),
        "domain_scores": _domain_scores(state),
    }
    fields.update({key: stage_b.get(key) for key in _STAGE_B_PASSTHROUGH})

    warnings = [w for w in (vocab.unsupported(name, fields.get(name), accepted)
                            for name, accepted in _CHECKED) if w]
    if len(sections) > 1:
        warnings.append(
            f"engagement is in scope for Annex III sections {', '.join(sections)}, "
            f"but S6's application_domain is a single value — reported as "
            f"{fields['application_domain']!r} (highest-confidence section)")
    return fields, warnings


__all__ = ["_CHECKED", "_STAGE_B_PASSTHROUGH", "build_s6_fields"]
