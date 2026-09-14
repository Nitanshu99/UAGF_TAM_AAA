"""Whether the reply met its output contract, and the notice sent back when it did not."""
from __future__ import annotations

from typing import Any, Sequence


class OutputContractNotMetError(RuntimeError):
    """The reply carried none of the keys its output contract names — fix 42."""
def contract_unmet(result: Any, contract: Sequence[str]) -> bool:
    """Whether *result* carries none of the keys it was contracted to return.

    "None of", not "all of": every caller in this codebase reads its narrative
    from a short list of alternatives — ``summary`` *or* ``rationale_summary``,
    ``security_narrative`` *or* ``summary`` — so the contract is met by any one
    of them arriving non-empty. That is the same question the caller asks one
    line later, moved to where it can still be acted on.

    :param result: The model's parsed reply.
    :param contract: Keys the caller will read the answer from. Empty means the
        caller declared no contract, and nothing is asserted.
    :returns: ``True`` when a contract was declared and none of its keys is
        present and non-empty.
    """
    if not contract:
        return False
    if not isinstance(result, dict):
        return True
    return not any(str(result.get(key) or "").strip() for key in contract)
def _contract_notice(contract: Sequence[str]) -> dict[str, Any]:
    """The contract, stated to the model in the closing re-prompt.

    Fix 28 enumerated the shapes a wrong reply *had* taken, and a model has more
    ways to be wrong than a list can hold — three of five spawn replies to one
    unchanged prompt were wrong, in two shapes the list did not hold. Stating
    what a right reply looks like is a finite instruction; enumerating the wrong
    ones is not.
    """
    return {
        "required_any_of": list(contract),
        "notice": (
            "Your previous reply did not carry the answer this dispatch was "
            f"contracted to produce. Reply with a JSON object containing at "
            f"least one of: {', '.join(contract)}. Do not emit a tool name, a "
            "tool call, tool arguments or a retrieval plan — the runtime's tools "
            "ran before you were invoked (see tools_executed) and no further "
            "retrieval will run. This is the last attempt; if it is not met, no "
            "artefact is filed from your reply."),
    }


__all__ = ["OutputContractNotMetError", "_contract_notice", "contract_unmet"]
