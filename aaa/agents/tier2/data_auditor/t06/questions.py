"""What T06 asks of the provider's documents (Datasheets for Datasets, Art. 10).

A datasheet describes one dataset — the one Phase 2 measured. Questions about how
*that* dataset was acquired, pre-processed, dated or retained therefore require the
passage to name it ("evaluation set"), so a sentence about the platform's live
records or its reference taxonomies is not quoted as the evaluation set's history.
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t08.art10_5 import QUESTION as ART10_5_QUESTION
from aaa.tools.document_evidence import DATE_RANGE, DENIALS, PERIODS, Question

#: How documents name the dataset in each role ``dataset_role`` returns.
ROLE_TERMS = {
    "training": ("training set", "training data*", "train split"),
    "evaluation": ("evaluation set", "evaluation data*", "test set", "validation set"),
}
#: With no role, the passage must still be about a dataset, not any "data collected".
_ANY_DATA = ("dataset*", "training data*", "training set", "train", "evaluation split")
_ORIGIN = ("originat*", "self-supplied", "supplied", "collected", "sourced", "provided by",
           "scraped", "purchased", "drawn from", "derived from", "extracted from")
#: Declared Annex IV fields that describe the dataset in each role; every sentence of
#: one is about that dataset whatever the provider calls it ("screening corpus").
ROLE_FIELDS = {"training": ("training_data_description",), "evaluation": ()}


def t06_questions(role: str | None) -> tuple[Question, ...]:
    """The T06 questions about the dataset in *role* ("training", "evaluation" or ``None``)."""
    about = {"subject": ROLE_TERMS.get(role or "", _ANY_DATA),
             "subject_fields": ROLE_FIELDS.get(role or "", ("training_data_description",))}
    return (
        Question("acquisition", f"{role or ''} dataset source origin collected drawn from",
                 (_ORIGIN,), DENIALS, limit=3, **about),
        Question("timeframe", f"{role or ''} dataset date range period", (), DENIALS,
                 pattern=DATE_RANGE, **about),
        Question("third_party", "third-party public reference data published sources",
                 (("third-party", "third party", "published", "public", "vendor", "licensed"),
                  ("data", "taxonomy", "reference list", "records", "corpus")),
                 DENIALS, limit=3, **about),
        Question("consent", "consent lawful basis data processing",
                 (("consent*",), ("data", "gdpr", "lawful basis", "processing", "profile*",
                                  "record*")), DENIALS),
        Question("preprocessing", f"{role or ''} dataset pseudonymised identifiers removed",
                 (("pseudonymi*", "anonymi*", "excluded", "removed", "hashed", "deduplicat*",
                   "cleaned", "filtered out"),), DENIALS, limit=2, **about),
        Question("labelling", "ground truth label decision recorded",
                 (("label*", "ground truth", "annotat*"),
                  ("decision*", "recorded", "derived", "annotator*", "audit trail")), DENIALS),
        Question("relationships", f"{role or ''} dataset drawn from subset of",
                 (("drawn from", "derived from", "extracted from", "subset of", "sampled from"),),
                 DENIALS, **about),
        Question("retention", f"{role or ''} dataset retention period deletion",
                 (("retention", "retain*", "deleted after", "removed after"), PERIODS),
                 DENIALS, **about),
        # Not a datasheet field: T08 reads it (a declared Art. 10(5) reliance).
        ART10_5_QUESTION,
    )


__all__ = ["ROLE_FIELDS", "ROLE_TERMS", "t06_questions"]
