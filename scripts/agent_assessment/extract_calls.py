"""Extract one mock-case run from the LLM audit trail into per-call records.

Usage: python -m scripts.agent_assessment.extract_calls <boundary_line_count> <out.json> [end_line]

Everything appended to logs/audit/llm_audit.jsonl after <boundary_line_count>
belongs to the run under assessment.  Pass *end_line* when several cases were run
in succession into the same append-only trail: the slice is then ``[boundary,
end_line)``, which is exactly the pair ``run_all_cases.sh`` records per case.
Without it the slice runs to the end of the file, which is only unambiguous when
the assessed run is the last one in the trail.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

AUDIT = Path("logs/audit/llm_audit.jsonl")


def main(boundary: int, out: Path, end: int | None = None) -> None:
    """Slice one run out of the audit trail and write its per-call records.

    :param boundary: Audit-trail line count taken immediately before the run.
    :param out: Where to write ``calls.json``.
    :param end: Line count immediately after the run; ``None`` reads to EOF.
    """
    lines = AUDIT.read_text("utf-8").splitlines()[boundary:end]
    calls = []
    for seq, line in enumerate(lines, start=1):
        rec = json.loads(line)
        msgs = rec.get("messages") or []
        calls.append({
            "seq": seq,
            "ts": rec.get("ts"),
            "engagement_id": rec.get("engagement_id"),
            "agent": rec.get("agent"),
            "model": rec.get("model"),
            "status": rec.get("status"),
            "latency_ms": rec.get("latency_ms"),
            "prompt_tokens": rec.get("prompt_tokens"),
            "completion_tokens": rec.get("completion_tokens"),
            "total_tokens": rec.get("total_tokens"),
            "cost_usd": rec.get("estimated_cost_usd"),
            "error": rec.get("error"),
            "messages": msgs,
            "response_text": rec.get("response_text", ""),
        })
    out.write_text(json.dumps(calls, indent=1, ensure_ascii=False), "utf-8")

    print(f"{len(calls)} calls -> {out}")
    for c in calls:
        roles = "/".join(m.get("role", "?") for m in c["messages"])
        chars = sum(len(str(m.get("content", ""))) for m in c["messages"])
        print(f"  #{c['seq']:03d} {c['ts'] or '-':32s} {c['agent'] or '?':20s} "
              f"{c['status']:5s} eng={c['engagement_id'] or '-':24s} "
              f"roles={roles:14s} in={chars:7d}ch out={len(c['response_text']):6d}ch "
              f"tok={c['total_tokens'] or 0:7d} lat={(c['latency_ms'] or 0)/1000:7.1f}s")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]),
         int(sys.argv[3]) if len(sys.argv) > 3 else None)
