"""AAA's internal vocabulary → the fields S6 reads — fixes F8 and F10.

**Why a translation and not a migration.** AAA's ``declared_modality`` enum is
``tabular, cv, nlp, time_series, llm, agentic, gpai``: a data modality *and* a
system type in one control (:mod:`aaa.ui.wizard.step3.stage_a.classification`).
S6's contract separates them, which is why its ``system_type`` row has to say
*"is_llm_or_agentic or other json fields"* — the source it names is a bool, and a
bool cannot tell ``llm`` from ``agentic`` (finding S14).

Migrating the internal enum would touch ``_L_BRANCH_MODALITIES``,
``suggest_task_type`` and the branch routing in
:mod:`aaa.agents.tier1.phases.nodes.route`, for no correctness the boundary
cannot deliver. So the internal vocabulary stays, and the split happens here,
where the contract actually is.

**Why S6 gets the derived fields rather than deriving them.** Its sheet lists
these as internal fields it computes from S5 sources — but two of those
derivations are not computable on their side. ``application_domain`` needs an
Annex III section → domain mapping that existed nowhere in this codebase
(finding S15), and ``system_type`` needs the ``llm``/``agentic`` distinction that
``is_llm_or_agentic`` has already discarded. Handing over the derived values
removes both guesses without changing a byte of the audit state.
"""
from __future__ import annotations

from typing import Any, Final

#: AAA ``declared_modality`` → ``(S6 modality, S6 system_type)``.
#:
#: ``gpai`` maps to ``multimodal``/``llm``: a general-purpose model is not
#: restricted to one input modality, and it takes the LLM evaluation pathway.
_MODALITY_SPLIT: Final[dict[str, tuple[str, str]]] = {
    "tabular":     ("tabular", "traditional_ml"),
    "time_series": ("time_series", "traditional_ml"),
    "nlp":         ("text", "traditional_ml"),
    "cv":          ("image", "traditional_ml"),
    "llm":         ("text", "llm"),
    "agentic":     ("text", "agentic"),
    "gpai":        ("multimodal", "llm"),
}

#: Annex III section → S6 ``application_domain``. One-to-one with the section
#: titles in :data:`aaa.ui.wizard.constants.ANNEX_III_LABELS`.
_SECTION_DOMAIN: Final[dict[str, str]] = {
    "1": "biometrics", "2": "critical_infrastructure", "3": "education",
    "4": "employment", "5": "essential_services", "6": "law_enforcement",
    "7": "migration", "8": "justice",
}

#: Entry provenance meaning "declared, but Phase 1 refuted it". Excluded from the
#: domain, matching ``aaa.agents.tier2.scope_agent.diffing.decide_art43``.
_REJECTED: Final = "phase1_rejected"


def split_modality(state: dict[str, Any]) -> tuple[str, str]:
    """Separate AAA's conflated modality into S6's two fields.

    :param state: Audit state carrying ``modality`` (or ``declared_modality``)
        and ``is_llm_or_agentic``.
    :returns: ``(modality, system_type)``, both members of S6's vocabularies.
        An unrecognised modality yields ``"unknown"`` with the system type
        falling back to ``is_llm_or_agentic``, which can still distinguish
        traditional ML from the LLM pathway even when it cannot name which.
    """
    declared = str(state.get("modality") or state.get("declared_modality") or "").lower()
    if declared in _MODALITY_SPLIT:
        return _MODALITY_SPLIT[declared]
    return "unknown", ("llm" if state.get("is_llm_or_agentic") else "traditional_ml")


def annex_iii_sections(state: dict[str, Any]) -> list[str]:
    """Annex III sections this engagement is in scope for, verified first.

    Phase 1's verified mapping governs; the client's declaration is the
    fallback, and is populated in every delivered case even when Phase 1 is not.

    :param state: Audit state carrying ``annex_iii_mapping`` and
        ``declared_annex_iii_sections``.
    :returns: Sorted section numbers as strings; empty when neither is present.
    """
    verified = [
        str(e.get("annex_iii_section"))
        for e in (state.get("annex_iii_mapping") or [])
        if isinstance(e, dict) and e.get("provenance") != _REJECTED
        and e.get("annex_iii_section") is not None
    ]
    declared = [str(s) for s in (state.get("declared_annex_iii_sections") or [])]
    return sorted(set(verified or declared))


def primary_section(state: dict[str, Any]) -> str | None:
    """The Annex III section that best characterises this engagement.

    Ranked by the ``confidence`` T03 records for exactly this purpose, then by
    section number for determinism. Ranking matters: LegalMind is mapped to
    **§8 administration of justice** (0.75, client-declared) *and* **§1
    biometrics** (0.675, a Phase 1 addition on the marker ``"face"`` in a legal
    corpus). Taking the lowest section number would file a contract-drafting
    assistant under biometrics; taking the strongest evidence does not.

    :param state: Audit state.
    :returns: The section number, or ``None`` when none is in scope.
    """
    entries = [e for e in (state.get("annex_iii_mapping") or [])
               if isinstance(e, dict) and e.get("provenance") != _REJECTED
               and e.get("annex_iii_section") is not None]
    if entries:
        best = max(entries, key=lambda e: (float(e.get("confidence") or 0.0),
                                           -int(str(e["annex_iii_section"]))))
        return str(best["annex_iii_section"])
    declared = annex_iii_sections(state)
    return declared[0] if declared else None


def application_domain(state: dict[str, Any]) -> str:
    """The S6 ``application_domain`` for this engagement.

    :param state: Audit state.
    :returns: A member of
        :data:`aaa.integrations.s6_contract.vocabulary.APPLICATION_DOMAINS`;
        ``"unknown"`` when no section is in scope. A multi-domain engagement
        resolves to :func:`primary_section` — S6's field is singular, so the
        remaining ambiguity is reported as a warning rather than hidden.
    """
    section = primary_section(state)
    return _SECTION_DOMAIN.get(section or "", "unknown")


__all__ = ["split_modality", "annex_iii_sections", "primary_section",
           "application_domain"]
