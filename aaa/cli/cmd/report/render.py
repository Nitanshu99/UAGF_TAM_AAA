"""``report`` sub-command: regenerate customer PDFs from persisted deliverables.

Walks ``data/customer/<company>/`` folders, loads each engagement's
``*_audit_state.json`` / ``*_T17.json`` / ``*_T18.json``, and re-renders
``<engagement_id>_audit_report.pdf`` in place. Pure rendering — no LLM calls.
Figures come from the evidence store when one is reachable (see
:mod:`aaa.cli.cmd.report.store`) and are skipped, with a reason, when not.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aaa.cli.cmd.report.store import try_store
from aaa.data.paths import customer_dir


def _load(path: Path) -> dict:
    """Read one JSON deliverable, returning ``{}`` when absent/corrupt.

    :param path: Deliverable file path.
    :type path: Path
    :returns: Parsed payload or an empty dict.
    :rtype: dict
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _render_company(folder: Path, store: object | None) -> int:
    """Render one PDF per engagement found in *folder*; return the count."""
    from aaa.tools.report_render.pdf.builder import build_pdf
    rendered = 0
    for state_path in sorted(folder.glob("*_audit_state.json")):
        engagement_id = state_path.name[: -len("_audit_state.json")]
        t18 = _load(folder / f"{engagement_id}_T18.json")
        if not t18:
            print(f"[report] {engagement_id}: no T18 payload — skipped", file=sys.stderr)
            continue
        pdf = build_pdf(t18, _load(folder / f"{engagement_id}_T17.json"),
                        _load(state_path), store=store)
        (folder / f"{engagement_id}_audit_report.pdf").write_bytes(pdf)
        print(f"[report] wrote {folder.name}/{engagement_id}_audit_report.pdf "
              f"({len(pdf):,} bytes)")
        rendered += 1
    return rendered


def _cmd_report(args: argparse.Namespace) -> int:
    """Run the batch report renderer per the parsed arguments.

    :param args: Namespace with ``company`` (name or ``None`` for all).
    :type args: argparse.Namespace
    :returns: Process exit code (0 = at least one PDF written).
    :rtype: int
    """
    root = customer_dir("")  # Path / "" is a no-op → the customer root itself
    folders = ([customer_dir(args.company)] if args.company
               else sorted(p for p in root.iterdir() if p.is_dir()))
    store = try_store()
    total = 0
    for folder in folders:
        if not folder.is_dir():
            print(f"[report] company folder not found: {folder}", file=sys.stderr)
            return 3
        total += _render_company(folder, store)
    print(f"[report] {total} PDF(s) generated")
    return 0 if total else 3
