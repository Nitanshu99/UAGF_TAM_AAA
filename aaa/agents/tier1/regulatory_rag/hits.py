"""Qdrant payload → search-result mapping and pinpoint locators."""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Qdrant payload → search-result mapping
# ---------------------------------------------------------------------------
_REGULATION_LABEL: dict[str, str] = {
    "EU_AI_Act": "EU AI Act",
    "GDPR": "GDPR",
    "ISO_IEC_42001": "ISO/IEC 42001",
    "ISAE 3000": "ISAE 3000 (Revised)",
    "ISO 19011": "ISO 19011:2018",
}

# URI scheme per regulation for the synthetic pinpoint locator.
_REGULATION_SCHEME: dict[str, str] = {
    "EU_AI_Act": "euaiact",
    "GDPR": "gdpr",
    "ISO_IEC_42001": "iso42001",
}


def _locator(regulation: str, ref: str, source_file: str = "") -> str:
    """Build a stable pinpoint locator/source_uri for a regulatory unit.

    e.g. ``euaiact://Article_9`` (optionally ``…#source_file``). Empty when there
    is no ref to anchor on. This is enough for claim-level traceability; a real
    EUR-Lex/CELEX deep link is future work.
    """
    if not ref:
        return ""
    scheme = _REGULATION_SCHEME.get(regulation, "reg")
    slug = re.sub(r"\s+", "_", ref.strip())
    locator = f"{scheme}://{slug}"
    return f"{locator}#{source_file}" if source_file else locator


def _point_to_hit(point: Any) -> dict[str, Any]:
    """Project a Qdrant ScoredPoint to the public hit contract.

    Surfaces ``ref``/``title``/``source_file``/``obligations`` and a pinpoint
    ``locator``/``source_uri`` so downstream agents can cite a specific clause,
    in addition to the legacy ``{text, source, article, score}`` keys.

    ``chunk_index`` comes out too: an article is chunked per unit, so two
    passages of Article 10 share one synthetic locator and the index is what
    orders them and what makes ``merge_hits``'s de-duplication key exact.
    """
    payload = getattr(point, "payload", None) or {}
    regulation = payload.get("regulation", "")
    ref = payload.get("ref", "") or payload.get("article", "")
    label = _REGULATION_LABEL.get(regulation, regulation or "Regulation")
    source_file = payload.get("source_file", "")
    locator = _locator(regulation, ref, source_file)
    return {
        "text": payload.get("text", ""),
        "source": f"{label} {ref}".strip() if ref else label,
        "article": ref,
        "ref": ref,
        "title": payload.get("title", ""),
        "source_file": source_file,
        "obligations": list(payload.get("obligations", []) or []),
        "locator": locator,
        "source_uri": locator,
        "chunk_index": payload.get("chunk_index"),
        "score": float(getattr(point, "score", 0.0) or 0.0),
    }
