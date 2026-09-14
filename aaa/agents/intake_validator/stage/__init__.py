"""The IntakeValidator's two validation stages.

``a`` validates the Stage A declaration, ``b`` the Stage B dossier; the agent
runs them in that order and merges what they return.
"""
from __future__ import annotations

from aaa.agents.intake_validator.stage.a import run_stage_a
from aaa.agents.intake_validator.stage.b import run_stage_b

__all__ = ["run_stage_a", "run_stage_b"]
