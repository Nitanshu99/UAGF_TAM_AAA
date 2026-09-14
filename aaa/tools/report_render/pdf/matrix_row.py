"""One conformity-matrix row: its verdict, its evidence basis and its notes."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph

from aaa.tools.report_render.numbers import shorten
from aaa.tools.report_render.pdf.theme import STYLES, verdict_color

#: A rationale shorter than this is cheaper to repeat than to cross-reference.
_NOTE_THRESHOLD = 120
def _notes(articles: list[dict[str, Any]]) -> dict[str, int]:
    """Number the long rationales that more than one article shares (Q15).

    Four articles carried the same 300-character fairness paragraph in the
    delivered report, filling half of two pages with one repeated sentence.
    A shared basis is stated once and referenced after that.

    :param articles: T17 article entries.
    :returns: ``{rationale: note number}`` for each repeated long rationale.
    """
    counts: dict[str, int] = {}
    for entry in articles:
        text = (entry.get("rationale") or "").strip()
        if len(text) >= _NOTE_THRESHOLD:
            counts[text] = counts.get(text, 0) + 1
    repeated = [text for text, n in counts.items() if n > 1]
    return {text: i for i, text in enumerate(repeated, 1)}
def _basis(entry: dict[str, Any], notes: dict[str, int], seen: set[int]) -> str:
    """The Basis cell: the rationale, or a reference once it has been given."""
    text = shorten((entry.get("rationale") or "").strip())
    key = (entry.get("rationale") or "").strip()
    note = notes.get(key)
    if note is None:
        return text
    if note in seen:
        return f'<i>See note {note} below.</i>'
    seen.add(note)
    return f"<b>[{note}]</b> {text}"
def _row(entry: dict[str, Any], notes: dict[str, int], seen: set[int]) -> list[Any]:
    """Build one article row: article · verdict · findings · rationale."""
    verdict = (entry.get("verdict") or "—").upper()
    verdict_para = Paragraph(
        f'<font color="{verdict_color(verdict).hexval()}"><b>{verdict}</b></font>',
        STYLES["cell"])
    findings = len(entry.get("blocking_findings") or [])
    article = str(entry.get("article") or "—").replace("_", " ")
    return [Paragraph(f"<b>{article}</b>", STYLES["cell"]), verdict_para,
            Paragraph(str(findings) if findings else "—", STYLES["cell"]),
            Paragraph(_basis(entry, notes, seen), STYLES["cell"])]


__all__ = ["_NOTE_THRESHOLD", "_basis", "_notes", "_row"]
