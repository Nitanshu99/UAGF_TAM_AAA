"""Reading the grounded document answers into T06 fields."""
from __future__ import annotations

import re
from typing import Mapping

from aaa.tools.document_evidence import DATE_RANGE, Evidence

Found = Mapping[str, Evidence | None]

#: A required text field that neither the dossier nor a document answers.
NOT_DECLARED = "Not declared in the Annex IV dossier or the provider's documents."


def cite(found: Found, key: str) -> str | None:
    """The quoted answer to *key*, attributed, or ``None``."""
    evidence = found.get(key)
    return evidence.cite() if evidence else None


def performed(found: Found, key: str) -> bool | None:
    """``True`` where a document says the step was done; unknown otherwise, never ``False``."""
    return True if found.get(key) else None


def timeframe(found: Found) -> str | None:
    """The collection window a document states for this dataset, with its source."""
    evidence = found.get("timeframe")
    window = re.search(DATE_RANGE, evidence.quote) if evidence else None
    return f"{window.group(0)} ({evidence.origin})" if evidence and window else None


def grounded(found: Found) -> list[str]:
    """The question keys a document answered, in question order."""
    return [key for key, evidence in found.items() if evidence]


__all__ = ["NOT_DECLARED", "Found", "cite", "grounded", "performed", "timeframe"]
