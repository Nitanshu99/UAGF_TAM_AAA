"""Accepting a passage as evidence only when it says what the question asks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from aaa.tools.document_evidence.units import ENDS, units
from aaa.tools.term_match import match_term

#: How a document says something is missing: a gap, a plan, an absence.
NEGATIONS = ("not yet", "to build", "declared gap", "not implemented", "not in place",
             "does not exist", "no longer", "planned", "will be", "to be designated")
#: What turns a capability sentence into its opposite, for ``Question.absent``:
#: "No drift detection ... is in place" names the tool and the operating state.
DENIALS = NEGATIONS + ("no", "not", "never", "cannot", "none")
#: A period stated as a duration ("30 days", "30-day", "for the life of the record").
PERIODS = ("days", "*-day", "weeks", "months", "*-month", "years", "*-year", "life of")
#: A collection window stated as ISO dates or months ("2026-01-01 to 2026-08-31"), or
#: as years ("2024–2025"; case 05's intake, which the ISO-only form never matched).
DATE_RANGE = (r"\d{4}-\d{2}(?:-\d{2})?\s*(?:to|–|—|until)\s*\d{4}-\d{2}(?:-\d{2})?"
              r"|\b(?:19|20)\d{2}\s*(?:to|–|—|-|until)\s*(?:19|20)\d{2}\b")
#: The ``source_uri`` prefix of a passage that is a declared Stage B field.
DOSSIER = "annex_iv_dossier:"


@dataclass(frozen=True)
class Question:
    """A datasheet or review question, and the terms a passage must contain to answer it.

    ``required`` is a conjunction of alternatives: a unit must match at least one
    term from every group. A unit containing any ``absent`` term does not answer —
    "a tamper-evident log does not yet exist" is not log-integrity evidence.
    ``limit`` is how many distinct units one answer may quote (table rows);
    ``pattern`` is a regular expression the unit must also contain.

    ``subject`` names what the answer must be about ("training set"): a unit answers
    only if it names it, or if its passage is a declared field in ``subject_fields``,
    which is about that subject by definition. Case 05's ``training_data_description``
    calls its data a "screening corpus"; required in the sentence, "training data"
    left every datasheet question unanswered (T-20260913-097).
    """

    key: str
    query: str
    required: tuple[tuple[str, ...], ...]
    absent: tuple[str, ...] = ()
    limit: int = 1
    pattern: str | None = None
    subject: tuple[str, ...] = ()
    subject_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class Evidence:
    """A verbatim quote that answers a question, and where it came from."""

    quote: str
    source_uri: str
    document: str

    @property
    def origin(self) -> str:
        """The document's name, or "Annex IV dossier, <field>" for a declared field."""
        if self.source_uri.startswith(DOSSIER):
            return f"Annex IV dossier, {self.source_uri[len(DOSSIER):]}"
        return self.document

    def cite(self) -> str:
        """The quote attributed to where it came from, for a text field."""
        return f'Provider statement ({self.origin}): "{self.quote}"'


def _has(text: str, terms: Iterable[str]) -> bool:
    return any(match_term(term, text) for term in terms)


def about_subject(source_uri: str, question: Question) -> bool:
    """Whether a passage is a declared field that is, by its name, about the subject."""
    return (source_uri.startswith(DOSSIER)
            and source_uri[len(DOSSIER):] in question.subject_fields)


def answers(unit: str, question: Question, about: bool = False) -> bool:
    """Whether *unit* says what *question* asks, and does not say its opposite.

    :param unit: One sentence, line or bullet.
    :param question: What must be said.
    :param about: The passage is already known to be about ``question.subject``.
    """
    low = unit.lower()
    return ((about or not question.subject or _has(low, question.subject))
            and all(_has(low, group) for group in question.required)
            and not _has(low, question.absent)
            and (question.pattern is None or re.search(question.pattern, unit) is not None))


__all__ = ["DATE_RANGE", "DENIALS", "DOSSIER", "ENDS", "NEGATIONS", "PERIODS", "Evidence", "Question",
           "about_subject", "answers", "units"]
