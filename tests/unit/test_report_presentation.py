"""Fixes 34–37 — what the delivered PDF says, and what it used to leave out.

The report reviewed in part 2 was typographically good and substantively
misleading: it presented a provisional, unsigned assessment as a `FINAL
VERDICT`, filled its evidence sections with unresolvable URIs, printed a float's
``repr`` at seventeen significant figures, and cut its own rationale mid-word.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.compliance_matrix.rationale import _clip, _rationale
from aaa.agents.tier2.report_architect.roadmap import remediation_roadmap
from aaa.tools.report_render.numbers import fmt, shorten
from aaa.tools.report_render.pdf.artefact_evidence import (
    explainability_rows,
    fairness_rows,
    resolve,
    robustness_rows,
)
from aaa.tools.report_render.pdf.matrix import build_matrix
from aaa.tools.report_render.pdf.matrix_row import _notes
from aaa.tools.report_render.pdf.status import is_provisional, verdict_label
from aaa.tools.report_render.pdf.summary import _scrub

_LONG = ("Output fairness across 'personal_status' is PASS_WITH_OBSERVATIONS "
         "(disparate-impact ratio=1.063187, demographic-parity diff=0.163522).")


def _rendered_text(flow: list) -> str:
    """Every string a reader would see, including the ones inside table cells."""
    out: list[str] = []
    for item in flow:
        out.append(str(getattr(item, "text", "")))
        for row in getattr(item, "_cellvalues", []) or []:
            out += [str(getattr(cell, "text", "")) for cell in row]
    return " ".join(out)


# --------------------------------------------------------------------------
# fix 34 — the report says whether it may be relied on (Q12)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("t18", [
    {"report_status": "PROVISIONAL_PENDING_HITL", "report_signed": False},
    {"report_status": "FINAL", "report_signed": False},
    {"report_status": "FINAL", "report_signed": True, "hitl_required": True},
])
def test_an_unsigned_or_pending_report_is_not_called_final(t18):
    """Each of the three states the delivered report was in, and hid."""
    assert is_provisional(t18) is True
    assert verdict_label({**t18, "final_verdict": "FAIL"}) == "PROVISIONAL VERDICT: FAIL"


def test_a_signed_final_report_still_says_final():
    """The banner is not simply relabelled — it follows the signature."""
    t18 = {"report_status": "FINAL", "report_signed": True, "final_verdict": "PASS"}

    assert is_provisional(t18) is False
    assert verdict_label(t18) == "FINAL VERDICT: PASS"


def test_the_cover_carries_the_reasons_the_signature_was_withheld():
    """Fix 10 derived them; until now nothing rendered them."""
    from aaa.tools.report_render.pdf.status import build_status

    text = _rendered_text(build_status({
        "report_status": "PROVISIONAL_PENDING_HITL", "report_signed": False,
        "signature_withheld": ["the engagement is pending human review"],
        "hitl_reason": "Phase 5 escalated T15."}))

    assert "provisional" in text.lower()
    assert "pending human review" in text
    assert "Phase 5 escalated T15." in text


# --------------------------------------------------------------------------
# fix 35 — the evidence sections carry evidence (Q13)
# --------------------------------------------------------------------------
def test_the_explainability_rows_carry_the_ranked_attributions():
    """SHAP produced these and the delivered report showed a URI instead."""
    rows = explainability_rows({
        "techniques_applied": ["shap", "lime"],
        "global_explanation": {"technique": "shap", "feature_importance": [
            {"rank": 1, "feature": "duration_months", "importance": 3.807245696}]},
        "local_explanations": [{}, {}]})
    flat = dict((k.strip(), v) for k, v in rows)

    assert flat["Techniques applied"] == "shap, lime"
    assert flat["1. duration_months"] == "3.807"
    assert flat["Local explanations"] == "2 instance(s) explained"


def test_the_robustness_rows_carry_the_measured_curve():
    """The probe curve is the Art. 15 evidence; it was never rendered."""
    rows = robustness_rows({
        "overall_robustness_verdict": "PASS", "clean_accuracy": 0.955,
        "min_adversarial_accuracy": 0.875,
        "probes": [{"probe_name": "eps_0.2", "adversarial_accuracy": 0.875}]})
    text = " ".join(f"{k}{v}" for k, v in rows)

    assert "0.955" in text and "adversarial accuracy 0.875" in text


def test_the_fairness_rows_expose_the_group_count_behind_each_metric():
    """45 single-year age cohorts is what makes Q2's finding an artefact."""
    rows = fairness_rows({
        "overall_fairness_verdict": "FAIL", "sensitive_features": ["age"],
        "demographic_parity": {"difference": 1.0, "verdict": "FAIL",
                               "group_rates": [{"group": str(i)} for i in range(45)]}})

    assert any("over 45 group(s)" in v for _, v in rows)


