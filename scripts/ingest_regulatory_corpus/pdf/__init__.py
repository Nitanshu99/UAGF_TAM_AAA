"""Low-level PDF text extraction and the ISO/ISAE heading/noise regexes."""
from __future__ import annotations

from scripts.ingest_regulatory_corpus.pdf.lines import pdf_lines_by_page
from scripts.ingest_regulatory_corpus.pdf.patterns import (
    ISAE_PAGE_NOISE_RE,
    ISAE_PARAGRAPH_RE,
    ISO_PAGE_NOISE_RE,
    match_iso_heading,
)

__all__ = [
    "ISAE_PAGE_NOISE_RE",
    "ISAE_PARAGRAPH_RE",
    "ISO_PAGE_NOISE_RE",
    "match_iso_heading",
    "pdf_lines_by_page",
]
