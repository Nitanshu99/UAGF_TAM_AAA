"""Builds the audit-state hand-off document sent to external partner services.

The hand-off is the full audit state wrapped in a versioned envelope, plus
fail-soft warnings when fields the S6 evaluation contract requires are
missing — callers surface the warnings but proceed.

Warnings key off ``model_access_mode``: under the reference modes S6 resolves
the model from the vendor rather than from an upload, so the fields it needs
are the ones identifying *which* model, not the ones describing a file.

Fixes F8-F10 add ``s6_fields``: the flat projection of the audit state onto
S6's own field list and vocabulary, so a consumer reads a value rather than
re-deriving one. See :mod:`aaa.integrations.s6_contract`.

Fix F3 (finding S3) adds the warning that had to exist first. Every field check
below asks whether a *value* is present; none of them asked whether the run that
produced the value had actually happened. The 2026-09-03 finclear hand-off passed
all of them while eight of its twenty artefacts were placeholders, so the missing
Phase 1 reached S6 as an empty ``annex_iii_mapping`` and was filed as a schema
gap. Integrity is therefore checked before the fields, and reported first.
"""
from __future__ import annotations

from typing import Any

from aaa.integrations.s6_contract import build_s6_fields
from aaa.integrations.warnings import _integrity_warnings, _model_warnings
from aaa.platform.state.model_vocab import SUPERVISED_TASK_TYPES
from aaa.platform.state.run_integrity import build_run_integrity
from aaa.tools.data_dictionary import explicit_data_dictionary

HANDOFF_SCHEMA_VERSION = "1.0.0"








def build_handoff(state: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Wrap *state* in the hand-off envelope and validate S6-required fields.

    The envelope carries ``run_integrity`` so a consumer can gate on the run
    having happened before it reads a single field — the check that would have
    turned the 2026-09-03 delivery's two schema tickets into one pipeline report.

    :param state: The (JSON-serialisable) audit state.
    :type state: dict[str, Any]
    :returns: ``(payload, warnings)`` — warnings name a degraded run and any
        missing field; the payload is always built (fail-soft).
    :rtype: tuple[dict[str, Any], list[str]]
    """
    stage_b = (state.get("client_submission") or {}).get("stage_b") or {}
    integrity = build_run_integrity(state)
    s6_fields, vocabulary_warnings = build_s6_fields(state)
    warnings: list[str] = (_integrity_warnings(state, integrity)
                           + _model_warnings(stage_b) + vocabulary_warnings)
    task_type = stage_b.get("task_type")
    # Nested or top-level: warning on the top level alone reported a supervised
    # engagement as missing a target column it had declared in its bundle.
    dictionary = explicit_data_dictionary(stage_b)
    if task_type in SUPERVISED_TASK_TYPES and not dictionary.get("target_column"):
        warnings.append("stage_b.target_column missing — required for supervised task types")
    if task_type == "binary_classification" and dictionary.get("positive_label") in (None, ""):
        warnings.append("stage_b.positive_label missing — required for binary classification")
    payload = {
        "handoff_schema_version": HANDOFF_SCHEMA_VERSION,
        "engagement_id": state.get("engagement_id"),
        "run_integrity": integrity,
        "s6_fields": s6_fields,
        "audit_state": state,
    }
    return payload, warnings
