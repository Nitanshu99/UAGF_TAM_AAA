"""Sliding-window chunking of extracted document text."""
from __future__ import annotations

import hashlib
import re
from typing import Any

from aaa.tools.client_doc_ingest.config import (
    _CHUNK_CHARS,
    _OVERLAP_CHARS,
    _content_type,
    _filename,
)
from aaa.tools.client_doc_ingest.extract import _extract_pages
from aaa.tools.client_doc_ingest.loading import _document_role


def normalise_layout(text: str) -> str:
    """Collapse runs of spaces and blank lines, keeping the line breaks.

    Every whitespace run used to become one space, so each uploaded document was
    stored as a single line: a table row lost its boundary, a heading could never
    be found by :func:`_section_hint`, and a reader of a passage could not tell a
    sentence from a flattened table (live run bb7837: T15 read "drift … Live" out
    of two different rows of the monitoring plan).

    :param text: Extracted page text.
    """
    text = re.sub(r"[^\S\n]+", " ", text)
    return re.sub(r" ?\n[\s]*", "\n", text).strip()


def _section_hint(text: str) -> str | None:
    """Return the first heading-like line of *text* (or ``None``)."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped[:1].isdigit():
            return stripped[:120]
    return None


def _point_id(chunk: dict[str, Any]) -> str:
    """Derive a stable UUID-shaped point id from the chunk identity."""
    raw = f"{chunk['source_uri']}:{chunk['chunk_index']}:{chunk['source_sha256']}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def _chunks_for_document(uri: str, data: bytes) -> list[dict[str, Any]]:
    """Chunk one document into overlapping windows with provenance payloads."""
    ctype = _content_type(uri)
    source_sha = hashlib.sha256(data).hexdigest()
    chunks: list[dict[str, Any]] = []
    step = max(1, _CHUNK_CHARS - _OVERLAP_CHARS)
    for page_number, text in _extract_pages(data, ctype):
        text = normalise_layout(text)
        if not text:
            continue
        for start in range(0, len(text), step):
            body = text[start:start + _CHUNK_CHARS].strip()
            if not body:
                continue
            chunks.append({
                "text": body, "source_uri": uri, "source_filename": _filename(uri),
                "source_sha256": source_sha, "content_type": ctype,
                "document_role": _document_role(uri), "page_number": page_number,
                "section_hint": _section_hint(body), "char_start": start,
                "char_end": min(start + _CHUNK_CHARS, len(text)),
            })
    total = len(chunks)
    for idx, chunk in enumerate(chunks):
        chunk["chunk_index"] = idx
        chunk["chunk_total"] = total
    return chunks