def test_an_unresolvable_artefact_degrades_to_nothing_rather_than_raising():
    """A report must still render when the evidence store cannot be reached."""

    class _Boom:
        """A store whose bucket is unreachable."""

        def get_artefact(self, uri):  # noqa: ARG002
            """Fail the way an unreachable bucket fails."""
            raise RuntimeError("bucket unreachable")

    assert resolve({"phase_artefacts": {"T10": {"uri": "minio://x"}}}, _Boom(), "T10") == {}
    assert resolve({"phase_artefacts": {}}, None, "T10") == {}


# --------------------------------------------------------------------------
# fix 36 — numbers and rationales a reader can use (Q15)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("value, expected", [
    (0.16352201257861637, "0.164"), (1.0, "1.000"), (200, "200"),
    (None, "—"), ("PASS", "PASS"), (True, "True"),
])
def test_a_metric_renders_at_a_readable_precision(value, expected):
    """Fixed width for floats; everything else is passed through untouched."""
    assert fmt(value) == expected


def test_a_number_already_embedded_in_prose_is_rounded_too():
    """Agent-composed descriptions interpolate floats the renderer cannot type."""
    assert shorten("diff=0.16352201257861637 over 300 rows") == "diff=0.164 over 300 rows"


def test_a_clipped_rationale_never_stops_mid_word():
    """The delivered report read "…is FAIL (d." four times."""
    clipped = _clip("; ".join([_LONG] * 4))

    assert clipped.endswith("…")
    assert not clipped.rstrip(" …").endswith("(d")
    assert len(clipped) <= 320


def test_a_clipped_rationale_does_not_get_a_second_terminator():
    """The ellipsis is a terminator; the branch used to add a full stop after it."""
    text = _rationale("FAIL", [], [{"description": _LONG}] * 4)

    assert ".." not in text
    assert "… ." not in text


def test_a_short_rationale_is_untouched():
    """Nothing is clipped, ellipsised or reflowed when it already fits."""
    assert _clip("Two sentences. That fit.") == "Two sentences. That fit."


def test_a_basis_shared_by_several_articles_is_stated_once():
    """Four articles carried the same 300-character paragraph across two pages."""
    articles = [{"article": a, "verdict": "FAIL", "rationale": _LONG + _LONG}
                for a in ("Art.10", "Art.10§2(f)", "Art.15", "Art.15§1")]
    notes = _notes(articles)

    assert list(notes.values()) == [1]
    assert _rendered_text(build_matrix({"articles": articles})).count(
        "See note 1 below") == 3


def test_a_basis_unique_to_one_article_gets_no_note():
    """A note is a cross-reference; one occurrence has nothing to refer to."""
    assert _notes([{"article": "Art.9", "rationale": _LONG + _LONG}]) == {}


# --------------------------------------------------------------------------
# fix 37 — summary, roadmap, management response (Q14, Q17)
# --------------------------------------------------------------------------
def test_the_scrubber_keeps_the_sentence_terminators():
    """It split on ". " and rejoined on " ", eating every full stop."""
    raw = ("Final verdict FAIL for CreditGuard v2.1. Two material findings drive it. "
           "Prompt metadata: source=PROMPT.md, llm_fallback_mode=false.")
    out = _scrub(raw)

    assert out == "Final verdict FAIL for CreditGuard v2.1. Two material findings drive it."
    assert "Prompt metadata" not in out


def test_an_unterminated_summary_gains_one():
    """A fragment the model left open still ends as a sentence."""
    assert _scrub("A single fragment").endswith(".")


def test_every_finding_gets_a_remediation_step():
    """The report asked for remediation and rendered no roadmap."""
    roadmap = remediation_roadmap([], [
        {"finding_id": "P4-FAIR-AGE", "materiality": "material",
         "recommendation": "Mitigate the disparity."},
        {"finding_id": "P4-FAIR-PERSONAL_STATUS", "materiality": "possibly_material"}])

    assert [s["finding_id"] for s in roadmap] == ["P4-FAIR-AGE", "P4-FAIR-PERSONAL_STATUS"]
    assert roadmap[0]["priority_label"] == "immediate"
    assert roadmap[0]["deadline_weeks"] == 4
    assert roadmap[1]["priority_label"] == "short_term"
    assert roadmap[0]["action"] == "Mitigate the disparity."


def test_the_partner_roadmap_is_never_rewritten_or_duplicated():
    """CGSA's items are the governance assessment's own product."""
    existing = [{"control_id": "C1", "recommended_action": "Partner step"},
                {"finding_id": "P4-FAIR-AGE", "recommended_action": "Already covered"}]
    roadmap = remediation_roadmap(existing, [
        {"finding_id": "P4-FAIR-AGE", "materiality": "material"}])

    assert roadmap[:2] == existing
    assert len(roadmap) == 2


def test_a_clean_engagement_gets_no_roadmap():
    """Silence on the healthy path — no findings, no steps."""
    assert remediation_roadmap([], []) == []
