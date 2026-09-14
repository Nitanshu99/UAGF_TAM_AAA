"""Low-level PDF text extraction via the pypdfium2 backend."""
from __future__ import annotations

from pathlib import Path

from scripts.ingest_regulatory_corpus.deps import require


def pdf_lines_by_page(path: Path) -> list[tuple[int, list[str]]]:
    """Extract non-empty text lines from *path* using pypdfium2.

    :param path: PDF file to read.
    :returns: ``(page_number, lines)`` tuples, 1-indexed.
    """
    pdfium = require("pypdfium2")
    pages: list[tuple[int, list[str]]] = []
    doc = pdfium.PdfDocument(str(path))
    try:
        for page_no, page in enumerate(doc, start=1):
            tp = page.get_textpage()
            try:
                text = tp.get_text_bounded() or ""
            finally:
                tp.close()
                page.close()
            lines = [raw.strip() for raw in text.splitlines() if raw.strip()]
            pages.append((page_no, lines))
    finally:
        doc.close()
    return pages
