"""The six phase runners, one module each: ``p1`` … ``p6``.

Deliberately no eager re-exports here. ``p6`` imports the Phase 6 declaration
summary, which in turn reads the earlier phases, so an ``__init__`` that
imported ``p1`` … ``p6`` in sequence re-entered ``p6`` while it was still being
initialised (circular import). The public surface is the parent package:
``from aaa.agents.tier1.phases.phase_runners import run_phase_1 … run_phase_6``.
"""
