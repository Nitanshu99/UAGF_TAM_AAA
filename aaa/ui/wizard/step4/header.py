"""The conformity score and the plain-language reading of a final verdict.

Rendering moved to :mod:`aaa.ui.wizard.step4.verdict`; what stays here is the
arithmetic and the vocabulary, both of which the dashboard and the admin
console have to agree on.
"""
from __future__ import annotations

#: Matrix verdicts that mean "this article does not apply to you" (or was never
#: put to the test), and so enter neither the score nor "requirements met" — a
#: system scored 12/17 for articles it was never subject to reads as a failure
#: it did not have. One set, so the gauge and the tiles cannot disagree.
NOT_SCORED = frozenset({"NOT_APPLICABLE", "NOT_TESTED", "PENDING"})

#: verdict → weight towards the article-conformity score
_VERDICT_WEIGHT = {"PASS": 1.0, "PASS_WITH_OBSERVATIONS": 0.5}

#: final verdict → (headline, what it means for the reader). Written in the
#: second person: the customer is being told about their own system, and
#: "DISCLAIMER_OF_OPINION" is not a thing anyone can be told.
_VERDICT_WORDS: dict[str, tuple[str, str]] = {
    "PASS": ("Your system met every requirement we assessed.",
             "We found no gaps in the articles that apply to your system. Keep "
             "the evidence current — conformity is assessed against the system "
             "as it is today."),
    "PASS_WITH_OBSERVATIONS": (
        "Your system met the requirements, with some observations.",
        "Nothing we found blocks conformity, but there are points worth "
        "tightening before your next assessment. They are listed below."),
    "FAIL": ("We found gaps you will need to close.",
             "One or more articles that apply to your system are not yet met. "
             "The report explains each one and what would close it."),
    "DISCLAIMER_OF_OPINION": (
        "We could not reach a conclusion on what was supplied.",
        "There was not enough evidence to judge your system either way. This is "
        "not a failure — it means the audit needs more from you before it can "
        "say anything. The report lists exactly what is missing."),
}
_UNKNOWN = ("Your audit has finished.", "The report below has the detail.")


def article_rows(matrix: dict) -> dict:
    """The matrix without its paragraph rows (``Art.15§1`` refines ``Art.15``).

    A paragraph row is a finer reading of an article that is already in the
    matrix; counting it as a separate requirement double-weights that article.

    :param matrix: Article → verdict mapping.
    :returns: The rows whose key is a whole article.
    """
    from aaa.tools.regulatory_coverage.engagement_scope import core_article

    return {a: v for a, v in matrix.items() if core_article(str(a)) == str(a).strip()}


def article_score(matrix: dict) -> float | None:
    """Compute the 0–100 article-conformity score from the compliance matrix.

    With no applicable article there is nothing to score, and the answer is
    ``None`` — not ``0.0``, which reads as "met none of its requirements" for a
    minimal-risk system that had none (T-094).

    :param matrix: Article → verdict mapping (paragraph rows are skipped).
    :type matrix: dict
    :returns: Weighted PASS percentage over applicable articles, or ``None``
        when no article applies.
    :rtype: float | None
    """
    verdicts = [str(v).upper() for v in article_rows(matrix).values()]
    scored = [_VERDICT_WEIGHT.get(v, 0.0) for v in verdicts if v not in NOT_SCORED]
    return 100.0 * sum(scored) / len(scored) if scored else None


def article_parts(matrix: dict) -> dict[str, tuple[str, list[tuple[str, str]]]]:
    """Each whole article with its verdict and the paragraph rows that refine it.

    A paragraph whose article has no row of its own stands as an article, so no
    verdict in the matrix goes unshown.

    :param matrix: Article → verdict mapping.
    :returns: ``{article: (verdict, [(paragraph, verdict), …])}``, paragraphs sorted.
    """
    from aaa.tools.regulatory_coverage.engagement_scope import core_article

    whole = {str(a): str(v) for a, v in article_rows(matrix).items()}
    parts: dict[str, list[tuple[str, str]]] = {}
    for ref, verdict in matrix.items():
        parent = core_article(str(ref))
        if str(ref) in whole:
            continue
        if parent in whole:
            parts.setdefault(parent, []).append((str(ref), str(verdict)))
        else:
            whole[str(ref)] = str(verdict)
    return {a: (v, sorted(parts.get(a, []))) for a, v in whole.items()}


def verdict_words(verdict: str | None) -> tuple[str, str]:
    """Return the headline and explanation for *verdict*.

    :param verdict: Final verdict token.
    :returns: ``(headline, explanation)`` in the customer's language.
    """
    return _VERDICT_WORDS.get((verdict or "").upper(), _UNKNOWN)
