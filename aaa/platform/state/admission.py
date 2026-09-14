"""Which artefacts a claim may rest on, and what the Verifier said about each.

An artefact is *admitted* when the independent Verifier's critique closed on a
verdict that lets it carry weight.  Three consumers ask this question — the
compliance matrix building an article's evidence list (fix 21), the T18 report
building its artefact manifest (fix 23), and the two KPI tools — and the answer
has to be the same each time, so it lives here rather than in whichever module
happened to need it first.

The Stage-B intake artefacts are the one exception, and it is a structural one:
the phase pipeline never critiques them because they are produced before it
starts, so presence is the only signal there is.  Presence is a *default* and
not an override — a critique that does arrive still governs, so a rejected
dossier admits nothing.
"""
from __future__ import annotations

from typing import Final

#: Critique verdicts that admit an artefact.  ``rerun`` and ``escalate_hitl``
#: are rejections; fix 20's ``unverified`` means the check never ran, which is
#: not an acceptance either.
ADMITTED_VERDICTS: Final[frozenset[str]] = frozenset({"accept", "accept_with_notes"})

#: What an artefact's verdict is when the Verifier never reached it.  Distinct
#: from a rejection: "not critiqued" and "rerun" are different findings about an
#: artefact, and a reader of the manifest needs to tell them apart.
NOT_CRITIQUED: Final = "not critiqued"

#: Stage-B intake artefacts, admitted by presence when nothing critiqued them.
PRESUMED_ADMITTED: Final[tuple[str, ...]] = (
    "T01b_annex_iv_dossier", "T01c_intake_completeness_report")


def artefact_verdict(state: dict, tid: str) -> str:
    """Return the Verifier's verdict on *tid*, or :data:`NOT_CRITIQUED`.

    :param state: Live audit state carrying ``verifier_critiques``.
    :param tid: Template id, or a tier-3 namespaced key (``<tid>@<spawn>``).
    :returns: The recorded verdict string, or ``"not critiqued"``.
    """
    critique = (state.get("verifier_critiques", {}) or {}).get(tid) or {}
    return str(critique.get("verdict") or NOT_CRITIQUED)


def admitted_artefacts(state: dict) -> set[str]:
    """Template ids whose evidence may be cited in support of a claim.

    :param state: Live audit state carrying ``verifier_critiques`` and
        ``phase_artefacts``.
    :returns: Template ids the Verifier admitted, plus any uncritiqued intake
        artefact that is present.
    """
    critiques = state.get("verifier_critiques", {}) or {}
    admitted = {tid for tid, crit in critiques.items()
                if (crit or {}).get("verdict") in ADMITTED_VERDICTS}
    artefacts = state.get("phase_artefacts", {}) or {}
    return admitted | {tid for tid in PRESUMED_ADMITTED
                       if tid in artefacts and tid not in critiques}


__all__ = ["ADMITTED_VERDICTS", "NOT_CRITIQUED", "PRESUMED_ADMITTED",
           "artefact_verdict", "admitted_artefacts"]
