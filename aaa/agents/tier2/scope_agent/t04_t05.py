"""T04 risk-tier decision and T05 Art. 43 decision artefact builders."""
from __future__ import annotations

#: Regulator-facing names for the procedure enum. ``.title()`` on the enum
#: produced "Annex Vi Internal Control" and "Annex Vii Notified Body" — it
#: lower-cases Roman numerals, which is a misspelling of the instrument in the
#: one sentence of the artefact that is a legal declaration (M15).
_PROCEDURE_LABELS = {
    "annex_vi_internal_control": "internal control based on Annex VI",
    "annex_vii_notified_body": (
        "assessment of the quality management system and of the technical "
        "documentation with the involvement of a notified body, based on Annex VII"),
    "annex_i_sectoral": (
        "the conformity assessment procedure required by the applicable Annex I "
        "Section A Union harmonisation legislation (Art. 43 §3)"),
    "not_applicable": "not applicable",
}




def build_t05(engagement_id: str, art43: dict, preview: str | None,
              delta: bool, inputs: dict, now: str, declared_tier: str | None = None) -> dict:
    """Build the T05 Art. 43 decision payload.

    :param declared_tier: The Stage A tier; when Phase 1 corrected it, the rationale says the
        procedure follows the verified tier, which T05 otherwise records unexplained beside it.
    """
    verified = inputs.get("risk_tier", "")
    corrected = (f" The procedure follows the Phase 1 verified risk tier '{verified}'; the "
                 f"declared tier '{declared_tier}' was corrected (T04_risk_tier_decision)."
                 if declared_tier and verified and declared_tier != verified else "")

    section_1_applies = any(
        e.get("annex_iii_section") == "1"
        for e in inputs.get("annex_iii_mapping", [])
    )
    return {
        "engagement_id": engagement_id,
        "procedure": art43["procedure"],
        "rationale": art43["rationale"] + corrected,
        "binding_statement": (
            f"The conformity assessment procedure for this engagement is "
            f"{_PROCEDURE_LABELS.get(art43['procedure'], art43['procedure'])}. "
            f"{art43['rationale']}"
        ),
        "preview_procedure": preview,
        "delta_from_preview": delta,
        "inputs": {
            "risk_tier": inputs.get("risk_tier", ""),
            "annex_iii_section_1_applies": section_1_applies,
            "harmonised_standards_applied": inputs.get("harmonised_standards_applied", False),
            "provider_elects_third_party": inputs.get("provider_elects_third_party", False),
        },
        "generated_at": now,
    }
