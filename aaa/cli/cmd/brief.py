"""``brief`` sub-command: write the client brief from a saved audit state.

The brief is produced at the end of a run like every other deliverable. This
command exists for the runs that finished before it did, and for rewording an
existing one without re-auditing: it reads ``<id>_audit_state.json`` — which is
the complete final state, verdicts and findings included — and writes
``<id>_client_report.md`` beside it. It makes LLM calls; it makes no audit
decisions, and it cannot change a verdict.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from aaa.cli.cmd.report.store import store_or_memory, try_store
from aaa.data.paths import customer_dir

if TYPE_CHECKING:
    from aaa.platform.evidence import EvidenceStore


async def _write_one(state_path: Path, store: EvidenceStore | None) -> bool:
    """Write the brief for one saved engagement; return whether it was written.

    Without a durable store the brief is still written — over an empty
    in-memory store, so figures simply do not resolve — rather than handing
    the agent ``None``.
    """
    import json

    from aaa.agents.tier2.client_brief import ClientBriefAgent
    engagement_id = state_path.name[: -len("_audit_state.json")]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if not state.get("compliance_matrix"):
        print(f"[brief] {engagement_id}: the saved state holds no compliance "
              f"matrix, so there is no result to explain — skipped.", file=sys.stderr)
        return False
    agent = ClientBriefAgent(evidence_store=store_or_memory(store), regulatory_rag=_try_rag())
    markdown = await agent.build_brief(state, engagement_id)
    out = state_path.parent / f"{engagement_id}_client_report.md"
    out.write_text(markdown, encoding="utf-8")
    print(f"[brief] wrote {out.parent.name}/{out.name} ({len(markdown):,} characters)")
    return True


def _try_rag() -> object | None:
    """Open the regulatory corpus, or ``None`` — the brief then cites unquoted."""
    try:
        from aaa.agents.tier1.regulatory_rag import RegulatoryRAG
        return RegulatoryRAG()
    except Exception as exc:  # noqa: BLE001 — degrade, but say so
        print(f"[brief] regulatory corpus unavailable ({type(exc).__name__}: {exc}); "
              f"articles will be named but their text not quoted.", file=sys.stderr)
        return None


async def _run(folders: list[Path]) -> int:
    """Write a brief for every saved engagement in *folders*."""
    store = try_store()
    written = 0
    for folder in folders:
        if not folder.is_dir():
            print(f"[brief] company folder not found: {folder}", file=sys.stderr)
            return 3
        for state_path in sorted(folder.glob("*_audit_state.json")):
            written += await _write_one(state_path, store)
    print(f"[brief] {written} brief(s) written")
    return 0 if written else 3


def _cmd_brief(args: argparse.Namespace) -> int:
    """Run the brief writer per the parsed arguments.

    :param args: Namespace with ``company`` (name, or ``None`` for every folder).
    :returns: Process exit code (0 = at least one brief written).
    """
    root = customer_dir("")
    folders = ([customer_dir(args.company)] if args.company
               else sorted(p for p in root.iterdir() if p.is_dir()))
    return asyncio.run(_run(folders))
