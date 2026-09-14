"""Finding F10 — a tool the model asks for is either run or said not to be.

``tool_calls`` was a field the phase prompts invited the model to fill and the
runtime never read. The tool block is assembled deterministically *before* the
model is invoked, so a tool named mid-protocol is simply not run — and nothing
recorded the divergence. At case 01 call #003 the DataAuditor asked for
``drift_test(training, evaluation)``; the pass-B payload carried no drift key,
the Report's tool log carried no drift entry, and the trail carried no
diagnostic. The agent's expectation and the runtime's behaviour parted company
in silence.

Two halves, and the first is what makes the second fair. The payload now names
what ran (``tools_executed``, from
:func:`aaa.agents.tier2.tools_run.tools_run`), so the model is told
rather than left to infer it from output keys that are not tool names. And a
name it emits anyway that did not run is logged here, at ``WARNING``, naming
the tool — the same shape fix 10 gave a model-asserted ``report_signed``: the
claim is discarded, but never quietly.

``tool_calls`` is stripped from the reply for the reason fix 10 strips
``retrieval_plan``: a field the runtime does not honour must not travel
downstream looking like a record of work done. The Report's ``tool_calls`` is
assembled by the phase agent from the tools it really ran.
"""
from __future__ import annotations

import re
from typing import Any

from aaa.tools.evidence_retrieval.logger import logger

#: ``"drift_test(minio://…, minio://…)"`` → ``drift_test``. The model writes
#: call expressions, dicts, or bare names depending on the phase prompt.
_NAME = re.compile(r"^[\s\"']*([A-Za-z_][A-Za-z0-9_]*)")


def requested_tools(result: Any) -> list[str]:
    """Extract the tool names a model reply asked for.

    :param result: The parsed model reply.
    :type result: Any
    :returns: Bare tool names, de-duplicated, in the order emitted.
    :rtype: list[str]
    """
    if not isinstance(result, dict):
        return []
    raw = result.get("tool_calls")
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        text = item.get("tool") if isinstance(item, dict) else item
        match = _NAME.match(str(text or ""))
        if match:
            names.append(match.group(1))
    return list(dict.fromkeys(names))


def check_tool_requests(result: Any, payload: dict[str, Any],
                        agent_name: str) -> dict[str, Any]:
    """Log any model-named tool that did not run, and strip ``tool_calls``.

    :param result: The model's final reply.
    :type result: Any
    :param payload: The payload it was given; ``tools_executed`` names the
        tools this dispatch ran.
    :type payload: dict[str, Any]
    :param agent_name: Agent name for the log line.
    :type agent_name: str
    :returns: The reply without its ``tool_calls`` key.
    :rtype: dict[str, Any]
    """
    if not isinstance(result, dict):
        return {}
    requested = requested_tools(result)
    executed = {str(name) for name in (payload.get("tools_executed") or [])}
    unexecuted = [name for name in requested if name not in executed]
    if unexecuted:
        logger.warning(
            "%s: named %d tool(s) the runtime did not run for this phase: %s. "
            "The tool block is fixed and runs before the agent is invoked, so "
            "tool_calls cannot request one (F10) — an assessment that needs a "
            "missing tool result belongs in the report as a gap. Tools that "
            "ran: %s.",
            agent_name, len(unexecuted), ", ".join(unexecuted),
            ", ".join(sorted(executed)) or "none declared")
    return {k: v for k, v in result.items() if k != "tool_calls"}


__all__ = ["check_tool_requests", "requested_tools"]
