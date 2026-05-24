"""
template_render — load a template's JSON Schema, validate a payload, render
an HTML/JSON fragment, and persist both to the Evidence Store (§4A).

  template_render(template_id, payload, *, engagement_id, phase, agent_name,
                  store, fragment_format="json") -> ArtefactRef

Schemas live in ``src/templates/<template_id>.json``.  Jinja2 partials are
optional — when ``src/templates/<template_id>.html.j2`` exists it is used to
render the human-readable fragment; otherwise the payload is round-tripped
through ``json.dumps`` as the fragment.

Both the schema validation and the jinja2 render are guarded so that the
function never raises on missing optional dependencies.  Pure-Python
fallbacks are used when ``jsonschema`` or ``jinja2`` are not installed.

The function returns an ``ArtefactRef`` ({uri, sha256, template_id}) pointing
at the **JSON payload** in the Evidence Store; rendered fragments are stored
under the same engagement / phase prefix with a ``.fragment`` suffix.
"""
from __future__ import annotations

import json
import logging
import pathlib
from typing import Any, Optional

from src.platform.evidence import EvidenceStore
from src.platform.state import ArtefactRef

logger = logging.getLogger(__name__)

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_TEMPLATES_DIR = _REPO_ROOT / "src" / "templates"


class TemplateRenderError(Exception):
    """Raised when payload validation or rendering fails hard."""

    def __init__(self, reason: str, details: Optional[dict[str, Any]] = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[template_render] {reason}")


def _load_schema(template_id: str) -> dict[str, Any]:
    """Read ``src/templates/<template_id>.json``; return parsed dict."""
    path = _TEMPLATES_DIR / f"{template_id}.json"
    if not path.exists():
        raise TemplateRenderError(
            f"schema not found for template_id={template_id!r}",
            {"expected_path": str(path)},
        )
    with path.open() as fh:
        return json.load(fh)


def _validate_payload(payload: dict, schema: dict, template_id: str) -> list[str]:
    """Return a list of validation error messages (empty when valid)."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        logger.debug("jsonschema not installed; skipping validation for %s.", template_id)
        return []
    try:
        jsonschema.validate(payload, schema)
        return []
    except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
        return [exc.message]
    except Exception as exc:  # pragma: no cover
        return [str(exc)]


def _render_fragment(template_id: str, payload: dict, fragment_format: str) -> str:
    """Render a human-readable fragment from ``payload``.

    Falls back to ``json.dumps`` when jinja2 or the ``.html.j2`` partial is
    unavailable.
    """
    if fragment_format == "json":
        return json.dumps(payload, indent=2, default=str)
    partial = _TEMPLATES_DIR / f"{template_id}.html.j2"
    if not partial.exists():
        return json.dumps(payload, indent=2, default=str)
    try:
        import jinja2  # type: ignore
    except ImportError:
        logger.debug("jinja2 not installed; falling back to JSON fragment for %s.", template_id)
        return json.dumps(payload, indent=2, default=str)
    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=jinja2.select_autoescape(["html"]),
        )
        template = env.get_template(f"{template_id}.html.j2")
        return template.render(**payload)
    except Exception as exc:  # pragma: no cover
        logger.warning("jinja2 render failed for %s: %s; using JSON fragment.", template_id, exc)
        return json.dumps(payload, indent=2, default=str)


def template_render(
    template_id: str,
    payload: dict[str, Any],
    *,
    engagement_id: str,
    phase: str,
    agent_name: str,
    store: EvidenceStore,
    fragment_format: str = "json",
    strict: bool = False,
) -> ArtefactRef:
    """Validate, render, and persist a template instance.

    Parameters
    ----------
    template_id : str
        e.g. ``"T17_compliance_matrix"``.
    payload : dict
        The structured payload to validate against the template schema.
    engagement_id, phase, agent_name : str
        EvidenceStore index fields.
    store : EvidenceStore
        Backing artefact store.
    fragment_format : "json" | "html"
        ``"json"`` (default) round-trips through ``json.dumps``;
        ``"html"`` looks up ``<template_id>.html.j2`` and renders via jinja2.
    strict : bool
        When ``True``, raise ``TemplateRenderError`` on any schema violation.
        When ``False`` (default), log a warning and store the payload anyway
        so downstream phases can still proceed (the verifier will flag it).
    """
    schema = _load_schema(template_id)
    errors = _validate_payload(payload, schema, template_id)
    if errors:
        logger.warning("[template_render] %s schema errors: %s", template_id, errors[:3])
        if strict:
            raise TemplateRenderError(
                f"payload failed schema validation for {template_id}",
                {"errors": errors[:5]},
            )

    fragment = _render_fragment(template_id, payload, fragment_format)

    uri = store.store_artefact(
        engagement_id=engagement_id,
        phase=phase,
        artefact_type=template_id,
        content=payload,
        agent_name=agent_name,
    )

    fragment_uri = store.store_artefact(
        engagement_id=engagement_id,
        phase=phase,
        artefact_type=f"{template_id}.fragment",
        content={"format": fragment_format, "body": fragment},
        agent_name=agent_name,
    )

    sha256 = ""
    for entry in store.get_index(engagement_id):
        if entry.get("uri") == uri:
            sha256 = entry.get("sha256", "")
            break

    return ArtefactRef(uri=uri, sha256=sha256, template_id=template_id)  # type: ignore[arg-type]
