"""term_match — whole-word, stem-aware term matching shared by the evidence tools.

Word boundaries as fix F14 set them ("face" is not in "HuggingFace"); the separator
inside a phrase is flexible ("law/enforcement", "credit-scoring"); a trailing ``*``
matches the words a term begins (``recruit*`` → "recruiters"); a leading ``*`` drops the
left boundary, for the second half of a compound (``*dimensional`` → "128-dimensional").
"""
from __future__ import annotations

import re


def match_term(term: str, text: str) -> str | None:
    """The span of lower-cased *text* that *term* matches, or ``None``.

    :param term: Lower-case term, optionally starting or ending in ``*``.
    :param text: Lower-cased haystack.
    """
    inner = r"[\s/_-]+".join(re.escape(part) for part in term.strip("*").split())
    head = r"[\w-]*" if term.startswith("*") else r"(?<![\w-])"
    tail = r"[\w-]*" if term.endswith("*") else r"(?![\w-])"
    found = re.search(rf"{head}{inner}{tail}", text)
    return found.group(0) if found else None


__all__ = ["match_term"]
