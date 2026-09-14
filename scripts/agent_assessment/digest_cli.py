"""The digest_calls command line."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.agent_assessment.digest_calls import digest


def main(calls_path: Path, full: set[int]) -> None:
    """Print a digest of every call, or the verbatim text of the ones named.

    :param calls_path: ``calls.json`` written by ``extract_calls.py``.
    :param full: Sequence numbers to print in full instead of digesting.
    """
    calls = json.loads(calls_path.read_text("utf-8"))
    for call in calls:
        if full and call["seq"] not in full:
            continue
        if call["seq"] in full:
            print(f"══ #{call['seq']:03d} {call['agent']} — FULL ══")
            for message in call["messages"]:
                print(f"--- {str(message.get('role')).upper()} ---")
                print(message.get("content", ""))
            print("--- REPLY ---")
            print(call["response_text"])
            print()
            continue
        print(digest(call))
        print()


__all__ = ["main"]
