"""LangGraph StateGraph construction for the audit pipeline."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.orchestrator import wrappers
from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier1.phases.node_stubs import node_hitl_checkpoint, node_route
from aaa.agents.tier1.phases.nodes.plan import node_plan
from aaa.agents.tier1.phases.nodes.stage0 import node_stage0

logger = logging.getLogger(__name__)


def build_graph(agents: dict[str, Any], checkpointer: Any | None = None) -> Any:
    """Build and compile the 9-node StateGraph (``None`` when unavailable).

    :param agents: Phase agents keyed by role (from ``initialise_agents``).
    :param checkpointer: Optional LangGraph checkpointer.
    :returns: The compiled graph, or ``None`` if LangGraph is not installed.
    """
    try:
        from langgraph.graph import END, StateGraph  # type: ignore
    except ImportError:
        logger.info("LangGraph not installed; using sequential runner.")
        return None

    # The pipeline threads a plain dict (AuditState keys) through every node.
    # LangGraph's stubs want a TypedDict schema, but the runtime accepts a
    # plain dict and switching schemas would change channel semantics — so the
    # builder is typed Any and the constructor argument ignored, scoped here.
    g: Any = StateGraph(dict)  # pyright: ignore[reportArgumentType]
    g.add_node("stage_0", node_stage0)
    g.add_node("plan", node_plan)
    g.add_node("phase_1", lambda s: wrappers.node_phase_1(agents, s))
    g.add_node("route", node_route)
    g.add_node("parallel_phases", lambda s: wrappers.node_parallel_phases(agents, s))
    g.add_node("phase_5", lambda s: wrappers.node_phase_5(agents, s))
    g.add_node("compliance_matrix", node_compliance_matrix)
    g.add_node("hitl_checkpoint", node_hitl_checkpoint)
    g.add_node("phase_6", lambda s: wrappers.node_phase_6(agents, s))

    g.set_entry_point("stage_0")
    for src, dst in (("stage_0", "plan"), ("plan", "phase_1"), ("phase_1", "route"),
                     ("route", "parallel_phases"), ("parallel_phases", "phase_5"),
                     ("phase_5", "compliance_matrix"),
                     ("compliance_matrix", "hitl_checkpoint")):
        g.add_edge(src, dst)
    # The pipeline always runs through to Phase 6 to emit a *provisional*
    # report + a HITL review packet; it no longer halts at the checkpoint.
    # HITL cases are deferred (marked PROVISIONAL_PENDING_HITL) and resolved
    # later via scripts/finalize_hitl.py after human review.
    g.add_edge("hitl_checkpoint", "phase_6")
    g.add_edge("phase_6", END)
    return g.compile(checkpointer=checkpointer)
