"""The rationale sentence behind each article verdict, and the notes appended to it."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.fail_basis import fail_basis, ordered
from aaa.agents.tier1.phases.compliance_matrix.finding_prose import _clip, _prose


def _rationale(verdict: str, tids: list[str], findings: list[dict]) -> str:
    """One-sentence justification for an article verdict.

    *tids* are the artefacts the verdict may cite (see
    :func:`~aaa.agents.tier1.phases.compliance_matrix.admitted.admitted_artefacts`).
    When it is empty the sentence says so: the old ``or 'phase artefacts'``
    fallback claimed verifier-accepted evidence while naming none, which is the
    same false claim P7 raised, made without even a rejected artefact behind it.
    """
    # Findings carrying no prose are dropped before the join rather than after
    # it: joining them yielded separators with nothing between them ("; ; ; "),
    # which is truthy, so the fallback below could never fire. Same class of
    # defect as `_clip` and `stop` below (Q15) — a rationale reading as
    # corruption — and dropping them also spares Art.9's one real sentence the
    # six empty joins that trailed it.
    # Most material first, so the clip can only drop what qualifies the verdict,
    # never what decides it (fail_basis).
    descs = _clip("; ".join(prose for prose in map(_prose, ordered(findings)) if prose))
    # Finding descriptions are sentences and a clipped list ends in an ellipsis,
    # so a terminator is added only when one is actually missing — the old form
    # rendered "…FAIL (…diff=1.0).." in the delivered PDF.
    stop = "" if descs.endswith(("…", ".", "!", "?")) else "."
    basis = ", ".join(tids)
    if verdict == "FAIL":
        return f"{fail_basis(findings)}: {descs or 'see findings register'}{stop}"
    if verdict == "INSUFFICIENT_EVIDENCE":
        return (
            f"Required independent verification could not be performed: "
            f"{descs or 'no admitted evidence for this article'}{stop}"
        )
    if verdict == "PASS_WITH_OBSERVATIONS":
        if not basis:
            return ("Admitted with observations, on no verifier-accepted artefact: "
                    f"{descs or 'minor observations noted'}{stop}")
        return (f"Admitted evidence ({basis}) with observations: "
                f"{descs or 'minor observations noted'}{stop}")
    if not basis:
        return ("Admitted with no findings raised; no verifier-accepted artefact "
                "evidences this article.")
    return f"Admitted, verifier-accepted evidence ({basis}) with no findings raised."


def _scope_note(flag: str | None) -> str:
    """Say why an article nothing evidenced is in the matrix at all.

    Without it a reader meets ``Art.27 INSUFFICIENT_EVIDENCE`` with no account of
    where Art. 27 came from — no phase named it and no artefact cites it.

    :param flag: The scope-gate flag that brought the article into scope, or
        ``None`` when the gate did not.
    :returns: A trailing sentence, or ``""``.
    """
    if not flag:
        return ""
    return (f" In scope because the Stage A scope gate set {flag}, which records "
            "that the obligation applies — not that it is met.")


def _exclusion_note(excluded: list[tuple[str, str]]) -> str:
    """Name the artefacts the verdict may *not* cite, and the verdict that bars each.

    Dropping them silently would trade P7's false claim for a missing one — a
    reader of T17 could no longer tell that a model card exists at all.  The
    rationale is free text under the T17 schema, so the exclusion travels with
    the sentence that would otherwise have claimed them.

    :param excluded: ``(template id, verifier verdict)`` pairs.
    :returns: A trailing sentence, or ``""`` when nothing was excluded.
    """
    if not excluded:
        return ""
    named = ", ".join(f"{tid} ({verdict})" for tid, verdict in excluded)
    return f" Not admitted, and so excluded from this article's evidence: {named}."


__all__ = ["_clip", "_exclusion_note", "_prose", "_rationale", "_scope_note"]
