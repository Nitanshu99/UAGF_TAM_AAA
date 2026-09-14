"""Steps 3–8: everything that has to be true before the app starts."""
from __future__ import annotations

import argparse
import os

from scripts.bootstrap.environment import child_env
from scripts.bootstrap.orchestrate.common import PYTHON, TOTAL, Children
from scripts.bootstrap.paths import ENV_EXAMPLE, ENV_FILE, REPO_ROOT
from scripts.bootstrap.steps.browsers import install_chromium
from scripts.bootstrap.steps.bundles import BUNDLES, unpack
from scripts.bootstrap.steps.docker import migrate, stack_up
from scripts.bootstrap.steps.dotenv import configure_env
from scripts.bootstrap.steps.ingest import ingest_corpus
from scripts.bootstrap.steps.ports import check_ports
from scripts.bootstrap.steps.prereqs import check_bundles, check_docker
from scripts.setup.console import ok, step


def mock_overrides(values: dict[str, str], base: str) -> dict[str, str]:
    """The environment that routes a ``--mock-llm`` run to the stub.

    The Prometheus counters go to their own directory: multiprocess counter
    files persist across runs of a checkout, so a smoke test's refused calls
    would otherwise sit in the real dashboards' error ratio for good.

    :param values: The ``.env`` values (for a key, if one is set).
    :param base: The stub's API root.
    :returns: Overrides for every process the bootstrap starts.
    """
    return {"OPENROUTER_API_BASE": base,
            "OPENROUTER_API_KEY": values.get("OPENROUTER_API_KEY") or "sk-or-v1-mock-no-spend",
            "PROMETHEUS_MULTIPROC_DIR": str(REPO_ROOT / "logs" / "metrics-mock")}


def _start_stub(values: dict[str, str], children: Children) -> dict[str, str]:
    """Start the no-spend stub; return the overrides that route the stack to it."""
    from scripts.bootstrap.stub.process import start_stub

    children["stub"], base = start_stub(PYTHON)
    ok(f"--mock-llm: embeddings and chat go to a local stub at {base} — nothing is spent")
    return mock_overrides(values, base)


def prepare(args: argparse.Namespace, children: Children) -> None:
    """Run steps 3–8 in order.

    :param args: The parsed command line.
    :param children: Where the stub process is recorded when ``--mock-llm`` is set.
    """
    step(3, TOTAL, "Prerequisites: Docker, and the two bundles")
    check_docker()
    zips = check_bundles(args.zip_dir)
    step(4, TOTAL, "Configure .env — one OpenRouter key for agents and embeddings")
    values = configure_env(ENV_FILE, ENV_EXAMPLE, args.openrouter_key, args.mock_llm)
    overrides = _start_stub(values, children) if args.mock_llm else {}
    os.environ.update(child_env(ENV_FILE, overrides))
    step(5, TOTAL, "Unpack mariposa.zip and corpus.zip")
    for bundle in BUNDLES:
        written, kept = unpack(zips[bundle.name], bundle)
        ok(f"{bundle.name} → {bundle.target.relative_to(REPO_ROOT)}/  "
           f"({written} written, {kept} already there)")
    step(6, TOTAL, "Docker stack: core services + observability + service UIs")
    check_ports(os.environ)
    stack_up(args.wait_timeout)
    migrate(PYTHON)
    step(7, TOTAL, "Chromium for Playwright")
    install_chromium(PYTHON)
    step(8, TOTAL, "Regulatory corpus → Qdrant")
    ingest_corpus(PYTHON, args.skip_ingest, args.reset_corpus)


__all__ = ["mock_overrides", "prepare"]
