"""ISO/IEC 42001 PDF loader."""
from __future__ import annotations

from pathlib import Path

from scripts.ingest_regulatory_corpus.console import warn
from scripts.ingest_regulatory_corpus.deps import require
from scripts.ingest_regulatory_corpus.iso.scan import scan_iso_units
from scripts.ingest_regulatory_corpus.models import Unit
from scripts.ingest_regulatory_corpus.pdf.patterns import ISO_PAGE_NOISE_RE


def load_pdf_units(path: Path, regulation: str = "ISO_IEC_42001") -> list[Unit]:
    """Parse the ISO/IEC 42001 PDF into clause + Annex-A control Units.

    Uses pypdfium2 because pdfminer-based readers (pdfplumber, pypdf) silently
    return zero pages on PDFs that use newline-separated object headers, as
    produced by the PDF Tools AG toolchain ISO ships its standards through.

    :param path: PDF file to read.
    :param regulation: Regulation label recorded on each unit.
    :returns: Clause and control units; empty when the PDF is scan-only.
    """
    pdfium = require("pypdfium2")
    lines: list[str] = []
    doc = pdfium.PdfDocument(str(path))
    try:
        for page in doc:
            tp = page.get_textpage()
            try:
                page_text = tp.get_text_bounded() or ""
            finally:
                tp.close()
                page.close()
            for raw in page_text.splitlines():
                stripped = raw.strip()
                if not stripped or ISO_PAGE_NOISE_RE.match(stripped):
                    continue
                lines.append(stripped)
    finally:
        doc.close()
    if not lines:
        warn(f"{path.name}: pypdfium2 extracted no text — PDF may be scan-only")
        return []
    return scan_iso_units(lines, regulation, path.name)
