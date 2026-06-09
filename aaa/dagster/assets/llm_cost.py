"""
aaa.dagster.assets.llm_cost — LLM cost summary asset.

Reads the JSONL audit log produced by BaseAgent.acompletion and emits
an aggregated cost/token summary as a Dagster materialisation.

This asset is a "monitoring" asset — it runs after all phase assets
but does not depend on them directly.  It reads the audit file directly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dagster import AssetExecutionContext, MetadataValue, asset


_AUDIT_JSONL = Path("logs/audit/llm_audit.jsonl")


def _read_audit_records() -> list[dict[str, Any]]:
    if not _AUDIT_JSONL.exists():
        return []
    records = []
    with _AUDIT_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


@asset(
    name="llm_cost_summary",
    group_name="observability",
    description="Aggregate LLM token usage and estimated cost from the audit JSONL log.",
)
def llm_cost_summary_asset(context: AssetExecutionContext) -> dict[str, Any]:
    """Read llm_audit.jsonl and emit token / cost aggregates as Dagster metadata."""
    records = _read_audit_records()
    total_calls = len(records)
    ok_calls = sum(1 for r in records if r.get("status") == "ok")
    error_calls = total_calls - ok_calls
    total_prompt_tokens = sum(r.get("prompt_tokens", 0) or 0 for r in records)
    total_completion_tokens = sum(r.get("completion_tokens", 0) or 0 for r in records)
    total_cost = sum(r.get("estimated_cost_usd", 0.0) or 0.0 for r in records)

    # Per-agent breakdown
    by_agent: dict[str, dict[str, Any]] = {}
    for rec in records:
        agent = rec.get("agent_name") or rec.get("agent", "unknown")
        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        by_agent[agent]["calls"] += 1
        by_agent[agent]["tokens"] += (rec.get("total_tokens", 0) or 0)
        by_agent[agent]["cost_usd"] += (rec.get("estimated_cost_usd", 0.0) or 0.0)

    context.add_output_metadata({
        "total_llm_calls": MetadataValue.int(total_calls),
        "ok_calls": MetadataValue.int(ok_calls),
        "error_calls": MetadataValue.int(error_calls),
        "total_prompt_tokens": MetadataValue.int(total_prompt_tokens),
        "total_completion_tokens": MetadataValue.int(total_completion_tokens),
        "estimated_total_cost_usd": MetadataValue.float(round(total_cost, 6)),
        "agent_breakdown": MetadataValue.json(by_agent),
    })

    return {
        "total_calls": total_calls,
        "ok_calls": ok_calls,
        "error_calls": error_calls,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "estimated_total_cost_usd": total_cost,
        "by_agent": by_agent,
    }
