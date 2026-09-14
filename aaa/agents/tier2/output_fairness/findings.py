"""The findings a fairness result raises, and the ones it raises when nothing could be decided."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.articles import FINDING_ARTICLES
from aaa.agents.tier2.output_fairness.thresholds import _ci, _over
from aaa.tools.fairness_ci import FOUR_FIFTHS
from aaa.tools.findings import Materiality, make_finding
from aaa.tools.report_render.numbers import fmt


def insufficient_findings(refused: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Record an attribute with no two cohorts to compare as an evidence gap.

    :param refused: Per-attribute entries the suite could not test.
    :returns: One ``possibly_material`` evidence-gap finding per attribute.
    """
    return [make_finding(
        finding_id=f"P4-FAIR-INSUFFICIENT-{attr['attribute'].upper()}",
        description=(
            f"Output fairness across '{attr['attribute']}' could not be tested on this "
            f"evaluation set: {attr['resolution']['reason']} No group-fairness verdict is "
            "asserted for this attribute."),
        materiality="possibly_material", articles=FINDING_ARTICLES, source_phase="P4",
        recommendation=(
            f"Supply an evaluation set in which '{attr['attribute']}' takes at least two "
            "values, or record why the attribute cannot be assessed."))
        for attr in refused]


def _description(attr: dict[str, Any]) -> str:
    """The finding's sentence: the numbers, their intervals, and what they decide."""
    numbers = (f"disparate-impact ratio={fmt(attr['di'].get('ratio'))}{_ci(attr['di'])}, "
               f"demographic-parity diff={fmt(attr['dp'].get('difference'))}{_ci(attr['dp'])}"
               f"{_over(attr.get('resolution') or {})}")
    if attr["verdict"] == "INSUFFICIENT_EVIDENCE":
        return (f"Output fairness across '{attr['attribute']}' is undecided ({numbers}): the "
                f"ratio's interval spans the four-fifths comparator ({FOUR_FIFTHS}), so this "
                "evaluation set establishes neither adverse impact nor its absence.")
    return f"Output fairness across '{attr['attribute']}' is {attr['verdict']} ({numbers})."


_MATERIALITY: dict[str, Materiality] = {
    "FAIL": "material", "INSUFFICIENT_EVIDENCE": "possibly_material",
    "PASS_WITH_OBSERVATIONS": "possibly_material"}
_RECOMMENDATION = {
    "INSUFFICIENT_EVIDENCE": ("Supply a larger evaluation set for this attribute, so the "
                              "ratio's interval can be placed against four-fifths."),
}


def fairness_findings(per_attribute: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Raise a finding per protected attribute that fails, is undecided, or shows disparity.

    :param per_attribute: Per-attribute breakdown from the fairness suite.
    :returns: Findings for FAIL / INSUFFICIENT_EVIDENCE / PASS_WITH_OBSERVATIONS attributes.
    """
    return [make_finding(
        finding_id=f"P4-FAIR-{attr['attribute'].upper()}",
        # Q15/Q2: intervals, the pair and the cohorts travel with every number.
        description=_description(attr), materiality=_MATERIALITY[attr["verdict"]],
        articles=FINDING_ARTICLES, source_phase="P4",
        recommendation=_RECOMMENDATION.get(
            attr["verdict"], "Investigate and mitigate the group disparity before deployment."))
        for attr in per_attribute if attr["verdict"] in _MATERIALITY]


__all__ = ["_ci", "_over", "fairness_findings", "insufficient_findings"]
