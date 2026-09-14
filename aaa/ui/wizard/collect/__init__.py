"""Stage A / Stage B payload collectors (compatibility re-exports)."""
from __future__ import annotations

from aaa.ui.wizard.collect.stage.a import collect_stage_a
from aaa.ui.wizard.collect.stage.b import collect_stage_b

__all__ = ["collect_stage_a", "collect_stage_b"]
