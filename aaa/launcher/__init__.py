"""aaa.launcher — one-command start-up for the AAA platform.

Starts every configured component of the stack (Docker infrastructure,
database migrations, FastAPI backend, Streamlit UI) from a single entry
point::

    python -m aaa            # or simply:  aaa

Component selection and ports are driven by ``.env`` — see
:mod:`aaa.launcher.config` for the recognised variables.
"""
from __future__ import annotations

from aaa.launcher.cli import main

__all__ = ["main"]
