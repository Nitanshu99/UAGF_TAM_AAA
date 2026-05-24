"""
aaa.cli — Command-line entry point for the AAA pipeline (§11).

Usage::

    python -m aaa.cli run \
        --engagement-id eng-uci-german-credit-001 \
        --intake-dir scripts/fixtures/uci_german_credit \
        [--cgsa-fixture-dir scripts/fixtures/cgsa] \
        [--output-file out/eng-uci-german-credit-001.json] \
        [--offline]

The ``run`` subcommand wires ``IntakeValidator → Orchestrator → ReportArchitect``
in a single process, prints a JSON summary of artefact URIs / KPIs / final
verdict to stdout, and (optionally) writes the same summary to ``--output-file``.

Exit codes:
    0 — engagement reached a final verdict (PASS / PASS_WITH_OBSERVATIONS / FAIL).
    2 — IntakeValidator gate failure (intake_completeness_score < 0.80).
    3 — Pipeline raised an unrecoverable error.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import pathlib
import sys
from typing import Any

logger = logging.getLogger("aaa.cli")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def _summarise(final: dict) -> dict:
    """Return a stdout-friendly summary of the final AuditState."""
    artefacts = final.get("phase_artefacts", {}) or {}
    return {
        "engagement_id": final.get("engagement_id"),
        "final_verdict": final.get("final_verdict"),
        "intake_completeness_score": final.get("intake_completeness_score"),
        "completeness_score": final.get("completeness_score"),
        "regulatory_coverage_pct": final.get("regulatory_coverage_pct"),
        "art43_decision": final.get("art43_decision"),
        "hitl_required": final.get("hitl_required", False),
        "hitl_reason": final.get("hitl_reason"),
        "phase_artefacts": {
            tid: (ref.get("uri") if isinstance(ref, dict) else None)
            for tid, ref in artefacts.items()
        },
        "compliance_matrix": final.get("compliance_matrix", {}),
        "blocking_findings_count": len(final.get("blocking_findings") or []),
        "positive_findings_count": len(final.get("positive_findings") or []),
    }


# ---------------------------------------------------------------------------
# `run` subcommand
# ---------------------------------------------------------------------------

async def _cmd_run(args: argparse.Namespace) -> int:
    # Late imports so ``--help`` works even if optional deps are missing.
    from aaa.agents.base import IntakeDispatch
    from aaa.agents.intake_validator import (
        IntakeValidator,
        IntakeValidatorError,
    )
    from aaa.agents.tier1.orchestrator import Orchestrator
    from aaa.platform.evidence import EvidenceStore

    intake_dir = pathlib.Path(args.intake_dir).resolve()
    if not intake_dir.is_dir():
        print(f"[cli] intake-dir not found: {intake_dir}", file=sys.stderr)
        return 3

    store = EvidenceStore()

    # ── Seed Stage A/B/C raw payloads into the EvidenceStore ─────────────────
    stage_a = _load_json(intake_dir / "stage_a.json")
    stage_b = _load_json(intake_dir / "stage_b.json")
    stage_c_path = intake_dir / "stage_c.json"
    stage_c = _load_json(stage_c_path) if stage_c_path.exists() else None

    stage_a_uri = store.store_artefact(
        args.engagement_id, "stage_a_raw", "stage_a_raw", stage_a, "cli")
    stage_b_uri = store.store_artefact(
        args.engagement_id, "stage_b_raw", "stage_b_raw", stage_b, "cli")
    stage_c_uri = (
        store.store_artefact(
            args.engagement_id, "stage_c_raw", "stage_c_raw", stage_c, "cli")
        if stage_c is not None else None
    )

    dispatch: IntakeDispatch = {
        "engagement_id": args.engagement_id,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": args.annex_iv_schema_version,
    }

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
    orch = Orchestrator(evidence_store=store)
    final = await orch.run(dict(initial_state))

    # ── Emit summary ────────────────────────────────────────────────────────
    summary = _summarise(final)
    text = json.dumps(summary, indent=2, default=str)
    print(text)

    if args.output_file:
        out = pathlib.Path(args.output_file).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n")
        print(f"[cli] summary written to {out}", file=sys.stderr)

    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aaa.cli",
        description="AAA — Autonomous AI Auditor CLI (§11).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a full audit engagement.")
    run_p.add_argument("--engagement-id", required=True,
                       help="Unique engagement identifier (UUID or slug).")
    run_p.add_argument("--intake-dir", required=True,
                       help="Directory containing stage_a.json / stage_b.json "
                            "[/ stage_c.json] payloads.")
    run_p.add_argument("--cgsa-fixture-dir", default=None,
                       help="Optional CGSA fixture directory "
                            "(sets CGSA_FIXTURE_DIR for offline GovernanceAgent).")
    run_p.add_argument("--output-file", default=None,
                       help="Optional path to write the JSON summary.")
    run_p.add_argument("--annex-iv-schema-version", default="1.0.0",
                       help="Annex IV schema version (default: 1.0.0).")
    run_p.add_argument("--offline", action="store_true",
                       help="Force AAA_OFFLINE_MODE=true for the run.")
    run_p.add_argument("--log-level", default="WARNING",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level))

    if args.offline:
        os.environ["AAA_OFFLINE_MODE"] = "true"
    if args.cgsa_fixture_dir:
        os.environ["CGSA_FIXTURE_DIR"] = str(
            pathlib.Path(args.cgsa_fixture_dir).resolve()
        )

    if args.command == "run":
        try:
            return asyncio.run(_cmd_run(args))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline crashed: %s", exc)
            print(f"[cli] pipeline error: {exc}", file=sys.stderr)
            return 3
    return 3


if __name__ == "__main__":
    sys.exit(main())
