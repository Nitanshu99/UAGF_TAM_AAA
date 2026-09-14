"""LLM-harness reporting: did the agents actually call the model?"""
from __future__ import annotations

import json
from collections import Counter

from scripts.run_mock_case.env import AUDIT_LOG


def audit_lines() -> list[str]:
    """Return the current lines of the LLM audit log (empty when absent)."""
    return AUDIT_LOG.read_text("utf-8").splitlines() if AUDIT_LOG.exists() else []


def report_harness(new_lines: list[str]) -> None:
    """Summarise the LLM calls made during this run.

    :param new_lines: Audit-log lines appended during the run.
    """
    calls = []
    for line in new_lines:
        try:
            calls.append(json.loads(line))
        except Exception:  # pylint: disable=broad-exception-caught
            pass
    ok = [c for c in calls if c.get("status") == "ok"]
    errors = [c for c in calls if c.get("status") == "error"]
    print("\nLLM harness:")
    print(f"  calls: {len(ok)} ok, {len(errors)} error")
    if ok:
        models = Counter(c.get("served_model") or c.get("model") for c in ok)
        print("  models used: " + ", ".join(f"{m}×{n}" for m, n in models.items()))
    if errors:
        by_agent = Counter(c.get("agent") for c in errors)
        sample = next((c.get("error", "") for c in errors), "")
        print("  errors by agent: " + ", ".join(f"{a}×{n}" for a, n in by_agent.items()))
        print(f"  first error: {str(sample)[:160]}")
    if not calls:
        print("  ⚠ no LLM calls recorded — check OPENAI_API_KEY / model routing")
