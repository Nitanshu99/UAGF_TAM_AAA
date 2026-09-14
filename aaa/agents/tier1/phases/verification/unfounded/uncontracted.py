"""A material defect on a field the template does not define is unfounded.

Case 01 (MiniMax run, 2026-09-14): the Verifier escalated T10 because "the artefact
payload contains no evidence_uris field". T10's schema has no such property — the
evidence URIs travel in the review request, and the Verifier prompt says a populated
artefact URI alone satisfies traceability. A field outside the contract cannot make an
artefact defective (T-20260914-053).
"""
from __future__ import annotations

import re
from typing import Any

from aaa.tools.template_render.logger import TemplateRenderError, _load_schema


def field_root(field: Any) -> str:
    """The top-level key an issue's field names ("entries[0].marker" → "entries")."""
    return re.split(r"[.\[\s]", str(field or "").strip(), maxsplit=1)[0]


def uncontracted_reason(issue: dict[str, Any], tid: str) -> str | None:
    """Why *issue* cannot make *tid* defective, or ``None`` when its field is contracted.

    :param issue: A material artefact-defect issue.
    :param tid: The template it was raised on.
    """
    try:
        contracted = set(_load_schema(tid).get("properties") or {})
    except TemplateRenderError:
        return None
    root = field_root(issue.get("field"))
    if not contracted or not root or root in contracted:
        return None
    return (f"it names a field the {tid} template does not define ({root}), and a field "
            "outside the contract cannot make the artefact defective")


__all__ = ["field_root", "uncontracted_reason"]
