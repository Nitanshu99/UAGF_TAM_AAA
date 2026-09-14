"""Compact, reviewable digest of an extracted run — the reading aid for the analysis.

``gen_report.py`` puts every call's *full* assembled input and raw output into the
delivered markdown, which is the point of the document. That same fullness makes the
run unreadable while the judgement is being formed: one case is ~50 calls of ~10,000
prompt tokens each.

This renders what an assessor actually needs to triage a call — which prompt sections
were assembled, what the payload carried, whether retrieval reached it, what the model
replied — and flags the calls that warrant reading in full.

Usage: python -m scripts.agent_assessment.digest_calls <calls.json> [--full SEQ[,SEQ...]]
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from scripts.agent_assessment.shapes import (
    SHORT_REPLY,
    _digest,
    _payload_shape,
    _retrieval,
    _sections,
)


def digest(call: dict[str, Any]) -> str:
    """One call, rendered for triage."""
    lines = [
        f"── #{call['seq']:03d} {call['agent']} · {call['status']} · "
        f"{(call['latency_ms'] or 0) / 1000:.1f}s · "
        f"{call['prompt_tokens'] or 0:,}→{call['completion_tokens'] or 0:,} tok "
        f"· eng={call['engagement_id'] or '(none)'}"
    ]
    for message in call["messages"]:
        role = str(message.get("role", "?")).upper()
        content = str(message.get("content", ""))
        head = f"   {role} {len(content):,}ch sha={_digest(content)}"
        if role == "SYSTEM":
            lines += [head, f"      sections: {' | '.join(_sections(content)) or '(none)'}"]
        else:
            lines += [head,
                      f"      retrieval: {_retrieval(content)}",
                      f"      payload: {', '.join(_payload_shape(content))}"]
    reply = call["response_text"]
    flag = "  ⚠ SHORT" if len(reply) < SHORT_REPLY and call["status"] == "ok" else ""
    lines.append(f"   REPLY {len(reply):,}ch{flag}")
    lines.append("      " + (reply if len(reply) <= 600 else
                             reply[:400] + "\n      …\n      " + reply[-160:]).replace(
                                 "\n", "\n      "))
    return "\n".join(lines)




if __name__ == "__main__":  # pragma: no cover - CLI entry point
    from scripts.agent_assessment.digest_cli import main

    seqs: set[int] = set()
    if "--full" in sys.argv:
        seqs = {int(s) for s in sys.argv[sys.argv.index("--full") + 1].split(",")}
    main(Path(sys.argv[1]), seqs)
