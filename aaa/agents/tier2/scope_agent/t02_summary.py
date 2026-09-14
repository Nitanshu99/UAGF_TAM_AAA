"""T02's phase summary, written from the fields beside it.

The LLM's summary used to replace this text. For case 04 it called the declared
modality verified while ``declaration_verification.modality`` said ``mismatch``, and
the Verifier escalated T02 with factual accuracy 0 (T-20260914-010). A summary of
deterministic checks is itself deterministic.
"""
from __future__ import annotations

from typing import Any


def phase1_summary(t01a: dict[str, Any], verified_modality: str,
                   verification_map: dict[str, Any], gpai_result: str | None,
                   art5: bool) -> str:
    """State what Phase 1 verified, in the terms of T02's own fields.

    :param t01a: The Stage A triage (declared values).
    :param verified_modality: The modality Phase 1 verified.
    :param verification_map: ``declaration_verification``: field → match / mismatch.
    :param gpai_result: ``gpai_screening_result``, or ``None`` when none was recorded.
    :param art5: Whether an Art. 5 prohibited practice was detected.
    """
    declared = t01a.get("declared_modality") or "not declared"
    mismatches = sorted(str(f) for f, v in verification_map.items() if v == "mismatch")
    modality = (f"Declared modality '{declared}', verified '{verified_modality}'"
                f"{' (mismatch)' if 'modality' in mismatches else ''}.")
    return " ".join([
        f"Phase 1: {modality}",
        f"Declaration fields not matching the evidence: {', '.join(mismatches) or 'none'}.",
        f"Art. 5 prohibited practice: {'detected' if art5 else 'none detected'}.",
        f"GPAI screening: {gpai_result or 'no result recorded'}.",
    ])


__all__ = ["phase1_summary"]
