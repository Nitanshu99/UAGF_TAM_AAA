"""Splitting a passage into the sentences, lines and bullets that can answer a question."""
from __future__ import annotations

import re

#: Sentence ends, lines and bullets — but not the full stop of "Art. 73" or "e.g.".
_SPLIT = re.compile(r"(?<!\bArt\.)(?<!\bArts\.)(?<!\be\.g\.)(?<!\bi\.e\.)(?<!\bNo\.)"
                    r"(?<=[.;!?])\s+|\n+|\s+•\s+")

#: A shorter line is a heading ("2. DATA COLLECTED"), not a statement; it can still
#: start a wrapped pair.
_MIN_WORDS = 4
#: A closed sentence of this many words is a statement, not a heading.
_MIN_SENTENCE_WORDS = 3
#: A longer unit is layout, not a statement. PDF text extraction flattens a table into
#: one 165-word run, where "Live" from one row and "drift" from another would both
#: be "in the sentence" (live run bb7837, the monitoring plan PDF).
_MAX_WORDS = 60
#: Punctuation that closes a statement.
ENDS = (".", ";", "!", "?", ")", ":")


def _continues(line: str) -> bool:
    """A wrapped line goes on in lower case or with a bracket; a capital starts a new item.

    "Daily : Automated anomaly count dashboard" and "Weekly : False-positive rate
    review" are two schedule entries, and joined they read as automated accuracy
    monitoring (case 03's plan, which says its performance review is not operational).
    """
    return line[:1].islower() or line[:1] in "([{"


def units(text: str) -> list[str]:
    """Sentences, lines and bullets, and each line joined to the line it wraps into, 4–60 words.

    Joined only when the first does not close a statement and the second continues it.

    Only one continuation line: a longer join crosses table rows, and "…error rate
    above 1% Live" + "requests" + "Candidate complaints … Partial" would put a live
    status on the complaints channel. Nothing joins across sentence punctuation:
    "…server logs; 30-day account-deletion grace period." is not a log retention period.
    """
    parts = [" ".join(p.split()) for p in _SPLIT.split(text or "") if p.strip()]
    joined = [f"{a} {b}" for a, b in zip(parts, parts[1:]) if not a.endswith(ENDS) and _continues(b)]
    return [u for u in parts + joined if _statement(u)]


def _statement(unit: str) -> bool:
    """A unit of 4–60 words, or a shorter closed sentence ("Retained 3 years.").

    Case 03 declares "Per-alert log: … Retained 3 years." — three words, dropped as a
    heading, so T15 said no log retention period was evidenced (MiniMax run,
    2026-09-14). A heading carries no sentence-final full stop.
    """
    words = len(unit.split())
    return (_MIN_WORDS <= words <= _MAX_WORDS
            or (words >= _MIN_SENTENCE_WORDS and unit.endswith((".", "!", "?"))
                and any(c.islower() for c in unit)))


__all__ = ["ENDS", "units"]
