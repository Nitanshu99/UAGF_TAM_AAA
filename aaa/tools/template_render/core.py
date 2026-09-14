"""Part 3 of the former ``template_render`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.platform.evidence import EvidenceStore
from aaa.platform.state import ArtefactRef
from aaa.tools.template_render.logger import (  # noqa: F401
    _TEMPLATES_DIR,
    TemplateRenderError,
    _load_schema,
    _validate_payload,
    logger,
)
from aaa.tools.template_render.render_fragment import _persist, _render_fragment  # noqa: F401


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
    return _persist(store, template_id, payload, fragment, fragment_format,
                    engagement_id=engagement_id, phase=phase, agent_name=agent_name)
