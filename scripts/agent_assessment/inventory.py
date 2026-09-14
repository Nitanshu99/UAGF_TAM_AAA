"""The run's call inventory: one table row per captured call."""
from __future__ import annotations


def inventory(calls: list[dict]) -> str:
    """Render the per-call inventory table (time, agent, status, tokens, latency)."""
    rows = ["| # | time (UTC) | agent | status | in-tok | out-tok | latency |",
            "|---|---|---|---|---|---|---|"]
    for c in calls:
        t = (c["ts"] or "")[11:19]
        rows.append(
            f"| {c['seq']:03d} | {t} | {c['agent']} | "
            f"{'ok' if c['status'] == 'ok' else '**error**'} | "
            f"{c['prompt_tokens'] or 0:,} | {c['completion_tokens'] or 0:,} | "
            f"{(c['latency_ms'] or 0)/1000:.1f} s |")
    return "\n".join(rows)


__all__ = ["inventory"]
