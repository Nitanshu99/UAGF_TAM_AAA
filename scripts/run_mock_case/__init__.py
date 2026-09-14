"""Run a mock engagement end-to-end through the real audit pipeline.

Self-contained: just run it.  The script

- works from any directory (chdirs to the repo root),
- loads ``.env`` so provider creds reach LiteLLM,
- auto-wires the *correct* CGSA fixture for the chosen case,
- reads every other knob from the environment (no flags),
- runs the full IntakeValidator → Orchestrator pipeline,
- prints the verdict + compliance matrix + findings,
- reports whether the LLM harness actually fired (ok vs error per agent),
- and saves T17 / T18 / audit-state JSON to ``data/customer/<company>/``.

Usage::

    python -m scripts.run_mock_case 01_finclear_gmbh

Environment (all optional; set in your shell or .env):
``OPENAI_API_KEY`` (creds for the backend serving gpt-5.x, plus
``OPENAI_API_BASE`` if a gateway), ``AAA_DISABLE_FLEX=true`` (send no
``service_tier="flex"`` for backends without Flex).

``CGSA_FIXTURE_DIR`` is set automatically from ``mock/<case>/cgsa`` —
do not set it by hand.
"""
from __future__ import annotations

from scripts.run_mock_case.runner import main

__all__ = ["main"]
