"""What each artefact is accountable for — one declaration — fix 50.

This fact was written down **three** times: in the phase runners' ``tid_articles``
(what the phase is dispatched to produce), in
``compliance_matrix._TEMPLATE_ARTICLES`` (what an *admitted* artefact passes), and
in ``node_stubs.TEMPLATE_ARTICLES`` (what a stub or an unrun phase leaves
unevidenced). Compared against each other they disagreed in **seven** places, and
every disagreement had already cost something:

* T12/T13 named ``Art.15`` and ``Art.50`` in one map and ``Art.10§2(f)`` in
  another — finding **R15**, and a delivered ``Art.50 = PASS`` on an output
  sampling log;
* T16 was in one map and absent from another — finding **R17**, and five admitted
  ``PASS`` rows KPI 2 could not count;
* T07, T08, T10 and T18 are in the runners and the stubs and were **absent** from
  the matrix map entirely, so an admitted data-quality report evidenced nothing;
* T09 and T14 simply differed.

The pattern is the same each time and it is not a coincidence: **a contract stated
in more than one place is a contract that will disagree with itself.** Fixes 47 and
49 each repaired one instance of it. This is the general repair.

**The runners are the authority**, because a phase's ``tid_articles`` is what the
dispatch actually asks for and what the verification gates are handed. Compared
against the union, the runners were right in every one of the seven cases — so this
map *is* the runners' contracts, plus the two intake artefacts that precede the
pipeline and so have no runner to declare them. A test asserts the runners and this
map cannot drift apart again.
"""
from __future__ import annotations

from typing import Final

#: Template id → the articles that artefact is accountable for.
#:
#: Sub-articles are written as the runner writes them (``Art.10§2(f)``); scope and
#: ownership tests reduce them with
#: :func:`~aaa.tools.regulatory_coverage.engagement_scope.core_article`.
ARTEFACT_ARTICLES: Final[dict[str, list[str]]] = {
    # Intake — produced before the phase pipeline, so no runner declares them.
    "T01b_annex_iv_dossier": ["Art.11", "Annex_IV"],
    "T01c_intake_completeness_report": ["Annex_IV"],
    # Phase 1 — scope
    "T02_system_card": ["Art.5", "Art.13"],
    "T03_annex_iii_mapping": ["Art.6", "Annex_III"],
    "T04_risk_tier_decision": ["Art.5", "Art.6"],
    "T05_art43_decision": ["Art.43"],
    # Phase 2 — data governance
    "T06_datasheet_for_datasets": ["Art.10"],
    "T07_data_quality_report": ["Art.10"],
    "T08_special_category_data_log": ["Art.10"],
    # Phase 3 — model validation. The model card carries the metric suite, so it
    # evidences accuracy (Art. 15) as well as the transparency Art. 13 requires;
    # the matrix map had only Art. 13 and the Verifier cited Art. 15 anyway.
    "T09_model_card": ["Art.13", "Art.15"],
    "T10_explainability_report": ["Art.13"],
    "T11_robustness_report": ["Art.15"],
    # Phase 4 — bias examination. Art. 10 §2(f), not Art. 15 §1 (fix 47, R15).
    "T12_output_fairness_report": ["Art.10§2(f)"],
    "T13_output_sampling_log": ["Art.10§2(f)"],
    # Phase 5 — governance. Art. 14 arrives as CGSA domain D5 inside T14 (fix 31).
    "T14_governance_findings": ["Art.9", "Art.14", "Art.17"],
    "T15_monitoring_logging_review": ["Art.12", "Art.72"],
    # L-branch — GPAI, under the canonical spelling (fix 49, R17).
    "T16_uagf_tam_l_evidence": ["Art.15", "GPAI_51", "GPAI_52", "GPAI_53",
                                "GPAI_54", "GPAI_55"],
    # Phase 6 — close-out.
    "T17_compliance_matrix": ["Art.17"],
    "T18_audit_report": ["Art.43", "Annex_IV"],
}


def contract_for(tid: str) -> list[str] | None:
    """The articles *tid* is accountable for, or ``None`` when it has no contract.

    ``None`` is deliberately distinct from ``[]``: an artefact with no entry is a
    gap in this map, not an artefact accountable for nothing, and a caller that
    restricts a claim to the contract must be able to tell the two apart.

    :param tid: Template id, or a tier-3 namespaced key (``<tid>@<spawn>``).
    :returns: The contracted articles, or ``None``.
    """
    return ARTEFACT_ARTICLES.get(tid.split("@", 1)[0])


__all__ = ["ARTEFACT_ARTICLES", "contract_for"]
