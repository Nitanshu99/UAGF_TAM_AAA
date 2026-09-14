"""``report`` sub-command: regenerate customer PDFs from persisted deliverables.

Split into :mod:`render` (walk the customer folders, rebuild each PDF) and
:mod:`store` (decide whether evidence figures are resolvable at all). The
historic import path ``aaa.cli.cmd.report._cmd_report`` is preserved for
:mod:`aaa.cli.build_parser`.
"""
from aaa.cli.cmd.report.render import _cmd_report, _load, _render_company  # noqa: F401
from aaa.cli.cmd.report.store import store_or_memory, try_store  # noqa: F401

__all__ = ["_cmd_report", "_load", "_render_company", "store_or_memory", "try_store"]
