"""Agent foundations: the BaseAgent ABC and typed message contracts (§5.2)."""
from __future__ import annotations

from aaa.agents.base.agent import BaseAgent
from aaa.agents.base.contracts import Critique, Dispatch, IntakeDispatch, Report
from aaa.agents.base.json_utils import _loads_lenient  # noqa: F401 (test access)

__all__ = ["BaseAgent", "Critique", "Dispatch", "IntakeDispatch", "Report"]
