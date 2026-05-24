"""
trajectory_audit — Audit of agentic tool-call sequences (§4.4).

Production path:  Langfuse trace parser.
Offline/fallback: deterministic analysis of a trace sample.

Usage
-----
    from src.tools.trajectory_audit import trajectory_audit
    results = trajectory_audit(trace_data)
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)


def trajectory_audit(
    traces: Sequence[dict[str, Any]] | None = None,
    permitted_tools: Sequence[str] | None = None,
) -> dict[str, Any]:
    """
    Analyze agent trajectories for tool-use compliance.

    Parameters
    ----------
    traces:
        List of trace dicts (e.g. from Langfuse).
    permitted_tools:
        List of tool names the agent is allowed to call.

    Returns
    -------
    dict matching the T16 ``trajectory_audit`` sub-schema.
    """
    if not traces:
        return {
            "total_trajectories": 0,
            "compliant_trajectories": 0,
            "violation_count": 0,
            "violations": [],
        }

    total = len(traces)
    violations = []
    
    for idx, trace in enumerate(traces):
        trace_id = trace.get("id", f"trace_{idx}")
        steps = trace.get("steps", [])
        
        for step_idx, step in enumerate(steps):
            if step.get("type") == "tool_call":
                tool_name = step.get("tool_name")
                
                # Check 1: Unauthorised tool
                if permitted_tools and tool_name not in permitted_tools:
                    violations.append({
                        "trajectory_id": trace_id,
                        "violation_type": "unauthorised_tool",
                        "description": f"Agent called unauthorised tool: {tool_name}",
                        "step_index": step_idx,
                    })
                
                # Check 2: Recursive tool calling (heuristic)
                if step.get("depth", 0) > 5:
                    violations.append({
                        "trajectory_id": trace_id,
                        "violation_type": "excessive_depth",
                        "description": "Agent exceeded tool-call depth limit (potential loop).",
                        "step_index": step_idx,
                    })

    compliant = total - len({v["trajectory_id"] for v in violations})
    
    return {
        "total_trajectories": total,
        "compliant_trajectories": max(0, compliant),
        "violation_count": len(violations),
        "violations": violations,
    }
