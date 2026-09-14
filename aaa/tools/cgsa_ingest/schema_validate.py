"""Part 3 of the former ``cgsa_ingest`` module (auto-split)."""
from __future__ import annotations

import json
import pathlib
from typing import Any

from aaa.tools.cgsa_ingest.logger import (  # noqa: F401
    _LOW_CONFIDENCE_THRESHOLD,
    _REQUIRED_TOP_LEVEL_KEYS,
    _VENDORED_SCHEMA,
    CGSAIngestError,
    IngestResult,
    logger,
)
from aaa.tools.cgsa_ingest.shallow_required_check import _shallow_required_check  # noqa: F401


def schema_validate(
    payload: dict[str, Any],
    schema_version: str = "1.0.0",
    schema_path: pathlib.Path | None = None,
) -> list[str]:
    """
    Validate ``payload`` against the vendored CGSA schema.

    Returns a list of error messages (empty ⇒ valid).
    Uses ``jsonschema`` when available; otherwise applies a minimal
    required-keys check so runs without ``jsonschema`` still
    surface gross structural problems.
    """
    path = schema_path or _VENDORED_SCHEMA
    if not path.exists():
        return [f"vendored schema not found at {path}"]

    with path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)

    declared = schema.get("schema_version")
    if declared and declared != schema_version:
        return [
            f"schema_version mismatch — vendored={declared}, requested={schema_version}"
        ]

    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft7Validator(schema)
        errors = [
            f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
            for err in validator.iter_errors(payload)
        ]
        return errors
    except ImportError:
        return _shallow_required_check(payload)
