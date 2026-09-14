"""The per-call metrics block: latency, tokens, cost and attempts."""
from __future__ import annotations


def _fence(text: str) -> str:
    """Wrap *text* in a fence long enough to survive any backticks inside it."""
    n = 3
    while "`" * n in text:
        n += 1
    tick = "`" * n
    return f"{tick}text\n{text}\n{tick}"
def _metrics(c: dict) -> str:
    cost = c.get("cost_usd")
    return "\n".join([
        "| field | value |",
        "|---|---|",
        f"| timestamp (UTC) | `{c['ts']}` |",
        f"| agent | **{c['agent']}** |",
        f"| model | `{c['model']}` |",
        f"| engagement_id on record | `{c['engagement_id']}` |",
        f"| status | `{c['status']}` |",
        f"| latency | {(c['latency_ms'] or 0)/1000:.1f} s |",
        f"| prompt / completion / total tokens | "
        f"{c['prompt_tokens'] or 0:,} / {c['completion_tokens'] or 0:,} / "
        f"{c['total_tokens'] or 0:,} |",
        f"| cost (USD) | {cost if cost is not None else 'n/a'} |",
    ])


__all__ = ["_fence", "_metrics"]
