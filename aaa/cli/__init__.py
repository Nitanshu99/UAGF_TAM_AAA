"""aaa.cli — Command-line entry point for the AAA pipeline (§11).

Usage::

    python -m aaa.cli run         --engagement-id eng-uci-german-credit-001         --intake-dir scripts/fixtures/uci_german_credit         [--cgsa-fixture-dir scripts/fixtures/cgsa]         [--output-file out/eng-uci-german-credit-001.json]

The ``run`` subcommand wires ``IntakeValidator → Orchestrator → ReportArchitect``
in a single process, prints a JSON summary of artefact URIs / KPIs / final
verdict to stdout, and (optionally) writes the same summary to ``--output-file``.

Exit codes:
    0 — engagement reached a final verdict (PASS / PASS_WITH_OBSERVATIONS / FAIL).
    2 — IntakeValidator gate failure (intake_completeness_score < 0.80).
    3 — Pipeline raised an unrecoverable error."""
from aaa.cli.build_parser import _build_parser, main  # noqa: F401
from aaa.cli.cmd.run import _cmd_run  # noqa: F401
from aaa.cli.logger import _load_json, _summarise, logger  # noqa: F401
from aaa.cli.seed.intake import _seed_intake  # noqa: F401

__all__ = [
    'logger', '_load_json', '_summarise', '_seed_intake', '_cmd_run', '_build_parser',
    'main',
]
