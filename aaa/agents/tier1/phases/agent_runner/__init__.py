"""aaa.agents.tier1.phases.agent_runner — Shared async agent invocation helper.

Provides ``run_agent_on_state(agent, dispatch, state, timeout)`` which:

1. Runs ``agent.process(dispatch)`` in an asyncio-safe way (handles both
   running and non-running event loops via a thread-pool executor).
2. Applies the ``declaration_verification_delta`` from the Report back
   onto the mutable *state* dict.
3. Returns the updated state (or the original state on failure)."""
from aaa.agents.tier1.phases.agent_runner.apply_delta import _apply_delta  # noqa: F401
from aaa.agents.tier1.phases.agent_runner.dedup_accumulated import _dedup_accumulated  # noqa: F401
from aaa.agents.tier1.phases.agent_runner.logger import (  # noqa: F401
    _ACCUMULATE_KEYS,
    _evidence_uris,
    _invoke,
    logger,
)
from aaa.agents.tier1.phases.agent_runner.run_agent_on_state import run_agent_on_state  # noqa: F401

__all__ = [
    'logger', '_evidence_uris', '_invoke', '_ACCUMULATE_KEYS', '_dedup_accumulated', '_apply_delta',
    'run_agent_on_state', '__all__',
]
