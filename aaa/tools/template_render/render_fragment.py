"""Part 2 of the former ``template_render`` module (auto-split)."""
from __future__ import annotations

import json

from aaa.platform.evidence import EvidenceStore
from aaa.platform.state import ArtefactRef
from aaa.tools.template_render.logger import (  # noqa: F401
    _TEMPLATES_DIR,
    TemplateRenderError,
    _load_schema,
    _validate_payload,
    logger,
)


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


def _persist(store: EvidenceStore, template_id: str, payload: dict, fragment: str,
             fragment_format: str, *, engagement_id: str, phase: str,
             agent_name: str) -> ArtefactRef:
    """Store the payload + rendered fragment and build the artefact ref.

    :returns: The :class:`ArtefactRef` of the stored payload artefact.
    """
    uri = store.store_artefact(
        engagement_id=engagement_id, phase=phase,
        artefact_type=template_id, content=payload, agent_name=agent_name)
    store.store_artefact(
        engagement_id=engagement_id, phase=phase,
        artefact_type=f"{template_id}.fragment",
        content={"format": fragment_format, "body": fragment}, agent_name=agent_name)
    sha256 = ""
    for entry in store.get_index(engagement_id):
        if entry.get("uri") == uri:
            sha256 = entry.get("sha256", "")
            break
    return ArtefactRef(uri=uri, sha256=sha256, template_id=template_id)  # type: ignore[arg-type]
