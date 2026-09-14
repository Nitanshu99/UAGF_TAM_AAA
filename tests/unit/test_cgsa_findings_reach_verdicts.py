"""A CGSA that declares itself non-compliant must not yield PASS verdicts.

A governance self-assessment declared itself non-compliant, with an unsatisfiable
constraint set and many blocking findings. The
delivered matrix scored Art.14 and Art.17 PASS — "verifier-accepted evidence
with no findings raised" — and Art.9 PASS_WITH_OBSERVATIONS. Two independent
causes, both fixed here.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.compliance_matrix.findings_by_article import _findings_by_article
from aaa.agents.tier1.phases.compliance_matrix.rationale import _rationale
from aaa.tools.findings import articles_for, normalise_article


def _cgsa_finding(**over: Any) -> dict[str, Any]:
    """A blocking finding in exactly the shape the CGSA schema mandates."""
    base = {"control_id": "C03", "control_name": "AI Risk Assessment Process",
            "finding": "Risk assessments are ad hoc and undocumented.",
            "eu_ai_act_article": "Article 9",
            "remediation_action": "Document the process and assign an owner."}
    base.update(over)
    return base


def test_the_cgsa_singular_field_name_is_recognised() -> None:
    """The schema requires ``eu_ai_act_article``; the reader only knew the plural."""
    assert articles_for(_cgsa_finding()) == ["Art.9"]


def test_the_cgsa_spelling_is_normalised() -> None:
    """``Article 9`` and ``Art.9`` are one obligation, not two (R17's class)."""
    assert normalise_article("Article 9") == "Art.9"
    assert normalise_article("Annex III") == "Annex_III"
    assert normalise_article("Art.10§2(f)") == "Art.10§2(f)", "internal spelling passes through"


def test_a_blocking_finding_is_material_without_an_explicit_severity() -> None:
    """The schema forbids ``gap_severity`` here, so reading one downgraded all of them."""
    index = _findings_by_article({"cgsa_blocking_findings": [_cgsa_finding()]})
    assert [f["materiality"] for f in index["Art.9"]] == ["material"]


def test_an_explicit_low_severity_still_wins() -> None:
    """Where a payload does carry a severity, it is honoured."""
    index = _findings_by_article(
        {"cgsa_blocking_findings": [_cgsa_finding(gap_severity="low")]})
    assert index["Art.9"][0]["materiality"] == "possibly_material"


def test_governance_gaps_reach_the_articles_they_fail() -> None:
    """Each gap indexes under its own article rather than vanishing."""
    index = _findings_by_article({"cgsa_blocking_findings": [
        _cgsa_finding(control_id="C03", eu_ai_act_article="Article 9"),
        _cgsa_finding(control_id="C24", eu_ai_act_article="Article 13"),
        _cgsa_finding(control_id="C34", eu_ai_act_article="Article 17")]})
    assert set(index) >= {"Art.9", "Art.13", "Art.17"}


def _rationale_for(findings: list[dict[str, Any]]) -> str:
    """The FAIL rationale an article carrying *findings* would print."""
    return _rationale("FAIL", [], findings)


def test_a_governance_only_article_states_a_reason() -> None:
    """Art.17 failed on controls alone and printed ``"; ; ; ."`` — a verdict with no reason.

    The CGSA schema names ``finding`` and no ``description``, so reading only
    ``description`` left one empty string per control. The join was still
    truthy, so ``'see findings register'`` could not fire either.
    """
    text = _rationale_for([
        _cgsa_finding(control_id="C34", control_name="Monitoring Plan",
                      finding="No post-market monitoring plan."),
        _cgsa_finding(control_id="C35", control_name="Drift Monitoring",
                      finding="Limited monitoring for drift."),
        _cgsa_finding(control_id="C36", control_name="Corrective Action",
                      finding="No corrective-action loop."),
        _cgsa_finding(control_id="C37", control_name="Log Retention",
                      finding="Retention period is undefined.")])

    assert "; ;" not in text, "the four silent joins that made Art.17 unreadable"
    assert "analysis: ;" not in text
    assert "No post-market monitoring plan." in text
    assert "Retention period is undefined." in text, "all four fit under the Q15 clip"


def test_the_failing_control_is_named() -> None:
    """A governance non-conformity is only actionable if it says which control failed."""
    text = _rationale_for([_cgsa_finding(control_id="C34",
                                         control_name="Post-Market Monitoring Plan")])

    assert "C34 (Post-Market Monitoring Plan):" in text


def test_the_substantive_sentence_wins_over_the_boilerplate() -> None:
    """S5 sends both, and its ``description`` is a counter, not a finding.

    ``finding_fields`` deliberately leaves the dialect's own ``description``
    alone — "Hard constraint violated for control C02." repeated across 26 of
    32 findings — and puts the written gap in ``finding``. Preferring
    ``description`` would print the useless one on a real engagement.
    """
    text = _rationale_for([_cgsa_finding(
        description="Hard constraint violated for control C02.",
        finding="Score 2 below threshold 3 (risk tier: high).")])

    assert "Score 2 below threshold 3 (risk tier: high)." in text
    assert "Hard constraint violated" not in text


def test_a_phase_finding_reads_exactly_as_before() -> None:
    """Phase findings carry ``control_id`` as ``None``, so nothing is prefixed to them."""
    text = _rationale_for([{"finding_id": "P4-NOT-TESTED", "control_id": None,
                            "control_name": None, "materiality": "material",
                            "description": "Output fairness could not be tested."}])

    assert text == ("Material non-conformity from independent analysis: "
                    "Output fairness could not be tested.")


def test_an_article_with_no_prose_falls_back() -> None:
    """With every finding silent the sentence must defer, not print separators."""
    assert "see findings register" in _rationale_for([])
    # Four of them is the case that used to slip past: one silent finding joins
    # to "", but four join to "; ; ; " — truthy, so the fallback never fired.
    assert "see findings register" in _rationale_for([{"control_id": f"C3{n}"} for n in range(4)])


def _observation(fid: str, text: str) -> dict[str, Any]:
    """A phase finding that qualifies a verdict without deciding it."""
    return {"finding_id": fid, "control_id": None, "materiality": "observation",
            "description": text}


def test_the_deciding_finding_leads_and_survives_the_clip() -> None:
    """Case 03: Art.15 failed on C15, but two observations filled the 300-character clip."""
    long = "Declared performance metrics recorded but not independently recomputed " * 3
    text = _rationale_for([
        _observation("P3-DATADICT", long), _observation("P3-DECLARED-UNVERIFIED", long),
        _cgsa_finding(control_id="C15", control_name="Adversarial Robustness",
                      finding="No adversarial robustness testing.", materiality="material")])
    assert "C15 (Adversarial Robustness): No adversarial robustness testing." in text
    assert text.index("C15") < text.index("Declared performance")


def test_a_fail_resting_on_the_self_assessment_says_so() -> None:
    """Only governance findings are material: the basis is the provider's, not ours."""
    governance = _cgsa_finding(control_id="C15", finding="No testing.", materiality="material")
    phase = {"finding_id": "P3-ROBUST", "control_id": None, "materiality": "material",
             "description": "Robustness probe FAILed."}
    assert _rationale_for([governance]).startswith(
        "Material non-conformity declared in the provider's governance self-assessment")
    assert _rationale_for([phase, governance]).startswith(
        "Material non-conformity from independent analysis and the provider's")
    assert _rationale_for([phase]).startswith("Material non-conformity from independent analysis:")


def test_a_governance_finding_is_cited_by_its_control_id() -> None:
    """T17's blocking_findings named only phase ids, so C15 vanished from the row."""
    from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry

    entry = _evidence_entry({}, "Art.15", "FAIL", [
        _observation("P3-DATADICT", "x."),
        _cgsa_finding(control_id="C15", finding="No testing.", materiality="material")])
    assert entry["finding_ids"] == ["C15", "P3-DATADICT"]
