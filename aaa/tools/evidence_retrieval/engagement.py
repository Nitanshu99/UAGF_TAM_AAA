"""What this engagement is, as a retrieval query — fix 17.

Every phase agent's client-document seed is one string fixed at authoring time
and identical for every engagement. The DataAuditor asks its dossier about
"data governance training data quality missingness class balance PII policy"
whether the system under audit is a credit scorer or a legal-research agent.
The dossier, unlike the Regulation, is written in *the client's* vocabulary —
it says "CreditGuard v2.1", "LexAI", "isotonic calibration", "PSI drift" — so a
query phrased in the declaration's own terms can reach passages the authored
string cannot.

**It has to be its own query.** The obvious reading of "widen the seed" is to
append these terms to the authored one, and that was measured on case 04's
49-chunk collection and rejected: the concatenated query kept **0 of 3** of the
DataAuditor's own hits and **0 of 3** of the ModelValidator's, collapsing every
phase onto the same three cover pages, because identity terms dominate a vector
query and stop it discriminating between subjects. Run separately and folded in
with :func:`~aaa.tools.evidence_retrieval.dedup.merge_hits`, the same terms keep
**3 of 3** everywhere and add one to three engagement-specific chunks on top.
Widening the seed means asking another question, not asking a longer one.

Nothing here is phase-specific: the declaration describes the system, and the
phase's own authored query supplies the subject. That is the division of labour
that makes the two queries additive rather than competing.
"""
from __future__ import annotations

from typing import Any

#: Declaration fields naming what the system *is*, most discriminating first.
#: Prose fields are included because the dossier is prose — the client's own
#: description of the system is the best available description of it.
_IDENTITY = ("system_name", "intended_purpose", "general_description",
             "model_type", "model_framework", "task_type")

#: Fields naming what it operates on. ``sensitive_feature_columns`` is the
#: reason case 01's fairness findings exist and never appeared in any seed.
_SUBJECT = ("target_column", "sensitive_feature_columns", "harmonised_standards")

#: Fields naming how it is classified under the Regulation.
_CLASSIFICATION = ("modality", "declared_modality", "risk_tier",
                   "declared_risk_tier", "deployment_context")

#: Boolean declarations worth stating in words; a bare ``True`` retrieves nothing.
_FLAGS = {"gdpr_overlap": "GDPR personal data processing",
          "special_category_data": "special categories of personal data"}


def _flatten(value: Any) -> str:
    """Render one declaration value as query text (``""`` when it has none).

    Underscored identifiers are split into words: the dossier says "gradient
    boosted" where the declaration says ``sklearn_gradient_boosting_classifier``,
    and the embedding matches the words, not the token.

    :param value: A declaration field value of any shape.
    :returns: Space-joined text, or ``""`` for empty, boolean and null values.
    """
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(part for part in (_flatten(v) for v in value) if part)
    return str(value).replace("_", " ").strip()


def engagement_terms(decl: dict[str, Any]) -> list[str]:
    """Collect the declaration's discriminating terms, de-duplicated.

    Reads *decl* and its nested ``stage_b`` — the phase runners hand each agent
    a different slice of the submission, so both shapes have to be searched
    rather than assumed.

    :param decl: The dispatch's ``declaration_summary``.
    :returns: Query fragments in identity → subject → classification order.
    """
    stage_b = decl.get("stage_b") if isinstance(decl.get("stage_b"), dict) else {}
    sources: dict[str, Any] = {**(stage_b or {}), **decl}
    terms: list[str] = []
    for field in (*_IDENTITY, *_SUBJECT, *_CLASSIFICATION):
        text = _flatten(sources.get(field))
        if text and text not in terms:
            terms.append(text)
    terms += [phrase for field, phrase in _FLAGS.items() if sources.get(field) is True]
    sections = _flatten(sources.get("declared_annex_iii_sections"))
    if sections:
        terms.append(f"Annex III point {sections}")
    return terms


def engagement_query(decl: dict[str, Any]) -> str:
    """The client-document query derived from *decl*, or ``""``.

    Empty when the declaration carries no describing field — a dispatch that
    says only ``engagement_id`` describes no system, and a query built from
    nothing would retrieve the collection's arbitrary top chunks under the
    appearance of having asked something.

    :param decl: The dispatch's ``declaration_summary``.
    :returns: A single free-text query, or ``""`` when there is nothing to ask.
    """
    return " ".join(engagement_terms(decl or {}))


__all__ = ["engagement_query", "engagement_terms"]
