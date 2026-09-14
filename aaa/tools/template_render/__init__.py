"""template_render — load a template's JSON Schema, validate a payload, render
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
under the same engagement / phase prefix with a ``.fragment`` suffix."""
from aaa.tools.template_render.core import template_render  # noqa: F401
from aaa.tools.template_render.logger import (  # noqa: F401
    _TEMPLATES_DIR,
    TemplateRenderError,
    _load_schema,
    _validate_payload,
    logger,
)
from aaa.tools.template_render.render_fragment import _persist, _render_fragment  # noqa: F401

__all__ = [
    'logger', '_TEMPLATES_DIR', 'TemplateRenderError', '_load_schema', '_validate_payload',
    '_render_fragment', '_persist', 'template_render',
]
