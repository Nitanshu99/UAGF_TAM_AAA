"""Heading / noise regexes for the ISO and ISAE PDF parsers."""
from __future__ import annotations

import re

# ISO/IEC 42001 clause / Annex A control heading patterns
ISO_CLAUSE_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,3})\s+([A-Za-z][A-Za-z0-9 ,\-:/&()]+)\s*$")
ISO_CONTROL_RE = re.compile(r"^\s*(A\.\d+(?:\.\d+){0,2})\s+([A-Za-z][A-Za-z0-9 ,\-:/&()]+)\s*$")
ISO_CLAUSE_NUM_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,3})\s*$")
ISO_CONTROL_NUM_RE = re.compile(r"^\s*(A\.\d+(?:\.\d+){0,2})\s*$")
ISO_TITLE_HEAD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 ,\-:/&()]+$")
ISO_PAGE_NOISE_RE = re.compile(
    r"^(ISO/IEC\s+42001[:\d\s()E\-]*|\(E\)|\d{1,4})$", re.IGNORECASE)

ISAE_PARAGRAPH_RE = re.compile(r"^(A?\d+)\.\s+(.*)$")
ISAE_PAGE_NOISE_RE = re.compile(
    r"^(\d{1,3}|ASSURANCE ENGAGEMENTS OTHER THAN AUDITS OR|"
    r"REVIEWS OF HISTORICAL FINANCIAL INFORMATION|ISAE 3000 \(REVISED\))$",
    re.IGNORECASE,
)


def match_iso_heading(lines: list[str], i: int) -> tuple[str, str, str, int] | None:
    """Match an ISO clause / control heading at *lines[i]*.

    Handles both single-line headings (``6.1 Actions``) and split headings
    where the number and title are on consecutive lines.

    :param lines: Noise-filtered document lines.
    :param i: Current line index.
    :returns: ``(ref, title, kind, lines_consumed_beyond_current)`` or
        ``None`` when the line is body text.
    """
    line = lines[i]
    m = ISO_CONTROL_RE.match(line)
    if m:
        return m.group(1), m.group(2).strip(), "control", 0
    m = ISO_CLAUSE_RE.match(line)
    if m and int(m.group(1).split(".")[0]) in range(4, 11):
        return m.group(1), m.group(2).strip(), "clause", 0
    has_title_next = i + 1 < len(lines) and ISO_TITLE_HEAD_RE.match(lines[i + 1])
    m = ISO_CONTROL_NUM_RE.match(line)
    if m and has_title_next:
        return m.group(1), lines[i + 1].strip(), "control", 1
    m = ISO_CLAUSE_NUM_RE.match(line)
    if m and int(m.group(1).split(".")[0]) in range(4, 11) and has_title_next:
        return m.group(1), lines[i + 1].strip(), "clause", 1
    return None
