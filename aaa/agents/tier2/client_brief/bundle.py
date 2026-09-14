"""Assemble the per-article evidence bundle the brief is written from.

One bundle per article, one LLM call per bundle. The alternative — a single
call over the whole audit state — is what the PDF already does, and it is why
the customer gets a verdict table instead of a reason.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.client_brief.artefacts import artefact_excerpts, rejected_artefacts
from aaa.agents.tier2.client_brief.constants import article_title, verdict_rank
from aaa.agents.tier2.client_brief.declaration import cgsa_controls_for, provider_declaration

#: Finding fields worth the prompt space. ``declared`` / ``observed`` are the
#: contrast the brief is built on; the URI lists are long and add nothing a
#: reader can act on.
_FINDING_FIELDS: tuple[str, ...] = (
    "finding_id", "description", "materiality", "declared", "observed",
    "recommendation", "control_id", "source_phase", "eu_ai_act_articles",
)


def audited_articles(state: dict[str, Any]) -> list[str]:
    """Return every article the matrix reached, worst verdict first.

    :param state: Final ``AuditState``.
    :returns: Article keys ordered FAIL → INSUFFICIENT_EVIDENCE → PASS.
    """
    matrix: dict[str, str] = state.get("compliance_matrix") or {}
    return sorted(matrix, key=lambda a: (verdict_rank(matrix[a]), a))


def _findings_for(article: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the blocking findings raised against *article*, trimmed to essentials."""
    return [{k: f.get(k) for k in _FINDING_FIELDS}
            for f in (state.get("blocking_findings") or [])
            if article in (f.get("eu_ai_act_articles") or [])]


def article_bundle(article: str, state: dict[str, Any], store: Any) -> dict[str, Any]:
    """Build the complete evidence bundle for one article.

    :param article: Matrix article key, e.g. ``"Art.10"``.
    :param state: Final ``AuditState``.
    :param store: Evidence store used to quote admitted artefacts back.
    :returns: A JSON-serialisable bundle: the verdict and the audit's own
        rationale, the provider's declarations, the admitted evidence, the
        artefacts the Verifier rejected and why, the findings, and the
        governance controls tied to this article.
    """
    evidence = (state.get("article_evidence") or {}).get(article) or {}
    return {
        "article": article,
        "subject": article_title(article),
        "verdict": (state.get("compliance_matrix") or {}).get(article),
        "audit_rationale": evidence.get("rationale"),
        "provider_declaration": provider_declaration(state),
        "admitted_evidence": artefact_excerpts(evidence.get("evidence_uris") or [], store),
        "admitted_template_ids": evidence.get("supporting_template_ids") or [],
        "rejected_artefacts": rejected_artefacts(article, state),
        "findings": _findings_for(article, state),
        "governance_controls": cgsa_controls_for(article, state),
    }
