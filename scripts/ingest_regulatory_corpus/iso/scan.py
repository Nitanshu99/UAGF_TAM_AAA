"""Heading-driven segmentation of the ISO/IEC 42001 line stream."""
from __future__ import annotations

from scripts.ingest_regulatory_corpus.models import Unit, normalise_text
from scripts.ingest_regulatory_corpus.pdf.patterns import match_iso_heading


def scan_iso_units(lines: list[str], regulation: str, source_file: str) -> list[Unit]:
    """Segment extracted PDF lines into clause / Annex-A control Units.

    :param lines: Noise-filtered text lines from the whole document.
    :param regulation: Regulation label recorded on each unit.
    :param source_file: Basename of the originating PDF.
    :returns: Clause and control units at least 40 characters long.
    """
    units: list[Unit] = []
    current_ref, current_title, current_kind = "", "", ""
    buf: list[str] = []

    def _flush() -> None:
        if current_ref and buf:
            text = normalise_text(" ".join(buf))
            if len(text) >= 40:
                units.append(Unit(regulation=regulation, kind=current_kind,
                                  ref=current_ref, title=current_title,
                                  text=text, source_file=source_file))

    i = 0
    while i < len(lines):
        heading = match_iso_heading(lines, i)
        if heading:
            _flush()
            buf = []
            current_ref, current_title, current_kind, consumed = heading
            i += consumed
        else:
            buf.append(lines[i])
        i += 1
    _flush()
    return units
