"""Orchestrator — Tier-1 lead agent (§3.1 #1, §6).

Thin coordinator that wires the 9-node LangGraph StateGraph; all node
implementations live in :mod:`aaa.agents.tier1.phases`::

  stage_0 → plan → phase_1 → route → parallel_phases
          → phase_5 → compliance_matrix → hitl_checkpoint → phase_6
"""
from __future__ import annotations

from aaa.agents.tier1.orchestrator.agent import Orchestrator

__all__ = ["Orchestrator"]
