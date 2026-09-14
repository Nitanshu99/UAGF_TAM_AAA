"""The Art. 43 conformity-assessment rule table (M9, M10).

The table had no tests at all. It is the legal core of the pipeline — it emits
the binding conformity-assessment procedure — so every branch is pinned here,
against the text of Regulation (EU) 2024/1689 Art. 43 as held in
``data/regulatory_corpus/EU_AI_Act.html``:

* **§1** governs Annex III **point 1** only. Where harmonised standards (Art. 40)
  or common specifications (Art. 41) *have* been applied the provider opts for
  Annex VI **or** Annex VII; where they have not, the provider *shall* follow
  Annex VII.
* **§2** governs Annex III **points 2 to 8**: Annex VI internal control, "which
  does not provide for the involvement of a notified body" — so there is no
  third-party election to make.
"""
from __future__ import annotations

import pytest

from aaa.tools.art43_select import Art43SelectInput, art43_select

BIOMETRIC = [{"annex_iii_section": "1"}]
EMPLOYMENT = [{"annex_iii_section": "3"}, {"annex_iii_section": "4"}]


def _decide(mapping, harmonised=False, elects=False, tier="high", acts=None):
    return art43_select(Art43SelectInput(
        risk_tier=tier, annex_iii_mapping=mapping,
        harmonised_standards_applied=harmonised, provider_elects_third_party=elects,
        annex_i_section_a_acts=list(acts or [])))


@pytest.mark.parametrize("tier", ["minimal", "limited", "gpai", "prohibited"])
def test_non_high_risk_tiers_are_not_applicable(tier):
    """Art. 43 applies only to high-risk systems (rules 1-2)."""
    assert _decide([], tier=tier)["procedure"] == "not_applicable"


def test_point_1_without_harmonised_standards_goes_to_notified_body():
    """Art. 43 §1 second subparagraph (b): Annex VII is mandatory."""
    decision = _decide(BIOMETRIC, harmonised=False)
    assert decision["procedure"] == "annex_vii_notified_body"
    assert "§1" in decision["rationale"]


def test_point_1_with_harmonised_standards_defaults_to_internal_control():
    """Art. 43 §1(a): the provider may opt for Annex VI."""
    assert _decide(BIOMETRIC, harmonised=True)["procedure"] == "annex_vi_internal_control"


def test_point_1_with_harmonised_standards_honours_the_election():
    """Art. 43 §1(b): the provider may instead opt for Annex VII."""
    assert _decide(BIOMETRIC, harmonised=True,
                   elects=True)["procedure"] == "annex_vii_notified_body"


def test_points_2_to_8_take_internal_control():
    """Art. 43 §2 assigns Annex VI to Annex III points 2-8."""
    assert _decide(EMPLOYMENT)["procedure"] == "annex_vi_internal_control"


def test_points_2_to_8_ignore_the_third_party_election():
    """Art. 43 §2 "does not provide for the involvement of a notified body"."""
    decision = _decide(EMPLOYMENT, elects=True)
    assert decision["procedure"] == "annex_vi_internal_control"
    assert "§2" in decision["rationale"]


# --- M9: the rationale must state only what the rule actually tested ---------

@pytest.mark.parametrize("mapping,harmonised,elects", [
    (EMPLOYMENT, False, False), (EMPLOYMENT, False, True),
    (EMPLOYMENT, True, False), (BIOMETRIC, False, False),
    (BIOMETRIC, True, False), (BIOMETRIC, True, True),
])
def test_rationale_never_claims_unapplied_harmonised_standards(mapping, harmonised, elects):
    """A rationale asserting harmonised standards where none were applied is
    a false statement in a regulator-facing binding statement (M9)."""
    rationale = _decide(mapping, harmonised=harmonised, elects=elects)["rationale"]
    if not harmonised:
        assert "harmonised standards applied in full" not in rationale
        assert "harmonised standard" not in rationale or "not" in rationale.lower()


def test_points_2_to_8_rationale_does_not_cite_the_paragraph_1_test():
    """§2 is unconditional; citing the §1 harmonised-standards trigger for it
    is the conflation the Verifier raised at call #007."""
    rationale = _decide(EMPLOYMENT, harmonised=True)["rationale"]
    assert "harmonised" not in rationale.lower()


# --- M18: Art. 43 §3, Annex I Section A ------------------------------------

def test_an_annex_i_section_a_product_takes_its_sectoral_procedure():
    """§3: neither Annex VI nor Annex VII, but the act's own procedure."""
    decision = _decide(EMPLOYMENT, acts=["medical_devices"])
    assert decision["procedure"] == "annex_i_sectoral"
    assert "§3" in decision["rationale"]
    assert "Regulation (EU) 2017/745" in decision["rationale"]


def test_section_3_outranks_the_annex_iii_routes():
    """A product under a sectoral act is not following Annex VI or VII."""
    for mapping in (BIOMETRIC, EMPLOYMENT):
        for harmonised in (True, False):
            assert _decide(mapping, harmonised=harmonised,
                           acts=["machinery"])["procedure"] == "annex_i_sectoral"


def test_section_3_does_not_apply_below_high_risk():
    """Art. 43 as a whole is a high-risk instrument."""
    assert _decide([], tier="minimal", acts=["lifts"])["procedure"] == "not_applicable"


def test_no_declared_acts_leaves_the_annex_iii_routes_untouched():
    """The ordinary case must be unchanged by M18."""
    assert _decide(EMPLOYMENT, acts=[])["procedure"] == "annex_vi_internal_control"
    assert _decide(BIOMETRIC, acts=[])["procedure"] == "annex_vii_notified_body"


def test_several_acts_are_all_cited():
    rationale = _decide(EMPLOYMENT, acts=["machinery", "ppe"])["rationale"]
    assert "Directive 2006/42/EC" in rationale
    assert "Regulation (EU) 2016/425" in rationale


def test_an_unknown_act_is_carried_through_not_dropped():
    """An unrecognised declaration is a reason to say so, not to ignore it."""
    decision = _decide(EMPLOYMENT, acts=["some_new_act"])
    assert decision["procedure"] == "annex_i_sectoral"
    assert "some_new_act" in decision["rationale"]


def test_the_catalogue_matches_the_act():
    """Annex I Section A holds twelve entries."""
    from aaa.tools.art43_select.annex_i import ANNEX_I_SECTION_A
    assert len(ANNEX_I_SECTION_A) == 12
    assert ANNEX_I_SECTION_A["medical_devices"][0] == "Regulation (EU) 2017/745"
