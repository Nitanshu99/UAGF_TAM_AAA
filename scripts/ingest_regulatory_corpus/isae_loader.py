"""ISAE 3000 PDF loader — paragraph-numbered segmentation."""
from __future__ import annotations

from pathlib import Path

from scripts.ingest_regulatory_corpus.models import Unit, normalise_text
from scripts.ingest_regulatory_corpus.pdf.lines import pdf_lines_by_page
from scripts.ingest_regulatory_corpus.pdf.patterns import ISAE_PAGE_NOISE_RE, ISAE_PARAGRAPH_RE


def is_isae_heading(line: str) -> bool:
    """Return True for ISAE section headings such as Objectives."""
    if ISAE_PAGE_NOISE_RE.match(line) or ISAE_PARAGRAPH_RE.match(line):
        return False
    if len(line) > 100 or line.endswith(".") or "........" in line:
        return False
    words = line.split()
    if not 1 <= len(words) <= 10:
        return False
    return line[:1].isupper() and any(ch.isalpha() for ch in line)


def load_isae_3000_units(path: Path, regulation: str = "ISAE 3000") -> list[Unit]:
    """Parse ISAE 3000 into paragraph/application-material Units.

    Parser investigation (2026-06-01): the ISO/IEC 42001 clause parser
    extracted only 10 oversized, mislabelled units from ``isae_3000.pdf``.
    ISAE 3000 is paragraph-numbered, so this loader segments on ``1.`` /
    ``A1.`` markers and carries the nearest section heading as the title.

    :param path: PDF file to read.
    :param regulation: Regulation label recorded on each unit.
    :returns: Paragraph and application-material units.
    """
    units: list[Unit] = []
    current_ref, current_title, current_kind = "", "", "paragraph"
    start_page = 0
    buf: list[str] = []

    def _flush() -> None:
        if not current_ref or not buf:
            return
        text = normalise_text(" ".join(buf))
        if len(text) < 40:
            return
        units.append(Unit(regulation=regulation, kind=current_kind, ref=current_ref,
                          title=current_title, text=text, source_file=path.name,
                          extra={"page": start_page}))

    for page_no, lines in pdf_lines_by_page(path):
        for line in lines:
            if ISAE_PAGE_NOISE_RE.match(line):
                continue
            match = ISAE_PARAGRAPH_RE.match(line)
            if match:
                _flush()
                current_ref = match.group(1)
                current_kind = "application" if current_ref.startswith("A") else "paragraph"
                start_page = page_no
                buf = [match.group(2)]
                continue
            if is_isae_heading(line):
                current_title = line
                continue
            if current_ref:
                buf.append(line)
    _flush()
    return units
