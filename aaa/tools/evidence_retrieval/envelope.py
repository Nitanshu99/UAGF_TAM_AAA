"""Unwrapping a tool-call envelope, and telling a plan apart from an answer."""
from __future__ import annotations

from typing import Any, Final, Sequence

from aaa.tools.evidence_retrieval.contract import contract_unmet

#: The keys a retrieval plan is made of.  A reply whose *every* key is one of
#: these is a plan however it is wrapped — finding Q4: case 01's
#: CyberSecurityAgent replied ``{"regulatory_queries": [...]}``, 97 characters
#: with no ``retrieval_plan`` wrapper, and neither the expansion loop nor the
#: close recognised that shape.  The plan was returned as the answer, the
#: narrative key it did not contain read as empty, and the spawn recorded
#: ``llm_fallback_mode=true`` as though the call had failed.
_PLAN_KEYS: Final[frozenset[str]] = frozenset({
    "retrieval_plan", "regulatory_queries", "client_doc_queries", "queries"})
class RetrievalPlanNotAnsweredError(RuntimeError):
    """The model returned a ``retrieval_plan`` when retrieval was closed."""
def unwrap_tool_envelope(result: Any, contract: Sequence[str]) -> Any:
    """Return the artefact a tool-call envelope carries, else *result* unchanged.

    Phase 6 of the 2026-09-09 Mariposa re-run spent **396 s** producing a
    complete T18 and lost it to its own wrapper::

        {"tool": "report_render",
         "args": {"template_id": "T18_audit_report", "payload": {…the report…}}}

    Every contracted key was in ``args.payload``, and the assertion reads the top
    level, so a finished report was called "not the artefact it was asked for".
    The re-prompt then exhausted the phase budget: T17, T18, the PDF and the
    client brief were all withheld over an envelope.

    The model is not misbehaving. ``report_render`` is a real tool named in its
    own prompt, and naming the tool it believes should render its output is a
    reasonable reading of that prompt. The runtime assembles tool calls
    deterministically (F10), so the *name* is discarded exactly as before — but
    the payload beside it is the artefact, and throwing it away buys nothing.

    Unwrapping is gated on the inner payload actually meeting the contract, so
    this can never promote a non-answer: a wrapper around a plan, or around a
    reply missing its keys, is left alone to fail as it does today.

    :param result: The model's parsed reply.
    :param contract: Keys the caller will read the answer from.
    :returns: The unwrapped payload when it satisfies *contract*, else *result*.
    """
    if not contract or not isinstance(result, dict) or "tool" not in result:
        return result
    args = result.get("args")
    if not isinstance(args, dict):
        return result
    inner = args.get("payload") if isinstance(args.get("payload"), dict) else args
    if isinstance(inner, dict) and not contract_unmet(inner, contract):
        return inner
    return result
def _not_an_answer(result: Any, contract: Sequence[str]) -> str | None:
    """Say why *result* is not the artefact it was asked for, or ``None``.

    The two failures are one failure: a reply that is a plan and a reply that
    carries none of its contracted keys are both *not the answer*, and both earn
    exactly one re-prompt between them rather than one each.
    """
    if plan_in(result) is not None:
        return "it is a retrieval plan, and a plan is not an artefact (F15)"
    if contract_unmet(result, contract):
        present = ", ".join(sorted(result)) if isinstance(result, dict) and result \
            else "nothing"
        return (f"it carries none of the keys its output contract names "
                f"({', '.join(contract)}) — keys present: {present}")
    return None
def plan_in(result: Any) -> dict[str, Any] | None:
    """Return the retrieval plan *result* carries — wrapped or bare — else ``None``.

    :param result: The model's parsed reply.
    :returns: The plan dict to execute, or ``None`` when the reply is an answer.
    """
    if not isinstance(result, dict) or not result:
        return None
    plan = result.get("retrieval_plan")
    if isinstance(plan, dict):
        return plan
    # Bare: the whole reply is queries and nothing else. A reply carrying real
    # content beside a query list is an answer, and is left alone.
    return result if set(result) <= _PLAN_KEYS else None


__all__ = ["RetrievalPlanNotAnsweredError", "_PLAN_KEYS", "_not_an_answer", "plan_in", "unwrap_tool_envelope"]
