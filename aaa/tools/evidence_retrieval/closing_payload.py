"""The payload of the one closing re-prompt: retrieval shut, the contract stated."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.evidence_retrieval.contract import _contract_notice
from aaa.tools.evidence_retrieval.notice import TERMINAL_NOTICE


def closing_payload(payload: dict[str, Any], contract: Sequence[str]) -> dict[str, Any]:
    """Build the closing re-prompt payload.

    :param payload: The payload the model was last given.
    :param contract: Keys the caller will read the answer from; empty states none.
    :returns: The payload with retrieval closed and, where declared, the contract.
    """
    closed = {**payload, "retrieval_expansion": {
        "round": 0, "final_round": True, "retrieval_closed": True,
        "regulatory_queries": [], "client_doc_queries": [],
        "notice": TERMINAL_NOTICE}}
    if contract:
        closed["output_contract"] = _contract_notice(contract)
    if contract:
        closed["output_contract"] = _contract_notice(contract)
    return closed


__all__ = ["closing_payload"]
