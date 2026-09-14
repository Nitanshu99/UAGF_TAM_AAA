"""
uagf-tam-templates — distributable T01a–T18 JSON Schemas + Jinja2 partials.

This is the public artefact-template package referenced by §4A of
``ARCHITECTURE.md``.  Audit toolchains that want to render UAGF-TAM
artefacts without depending on the full AAA codebase can install
this package from PyPI and use its loader API.

Public API
----------

* :func:`schema_path(template_id)` — absolute path to the schema file.
* :func:`load_schema(template_id)` — parsed JSON-Schema dict.
* :func:`list_templates()` — sorted list of all packaged template IDs.
* :func:`validate(template_id, instance)` — jsonschema draft-07 check.
* :func:`partial_env()` — pre-configured :class:`jinja2.Environment`
  whose loader resolves ``{template_id}.j2`` partials.
* :func:`render_partial(template_id, context)` — convenience renderer.

Template IDs are the canonical AAA names (e.g. ``T02_system_card``,
``T17_compliance_matrix``).
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache
from typing import Any

__version__ = "0.1.0"

_PKG_ROOT = pathlib.Path(__file__).resolve().parent
_SCHEMAS_DIR = _PKG_ROOT / "schemas"
_PARTIALS_DIR = _PKG_ROOT / "partials"

__all__ = [
    "__version__",
    "schema_path",
    "load_schema",
    "list_templates",
    "validate",
    "partial_env",
    "render_partial",
    "SchemaNotFoundError",
]


class SchemaNotFoundError(KeyError):
    """Raised when ``template_id`` is not packaged in this distribution."""


def list_templates() -> list[str]:
    """Return the sorted list of packaged template IDs (without ``.json``)."""
    return sorted(p.stem for p in _SCHEMAS_DIR.glob("T*.json"))


def schema_path(template_id: str) -> pathlib.Path:
    """Return the on-disk path to ``{template_id}.json``."""
    path = _SCHEMAS_DIR / f"{template_id}.json"
    if not path.is_file():
        raise SchemaNotFoundError(template_id)
    return path


@lru_cache(maxsize=None)
def load_schema(template_id: str) -> dict[str, Any]:
    """Return the parsed JSON-Schema dict for ``template_id``."""
    return json.loads(schema_path(template_id).read_text())


def validate(template_id: str, instance: dict[str, Any]) -> None:
    """
    Validate ``instance`` against the packaged schema for ``template_id``.

    Raises ``jsonschema.ValidationError`` on failure.
    """
    import jsonschema  # local import keeps importing the package cheap

    jsonschema.validate(instance, load_schema(template_id))


def partial_env():  # -> jinja2.Environment
    """
    Return a :class:`jinja2.Environment` pre-loaded with the packaged partials
    directory.  Templates are addressable as ``"{template_id}.j2"``.
    """
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    return Environment(
        loader=FileSystemLoader(str(_PARTIALS_DIR)),
        autoescape=select_autoescape(default_for_string=False),
        keep_trailing_newline=True,
    )


def render_partial(template_id: str, context: dict[str, Any]) -> str:
    """
    Render the Jinja2 partial ``{template_id}.j2`` with ``context``.

    Raises ``jinja2.TemplateNotFound`` if no partial is packaged.
    """
    env = partial_env()
    return env.get_template(f"{template_id}.j2").render(**context)
