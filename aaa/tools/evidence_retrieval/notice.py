"""The terminal-round notice a retrieval loop sends when it must stop asking."""
from __future__ import annotations

from typing import Any

TERMINAL_NOTICE = (
    "FINAL ROUND — no further retrieval will be run for this phase. Answer from "
    "the hits you now have. If a claim is still unsupported, mark the relevant "
    "article INSUFFICIENT_EVIDENCE and say so. A reply containing "
    "'retrieval_plan' is rejected at this point: a plan is not an artefact."
)
def terminal_block(round_idx: int, reg_q: list[str], client_q: list[str],
                   *, final: bool) -> dict[str, Any]:
    """Build the ``retrieval_expansion`` bookkeeping block for one round.

    :param round_idx: 1-based expansion round just executed.
    :param reg_q: Regulatory queries run this round.
    :param client_q: Client-document queries run this round.
    :param final: Whether this is the last round the budget allows.
    """
    block: dict[str, Any] = {"round": round_idx, "final_round": final,
                             "regulatory_queries": reg_q,
                             "client_doc_queries": client_q}
    if final:
        block["notice"] = TERMINAL_NOTICE
    return block


__all__ = ["TERMINAL_NOTICE", "terminal_block"]
