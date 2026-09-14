"""Orchestrates the probe: bootstrap, one mock call, then the sink checks."""
from __future__ import annotations

import asyncio
import os
import sys
import uuid

from scripts.run_mock_case.env import REPO_ROOT, load_dotenv_file


def bootstrap() -> None:
    """Prepare the process before any ``aaa`` import (env is read at import time)."""
    os.chdir(REPO_ROOT)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    load_dotenv_file(REPO_ROOT / ".env")


def main() -> int:
    """Run the probe and print one line per sink.

    :returns: 0 when every reachable sink saw the call, 1 otherwise.
    """
    bootstrap()
    from scripts.obs_probe.checks import run_checks
    from scripts.obs_probe.llm_call import probe_call

    probe_id = f"obs-probe-{uuid.uuid4().hex[:8]}"
    print(f"probe id: {probe_id}  (one mock LLM call, nothing billed)")
    record = asyncio.run(probe_call(probe_id))
    print(f"call made: agent={record['agent']} model={record['model']} "
          f"engagement_id={record['engagement_id']} reply={record['content']!r}\n")

    results = run_checks(probe_id, record)
    for result in results:
        tag = "OK  " if result.ok else ("SKIP" if result.optional else "FAIL")
        print(f"[{tag}] {result.name}: {result.detail}")
    failed = [r for r in results if not r.ok and not r.optional]
    print(f"\n{len(results) - len(failed)}/{len(results)} sinks confirmed"
          + (f" — {len(failed)} FAILED" if failed else ""))
    return 1 if failed else 0
