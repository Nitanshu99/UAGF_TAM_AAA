"""Domain types shared across the ingestion pipeline."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Unit:
    """A single structural unit of a regulation (article, recital, annex, clause)."""

    regulation: str            # "EU_AI_Act" | "GDPR" | "ISO_IEC_42001"
    kind: str                  # "article" | "recital" | "annex" | "clause" | "control"
    ref: str                   # "Article 9", "Recital 27", "Annex III", "6.1", "A.6.2"
    title: str                 # short heading, may be "" for recitals
    text: str                  # cleaned plain text
    source_file: str           # basename of the originating file
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunk produced by the per-unit SentenceSplitter."""

    text: str
    payload: dict[str, Any]

    @property
    def point_id(self) -> str:
        """Deterministic UUID-format ID from the chunk text + payload key fields."""
        h = hashlib.sha256()
        h.update(self.text.encode("utf-8"))
        h.update(self.payload.get("regulation", "").encode("utf-8"))
        h.update(self.payload.get("ref", "").encode("utf-8"))
        h.update(str(self.payload.get("chunk_index", 0)).encode("utf-8"))
        digest = h.hexdigest()
        # Qdrant accepts unsigned 64-bit integer IDs or UUID strings. Use UUID format.
        return f"{digest[0:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def normalise_text(text: str) -> str:
    """Collapse whitespace and strip the unicode artefacts EUR-Lex emits."""
    text = text.replace("\xa0", " ").replace("\u2003", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
