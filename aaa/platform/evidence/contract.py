"""Every stored artefact is checked against its template, and the result is kept.

Only T17 and T18 were ever validated, at render time. T06–T16 were stored unchecked,
so case 06's T14 carried 108 schema errors into the deliverable and nothing in the
run said so (T-20260913-018). The check runs where every artefact passes — the
evidence store — and it records rather than refuses: an audit is not abandoned
over a malformed artefact, but the artefact's index entry carries its errors and
the deliverable's ``run_integrity`` lists it.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, Iterable

from aaa.platform.repo_root import REPO_ROOT
from aaa.platform.state.artefact_keys import base_template_id

logger = logging.getLogger(__name__)

#: Errors kept on an index entry; the count is always complete.
MAX_RECORDED_ERRORS = 20
_MAX_MESSAGE = 300


@lru_cache(maxsize=64)
def _validator(template_id: str) -> Any | None:
    """The validator for *template_id*'s schema, or ``None`` when it has no template."""
    path = REPO_ROOT / "templates" / f"{template_id}.json"
    if not path.is_file():
        return None
    from jsonschema.validators import validator_for  # pylint: disable=import-outside-toplevel

    schema = json.loads(path.read_text(encoding="utf-8"))
    # The draft each template declares (draft-07 today), not an assumed one.
    return validator_for(schema)(schema)


def artefact_schema_errors(artefact_type: str, content: Any) -> list[str] | None:
    """Every violation of the artefact's template, as ``path: message``.

    :param artefact_type: Template id, optionally spawn-namespaced.
    :param content: The artefact payload.
    :returns: The errors (empty when valid), or ``None`` when no template applies.
    """
    validator = _validator(base_template_id(artefact_type))
    if validator is None:
        return None
    return sorted(f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message[:_MAX_MESSAGE]}"
                  for e in validator.iter_errors(content))


def contract_fields(artefact_type: str, content: Any, uri: str) -> dict[str, Any]:
    """Index-entry fields recording the check; logged when the artefact fails it.

    :returns: ``schema_error_count`` and the first errors, or ``{}`` when no
        template applies.
    """
    errors = artefact_schema_errors(artefact_type, content)
    if errors is None:
        return {}
    if errors:
        logger.warning("Artefact %s violates its template in %d place(s); first: %s",
                       uri, len(errors), errors[0])
    return {"schema_error_count": len(errors), "schema_errors": errors[:MAX_RECORDED_ERRORS]}


def schema_violations(index: Iterable[dict[str, Any]], artefacts: dict[str, Any]) -> dict[str, int]:
    """``{artefact key: error count}`` for the run's artefacts that failed their template.

    :param index: The engagement's evidence-store index entries.
    :param artefacts: ``phase_artefacts`` from the final state.
    """
    counts = {e.get("uri"): int(e.get("schema_error_count") or 0) for e in index}
    return {key: counts[ref["uri"]] for key, ref in (artefacts or {}).items()
            if isinstance(ref, dict) and counts.get(ref.get("uri"))}


__all__ = ["MAX_RECORDED_ERRORS", "artefact_schema_errors", "contract_fields", "schema_violations"]
