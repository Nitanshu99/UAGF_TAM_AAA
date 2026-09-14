"""Render a per-case agent-assessment markdown file from extracted LLM calls.

Usage: python -m scripts.agent_assessment.gen_report <calls.json> <analysis.py> <out.md>

The mechanical half (verbatim inputs/outputs, metrics) comes from calls.json;
the judgement half comes from analysis.py, which must define:

    HEADER   : str   -- everything above the per-call sections
    FOOTER   : str   -- everything below them
    NOTES    : dict[int, str]      -- seq -> assessment markdown
    TITLES   : dict[int, str]      -- seq -> short call title
    GROUPS   : list[tuple[str, list[int], str]]  -- (heading, seqs, preamble)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.agent_assessment.render import _load, inventory, render_call


def main(calls_path: Path, analysis_path: Path, out: Path) -> None:
    """Assemble the assessment report from the calls JSON and the analysis module."""
    calls = json.loads(calls_path.read_text("utf-8"))
    by_seq = {c["seq"]: c for c in calls}
    a = _load(analysis_path)

    doc = [a.HEADER.replace("{{INVENTORY}}", inventory(calls)).strip(), ""]
    covered: set[int] = set()
    for heading, seqs, preamble in a.GROUPS:
        doc += [f"## {heading}", ""]
        if preamble.strip():
            doc += [preamble.strip(), ""]
        for s in seqs:
            if s not in by_seq:
                continue
            covered.add(s)
            doc.append(render_call(by_seq[s], a.TITLES.get(s, ""), a.NOTES.get(s, "")))
    missing = [c["seq"] for c in calls if c["seq"] not in covered]
    if missing:
        doc += ["## Uncategorised calls", "",
                f"_Not assigned to a group: {missing}_", ""]
        for s in missing:
            doc.append(render_call(by_seq[s], a.TITLES.get(s, ""), a.NOTES.get(s, "")))
    doc += [a.FOOTER.strip(), ""]
    out.write_text("\n".join(doc), "utf-8")
    print(f"wrote {out}  ({out.stat().st_size/1024:.0f} KB, {len(calls)} calls, "
          f"{len(missing)} uncategorised)")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
