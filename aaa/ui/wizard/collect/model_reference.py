"""Assembly of the Stage B ``model_reference`` block from wizard state.

Empty answers are dropped rather than stored as ``None``: the T01b schema sets
``additionalProperties: false`` on the reference and requires provider,
model_id and revision, so an all-empty block would be a validation failure
where "the customer did not reach this branch" is the truth.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.state.model_meta import ModelReference
from aaa.platform.state.model_vocab import REFERENCE_MODES
from aaa.ui.wizard.step3.provenance.fields import state_key
from aaa.ui.wizard.step3.provenance.vendors import questions_for

#: Answers stored as free text but carried as structured objects.
_MAPPING_KEYS = ("runtime_versions", "decoding_params")


def _value(session: Any, reference_key: str) -> Any:
    """Read and normalise one answer from session state."""
    raw = session.get(state_key(reference_key))
    if reference_key == "gated":
        return bool(raw) if raw is not None else None
    text = str(raw or "").strip()
    if not text:
        return None
    return {"declared": text} if reference_key in _MAPPING_KEYS else text


def model_reference_fields(session: Any) -> dict[str, Any]:
    """Assemble ``model_access_mode`` and ``model_reference`` for stage_b.

    :param session: Wizard session state (mapping-like).
    :type session: Any
    :returns: The provenance fields, omitting anything the customer left blank.
    :rtype: dict[str, Any]
    """
    mode = str(session.get("s3_b_access_mode") or "").strip()
    if not mode:
        return {}
    fields: dict[str, Any] = {"model_access_mode": mode}
    if mode not in REFERENCE_MODES:
        return fields
    provider = str(session.get("s3_b_ref_provider") or "").strip()
    if not provider:
        return fields
    reference: dict[str, Any] = {"provider": provider}
    for reference_key, _label, _help in questions_for(provider):
        value = _value(session, reference_key)
        if value is not None:
            reference[reference_key] = value
    fields["model_reference"] = ModelReference(**reference)  # type: ignore[typeddict-item]
    return fields
