"""Stage 2's numbered steps, grouped by what has to be true when they run.

``prepare`` (steps 3–8) makes the stack exist; ``serve`` (steps 9–10) starts the
app and the browser; ``summary`` prints where everything is. ``main`` sequences
them and owns the clean-up.
"""
from scripts.bootstrap.orchestrate.common import PYTHON, TOTAL, Children
from scripts.bootstrap.orchestrate.prepare import mock_overrides, prepare
from scripts.bootstrap.orchestrate.serve import serve_and_browse
from scripts.bootstrap.orchestrate.summary import summary

__all__ = ["Children", "PYTHON", "TOTAL", "mock_overrides", "prepare", "serve_and_browse", "summary"]
