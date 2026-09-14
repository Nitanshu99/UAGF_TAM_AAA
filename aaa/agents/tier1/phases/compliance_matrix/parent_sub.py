"""A paragraph and the requirement it belongs to, reconciled — fix 43 (R11).

The delivered matrices carry pairs a regulator cannot read without explanation:

    case 03    Art.15   FAIL                   Art.15§1   PASS_WITH_OBSERVATIONS
    case 05    Art.15   PASS_WITH_OBSERVATIONS Art.15§1   INSUFFICIENT_EVIDENCE

Both are defensible **per article** — each row is derived from its own admitted
artefacts and its own findings — and nothing in T17 says so. A conformity table
that fails a requirement while passing its numbered paragraph reads as an error,
and a reader who does not already know how the matrix is built has no way to tell
that it is not one.

**Fix 47 was applied first, as the backlog required, and R11 survived it.** That
fix removed the *mis-attributed* half: Art. 15 §1 was carrying a fairness verdict
it was never entitled to, and it does not any more. What it left behind is a
correctly-attributed divergence, and in cases 03 and 05 it moved the pair rather
than closing it — `Art.10` (a material data-governance finding) now sits beside
`Art.10§2(f)` (the bias examination could not be run). Both true, both on their
own evidence, and still unreadable side by side without a sentence.

So this is a **presentation** repair, and deliberately only that: the verdicts are
untouched. Re-deriving a verdict from its parent's would be the opposite mistake —
a paragraph *may* be met while the requirement it belongs to is not, and saying so
is the honest reconciliation. Inventing agreement would not be.
"""
from __future__ import annotations

from aaa.tools.regulatory_coverage.engagement_scope import core_article

#: The verdict that means the audit reached no conclusion, as opposed to a
#: conclusion the reader may disagree with.
_UNASSESSED = "INSUFFICIENT_EVIDENCE"


def _describe(article: str) -> str:
    """Render an article id the way the sentence needs to read it."""
    return article.replace("§", " §")


def _why(verdict: str, other: str) -> str:
    """Say *how* the two differ, without ranking them.

    ``FAIL`` and ``INSUFFICIENT_EVIDENCE`` are different kinds of answer rather
    than different severities — one is a conclusion, the other is the absence of
    one — so the clause names the kind of difference instead of inventing a
    ladder to order them on.
    """
    if (verdict == _UNASSESSED) != (other == _UNASSESSED):
        if verdict == _UNASSESSED:
            return ("this row could not be assessed on the evidence available, "
                    "while the other was")
        return ("the other could not be assessed on the evidence available, "
                "while this row was")
    return "each rests on its own admitted artefacts and its own findings"


def relation_note(article: str, verdict: str, matrix: dict[str, str]) -> str:
    """Reconcile *article* with its parent or its paragraphs, when they diverge.

    :param article: The article this rationale belongs to.
    :param verdict: Its verdict in *matrix*.
    :param matrix: The complete compliance matrix.
    :returns: A trailing sentence, or ``""`` when nothing diverges.
    """
    parent = core_article(article)
    if parent != article:
        other = matrix.get(parent)
        if other is None or other == verdict:
            return ""
        return (f" {_describe(article)} is a paragraph of {parent}, which this matrix "
                f"reports {other}. The two are assessed separately and may legitimately "
                f"differ: {_why(verdict, other)}.")

    diverging = sorted(a for a, v in matrix.items()
                       if a != article and core_article(a) == article and v != verdict)
    if not diverging:
        return ""
    named = ", ".join(f"{_describe(a)} ({matrix[a]})" for a in diverging)
    return (f" This requirement's paragraphs are reported separately and do not all "
            f"agree with it: {named}. A requirement's verdict is not the sum of its "
            f"paragraphs': {_why(verdict, matrix[diverging[0]])}.")


__all__ = ["relation_note"]
