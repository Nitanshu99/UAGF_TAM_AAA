"""Artefact evidence for one article: what was admitted, and what was thrown out."""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Per-artefact character ceiling in the prompt. Whole payloads would push a
#: 17-article brief past any context window; the head of an artefact carries
#: the declared fields the brief quotes back.
_EXCERPT_CHARS = 6000

#: Artefacts per article. Ordering is the matrix's, so the first entries are the
#: ones the verdict was actually drawn from.
_MAX_ARTEFACTS = 4


def artefact_excerpts(uris: list[str], store: Any) -> list[dict[str, Any]]:
    """Resolve *uris* against the evidence *store* and excerpt each payload.

    A URI that does not resolve is reported as such rather than skipped: a
    dangling reference is itself a fact about the evidence chain, and silently
    dropping it would let the brief describe an article as evidenced when
    nothing backs it.

    :param uris: Artefact URIs from the article's evidence list.
    :param store: Evidence store, or ``None`` when unreachable.
    :returns: One entry per URI with the payload text or the reason it is absent.
    """
    out: list[dict[str, Any]] = []
    for uri in uris[:_MAX_ARTEFACTS]:
        payload = None
        if store is not None:
            try:
                payload = store.get_artefact(uri)
            except Exception as exc:  # noqa: BLE001 — a bad URI must not stop the brief
                logger.warning("Client brief: could not resolve %s (%s)", uri, exc)
        if payload is None:
            out.append({"uri": uri, "resolved": False,
                        "note": "This artefact could not be read back from the "
                                "evidence store, so nothing in it is quoted here."})
            continue
        body = json.dumps(payload, indent=2, default=str)
        out.append({"uri": uri, "resolved": True,
                    "truncated": len(body) > _EXCERPT_CHARS,
                    "content": body[:_EXCERPT_CHARS]})
    return out


def rejected_artefacts(article: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the artefacts the Verifier refused to admit for *article*.

    The ``reason`` on each entry is the Verifier's own wording, which is where
    the sharpest declared-versus-observed contradictions in a run are recorded
    ("the artefact claims no sensitive features, the data dictionary lists five").

    :param article: Matrix article key.
    :param state: Final ``AuditState``.
    :returns: Matching entries from ``unadmitted_artefacts``.
    """
    return [entry for entry in (state.get("unadmitted_artefacts") or [])
            if article in (entry.get("articles") or [])]
