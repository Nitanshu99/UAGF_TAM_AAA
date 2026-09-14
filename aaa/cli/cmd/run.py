"""Part 3 of the former ``cli`` module (auto-split)."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from aaa.cli.logger import _load_json, _summarise, logger  # noqa: F401
from aaa.cli.seed.intake import _seed_intake  # noqa: F401


async def _cmd_run(args: argparse.Namespace) -> int:
    # Late imports so ``--help`` works even if optional deps are missing.
    from aaa.agents.intake_validator import IntakeValidator, IntakeValidatorError
    from aaa.agents.tier1.orchestrator import Orchestrator
    from aaa.agents.tier1.regulatory_rag import build_regulatory_rag
    from aaa.platform.evidence import EvidenceStore

    intake_dir = pathlib.Path(args.intake_dir).resolve()
    if not intake_dir.is_dir():
        print(f"[cli] intake-dir not found: {intake_dir}", file=sys.stderr)
        return 3

    store = EvidenceStore()
    dispatch = _seed_intake(store, intake_dir, args)

    # ── IntakeValidator (Stage 0 A/B/C) ──────────────────────────────────────
    print(f"[cli] IntakeValidator: engagement={args.engagement_id}", file=sys.stderr)
    intake = IntakeValidator(evidence_store=store)
    try:
        initial_state = await intake.process(dispatch)
    except IntakeValidatorError as exc:
        print(f"[cli] IntakeValidator failed at stage {exc.stage}: {exc.reason}",
              file=sys.stderr)
        return 2

    # ── Orchestrator (Plan → P1 → P2/3/4 → P5 → CM → HITL → P6) ──────────────
    print("[cli] Orchestrator: running full workflow", file=sys.stderr)
    orch = Orchestrator(evidence_store=store, regulatory_rag=build_regulatory_rag())
    final = await orch.run(dict(initial_state))

    # ── Persist customer deliverables (audit_state + T17 + T18) ──────────────
    from aaa.data.writer import save_customer_artefacts
    cdir = save_customer_artefacts(args.engagement_id, final, store)
    if cdir is not None:
        print(f"[cli] customer artefacts written to {cdir}", file=sys.stderr)

    # ── Emit summary ────────────────────────────────────────────────────────
    summary = _summarise(final)
    text = json.dumps(summary, indent=2, default=str)
    print(text)

    if args.output_file:
        out = pathlib.Path(args.output_file).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"[cli] summary written to {out}", file=sys.stderr)

    return 0
