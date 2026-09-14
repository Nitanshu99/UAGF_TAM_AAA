"""A declared reliance on Art. 10(5), and whether there is special-category data for it to cover.

FinClear's dossier says "Age variable retained under Art. 10 para 5 derogation for fairness
monitoring". T08 recorded no special category, left ``art10_5_statistical_correction_applies``
null and said nothing about the declaration, and the Verifier escalated it (MiniMax run,
2026-09-14). Art. 10(5) permits processing the special categories of personal data of GDPR
Art. 9(1) for bias detection; age is not one of them.
"""
from __future__ import annotations

from aaa.tools.document_evidence import Evidence, Question

#: "Art. 10(5)", "Article 10 (5)", "Art. 10 §5", "Art. 10 para 5", "Article 10 paragraph 5".
ART10_5 = r"(?i)\bart(?:icle)?\.?\s*10\s*(?:\(\s*5\s*\)|§\s*5|para(?:graph)?\.?\s*5)"

#: The datasheet question that finds the declaration in the dossier or the documents.
QUESTION = Question("art10_5", "Article 10(5) special categories bias detection derogation",
                    (), ("does not rely", "do not rely", "not relied"), pattern=ART10_5)

_ART9 = ("racial or ethnic origin, political opinions, religious or philosophical beliefs, "
         "trade-union membership, genetic data, biometric data for identification, health, "
         "and sex life or sexual orientation")


def art10_5_assessment(declared: Evidence | None,
                       special_cat_present: bool) -> tuple[bool | None, str | None]:
    """``(applies, rationale)`` for T08 from the declaration and what was found.

    :param declared: The grounded Art. 10(5) statement, if the provider made one.
    :param special_cat_present: Whether special-category data was declared or detected.
    :returns: ``(None, None)`` when nothing was declared — whether Art. 10(5) is relied on
        is the provider's to say.
    """
    if declared is None:
        return None, None
    if special_cat_present:
        return True, (f"{declared.cite()} Recorded as declared; the lawful basis for each "
                      "category is not verified here.")
    return False, (f"{declared.cite()} No special category of personal data was declared or "
                   f"detected in the dataset — the GDPR Art. 9(1) categories are {_ART9} — so "
                   "the Art. 10(5) derogation the declaration invokes has nothing to apply to.")


__all__ = ["ART10_5", "QUESTION", "art10_5_assessment"]
