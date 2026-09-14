"""Loader dispatch and corpus-directory discovery."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from scripts.ingest_regulatory_corpus import config
from scripts.ingest_regulatory_corpus.html_loader import load_html_units
from scripts.ingest_regulatory_corpus.isae_loader import load_isae_3000_units
from scripts.ingest_regulatory_corpus.iso.loader import load_pdf_units
from scripts.ingest_regulatory_corpus.models import Unit, normalise_text


def load_units_for_path(path: Path, regulation: str | None = None) -> list[Unit]:
    """Dispatch a corpus source file to the correct structural-unit loader.

    :param path: Corpus file (HTML / PDF / text).
    :param regulation: Optional explicit regulation label.
    :returns: Structural units, or an empty list for unsupported files.
    """
    regulation = regulation or config.PDF_REGULATION_BY_NAME.get(
        path.name, config.REGULATION_BY_STEM.get(path.stem.replace(" ", "_"), path.stem))
    suffix = path.suffix.lower()
    if suffix == ".html":
        return load_html_units(path, regulation)
    if suffix == ".pdf" and regulation == "ISAE 3000":
        return load_isae_3000_units(path, regulation)
    if suffix == ".pdf":
        return load_pdf_units(path, regulation)
    if suffix in {".txt", ".md"}:
        text = normalise_text(path.read_text(encoding="utf-8"))
        return [Unit(regulation=regulation, kind="standard", ref="Document",
                     title="", text=text, source_file=path.name)] if text else []
    return []


def discover_corpus(corpus_dir: Path) -> Iterator[tuple[Path, str, str]]:
    """Yield ``(path, regulation, loader_kind)`` for every file in *corpus_dir*.

    :param corpus_dir: Directory containing the regulation sources.
    :raises SystemExit: When a required standards PDF is missing (unless
        ``AAA_ALLOW_ISO19011_STUB=true``).
    """
    missing = [name for name in config.REQUIRED_STANDARD_PDFS
               if not (corpus_dir / name).exists()]
    allow_stub = os.environ.get("AAA_ALLOW_ISO19011_STUB", "false").lower() == "true"
    if missing and not allow_stub:
        labels = ", ".join(f"{name} ({config.REQUIRED_STANDARD_PDFS[name]})"
                           for name in missing)
        raise SystemExit(f"missing required standards PDF(s) in {corpus_dir}: {labels}")
    for p in sorted(corpus_dir.iterdir()):
        if p.suffix.lower() == ".html":
            stem = p.stem.replace(" ", "_")
            yield p, config.REGULATION_BY_STEM.get(stem, stem), "html"
        elif p.suffix.lower() == ".pdf":
            regulation = config.PDF_REGULATION_BY_NAME.get(p.name)
            if regulation:
                yield p, regulation, "pdf"
