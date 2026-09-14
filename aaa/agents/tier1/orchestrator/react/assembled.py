"""Whether the compliance matrix has been assembled — by its verdict, not by its entries.

A minimal-risk engagement has no binding article, so its assembled matrix is ``{}``.
Testing the dict's truthiness refused FINALIZE and re-assembled the matrix every turn
until the loop's budget ran out (case 02, clean loop, 2026-09-13; T-20260913-087).
``final_verdict`` is written only by the matrix step, and is ``None`` until then.
"""
from __future__ import annotations

from typing import Any


def matrix_assembled(state: dict[str, Any]) -> bool:
    """True once the matrix has rows or the matrix step has produced a verdict, however few rows.

    :param state: The AuditState dict.
    """
    return bool(state.get("compliance_matrix")) or state.get("final_verdict") is not None


__all__ = ["matrix_assembled"]
