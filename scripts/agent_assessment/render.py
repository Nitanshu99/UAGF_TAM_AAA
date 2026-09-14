"""Rendering one captured call, and the run's call inventory, as Markdown."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from scripts.agent_assessment.inventory import inventory
from scripts.agent_assessment.metrics_block import _fence, _metrics


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("analysis", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load analysis module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def render_call(c: dict, title: str, note: str) -> str:
    """Render one LLM call as a Markdown section: metrics, verbatim input/output, assessment."""
    seq = c["seq"]
    parts = [f"### Call #{seq:03d} — {c['agent']} — {title}", "", _metrics(c), ""]
    parts += ["#### Exact LLM input (fully assembled, verbatim)", ""]
    for m in c["messages"]:
        role = str(m.get("role", "?")).upper()
        content = str(m.get("content", ""))
        parts += [f"**`{role}` message — {len(content):,} chars**", "",
                  _fence(content), ""]
    parts += ["#### Exact LLM output (verbatim)", ""]
    if c["status"] == "error":
        parts += ["Call **failed**. Raised:", "", _fence(str(c.get("error", ""))), ""]
    else:
        parts += [f"**{len(c['response_text']):,} chars**", "",
                  _fence(c["response_text"]), ""]
    parts += ["#### Assessment", "", note.strip() or "_(pending)_", "", "---", ""]
    return "\n".join(parts)


__all__ = ["_fence", "_load", "_metrics", "inventory", "render_call"]
