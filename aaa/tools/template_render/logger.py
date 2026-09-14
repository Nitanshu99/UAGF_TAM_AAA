"""Part 1 of the former ``template_render`` module (auto-split)."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from aaa.platform.repo_root import REPO_ROOT as _REPO_ROOT

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = _REPO_ROOT / "templates"


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
