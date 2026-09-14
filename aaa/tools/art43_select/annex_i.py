"""Annex I Section A — the Union harmonisation legislation Art. 43 §3 defers to.

Art. 43 §3: "For high-risk AI systems covered by the Union harmonisation
legislation listed in Section A of Annex I, the provider shall follow the
relevant conformity assessment procedure as required under those legal acts."

That is a third route, and the rule table had only two (M18). An Annex I
Section A product does not take Annex VI or Annex VII: it takes the procedure
its own sectoral act prescribes, and the AI Act's Section 2 requirements are
assessed *inside* that procedure. Recording it as ``not_applicable`` would say
the opposite of what §3 says — Art. 43 very much applies, it points elsewhere.

The twelve acts are transcribed from ``data/regulatory_corpus/EU_AI_Act.html``.
The repealed instruments each entry amends or replaces are deliberately absent:
they appear in the Act's text as citations, not as Section A entries.
"""
from __future__ import annotations

#: ``{act id: (citation, subject)}`` for Annex I Section A, in the Act's order.
#: Keyed by the Stage A contract's own enum (``templates/T01a_stage_a_triage.json``
#: ``annex_i_section_a``); two keys once differed from it, so those acts lost
#: their citation. ``test_art43_section_a_intake`` holds the two in step.
ANNEX_I_SECTION_A: dict[str, tuple[str, str]] = {
    "machinery": ("Directive 2006/42/EC", "machinery"),
    "toys": ("Directive 2009/48/EC", "safety of toys"),
    "recreational_craft": ("Directive 2013/53/EU",
                           "recreational craft and personal watercraft"),
    "lifts": ("Directive 2014/33/EU", "lifts and safety components for lifts"),
    "atex_equipment": ("Directive 2014/34/EU",
             "equipment and protective systems for explosive atmospheres"),
    "radio_equipment": ("Directive 2014/53/EU", "radio equipment"),
    "pressure_equipment": ("Directive 2014/68/EU", "pressure equipment"),
    "cableway": ("Regulation (EU) 2016/424", "cableway installations"),
    "ppe": ("Regulation (EU) 2016/425", "personal protective equipment"),
    "gas_appliances": ("Regulation (EU) 2016/426", "appliances burning gaseous fuels"),
    "medical_devices": ("Regulation (EU) 2017/745", "medical devices"),
    "ivd_medical_devices": ("Regulation (EU) 2017/746",
                            "in vitro diagnostic medical devices"),
}


def cite_acts(act_ids: list[str]) -> str:
    """Render the declared acts as a citation string for the rationale.

    An id the catalogue does not hold is carried through verbatim rather than
    dropped: an unrecognised act is a reason to say so in the artefact, not a
    reason to decide as though the provider had declared nothing.

    :param act_ids: Section A act ids as declared at intake.
    :returns: A comma-separated citation list, or ``""`` for no acts.
    """
    return ", ".join(
        f"{ANNEX_I_SECTION_A[a][0]} ({ANNEX_I_SECTION_A[a][1]})"
        if a in ANNEX_I_SECTION_A else str(a)
        for a in act_ids)


__all__ = ["ANNEX_I_SECTION_A", "cite_acts"]
