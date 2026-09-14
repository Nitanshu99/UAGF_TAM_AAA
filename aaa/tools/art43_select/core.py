"""The Article 43 conformity-assessment rule table (§3.5).

Every rationale here is derived from the branch that produced it. The previous
table returned one hardcoded string on its fall-through — *"High-risk AI system
with harmonised standards applied in full; internal control procedure permitted
by Art. 43 §2"* — on a branch that never reads ``harmonised_standards_applied``
and for a paragraph that imposes no such condition (M9). Because
``harmonised_standards_applied`` is ``False`` whenever Phase 1 builds ``T05``
(M10), that string was a false statement in every binding statement the system
wrote, and the Verifier was right to score ``factual_accuracy: 0`` against it on
all three attempts of the 2026-09-10 Mariposa run.

The paragraph split follows the Act as held in the corpus:

* **§1** governs Annex III **point 1** alone. With harmonised standards (Art. 40)
  or common specifications (Art. 41) applied, the provider *opts for* Annex VI
  (a) or Annex VII (b); without them the second subparagraph makes Annex VII
  mandatory.
* **§2** governs Annex III **points 2 to 8** and assigns Annex VI internal
  control, "which does not provide for the involvement of a notified body" —
  so a third-party election has nothing to attach to there.
* **§3** governs systems covered by the Union harmonisation legislation in
  **Annex I Section A**, and defers to the procedure those acts prescribe.

§3 is tested first (M18). It is the more specific instruction — its subject is
the product, not the use case — and its language is mandatory: such a provider
"shall follow the relevant conformity assessment procedure as required under
those legal acts", which is neither of the procedures §1 and §2 assign. A system
that is both an Annex I Section A product and an Annex III use case is assessed
against Section 2 of the AI Act *inside* the sectoral procedure, so answering
Annex VI or Annex VII for it would name a procedure the provider is not
following.
"""
from __future__ import annotations

from aaa.platform.state import Art43Decision
from aaa.tools.art43_select.annex_i import cite_acts
from aaa.tools.art43_select.art43selectinput import (  # noqa: F401
    Art43SelectInput,
    _non_high_risk_decision,
)
from aaa.tools.art43_select.point_1 import _point_1_decision


def art43_select(inputs: Art43SelectInput) -> Art43Decision:
    """Deterministic Article 43 procedure selector.

    Rule precedence (§3.5):
      1. Non-high-risk / GPAI / prohibited → ``not_applicable``
      2. High-risk + Annex I Section A product → Art. 43 §3, the sectoral procedure
      3. High-risk + Annex III point 1 → Art. 43 §1 (see :func:`_point_1_decision`)
      4. High-risk + Annex III points 2-8 → Art. 43 §2, internal control

    :param inputs: Risk tier, Annex III mapping, and the two provider flags.
    :returns: The procedure and the rationale for the branch that chose it.
    """
    decision = _non_high_risk_decision(inputs.risk_tier)
    if decision is not None:
        return decision

    if inputs.annex_i_section_a_acts:
        return Art43Decision(
            procedure="annex_i_sectoral",
            rationale=(
                "High-risk AI system covered by Union harmonisation legislation "
                "listed in Annex I Section A: "
                f"{cite_acts(inputs.annex_i_section_a_acts)}. Under Art. 43 §3 the "
                "provider follows the conformity assessment procedure required by "
                "those legal acts; the requirements of Section 2 of Chapter III "
                "apply and form part of that assessment."
            ),
        )

    if any(e.get("annex_iii_section") == "1" for e in inputs.annex_iii_mapping):
        return _point_1_decision(
            inputs.harmonised_standards_applied, inputs.provider_elects_third_party)

    # Art. 43 §2 is unconditional for points 2-8: neither the harmonised-standards
    # test (which is §1's) nor a third-party election can change it.
    return Art43Decision(
        procedure="annex_vi_internal_control",
        rationale=(
            "High-risk AI system under Annex III points 2 to 8. Art. 43 §2 assigns "
            "the conformity assessment procedure based on internal control referred "
            "to in Annex VI, which does not provide for the involvement of a "
            "notified body."
        ),
    )
