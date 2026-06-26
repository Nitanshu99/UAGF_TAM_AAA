"""Tests for Dagster asset logic (unit-level, no Dagster runtime needed)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

dagster = pytest.importorskip("dagster", reason="dagster not installed; skipping")


# ---------------------------------------------------------------------------
# LLM cost summary asset
# ---------------------------------------------------------------------------

def test_llm_cost_summary_empty(tmp_path):
    """Asset should return zeros when the audit file does not exist."""
    import aaa.dagster.assets.llm_cost as mod

    orig = mod._AUDIT_JSONL
    mod._AUDIT_JSONL = tmp_path / "nonexistent.jsonl"

    ctx = MagicMock()
    result = mod.llm_cost_summary_asset.__wrapped__(ctx) if hasattr(
        mod.llm_cost_summary_asset, "__wrapped__"
    ) else mod._read_audit_records()

    mod._AUDIT_JSONL = orig

    # Just check the helper returns empty list when file missing
    assert isinstance(result, list)
    assert result == []


def test_llm_cost_summary_with_records(tmp_path):
    """Asset should aggregate tokens and cost from JSONL."""
    import aaa.dagster.assets.llm_cost as mod

    audit_file = tmp_path / "llm_audit.jsonl"
    records = [
        {"agent_name": "A", "model": "gpt-4", "status": "ok",
         "prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150,
         "estimated_cost_usd": 0.005},
        {"agent_name": "B", "model": "gpt-4", "status": "error",
         "prompt_tokens": 20, "completion_tokens": 0, "total_tokens": 20,
         "estimated_cost_usd": 0.001},
    ]
    with audit_file.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    orig = mod._AUDIT_JSONL
    mod._AUDIT_JSONL = audit_file

    result = mod._read_audit_records()

    mod._AUDIT_JSONL = orig

    assert len(result) == 2
    total_cost = sum(r.get("estimated_cost_usd", 0.0) for r in result)
    assert abs(total_cost - 0.006) < 1e-6


def test_llm_cost_summary_skips_bad_json(tmp_path):
    """_read_audit_records must skip malformed lines."""
    import aaa.dagster.assets.llm_cost as mod

    audit_file = tmp_path / "llm_audit.jsonl"
    audit_file.write_text('{"ok": true}\nNOT_JSON\n{"ok": true}\n')

    orig = mod._AUDIT_JSONL
    mod._AUDIT_JSONL = audit_file
    result = mod._read_audit_records()
    mod._AUDIT_JSONL = orig

    assert len(result) == 2  # bad line skipped


def test_llm_cost_summary_empty_asset_emits_float_metadata(tmp_path):
    """Empty audit logs should still produce float-safe Dagster metadata."""
    import aaa.dagster.assets.llm_cost as mod

    orig = mod._AUDIT_JSONL
    mod._AUDIT_JSONL = tmp_path / "nonexistent.jsonl"

    ctx = MagicMock()
    result = mod.llm_cost_summary_asset.op.compute_fn.decorated_fn(ctx)

    mod._AUDIT_JSONL = orig

    assert result["estimated_total_cost_usd"] == 0.0
    ctx.add_output_metadata.assert_called_once()


# ---------------------------------------------------------------------------
# Dagster resources
# ---------------------------------------------------------------------------

def test_evidence_store_resource_creates_store():
    from aaa.dagster.resources import EvidenceStoreResource
    from aaa.platform.evidence import EvidenceStore

    resource = EvidenceStoreResource(backend="memory")
    store = resource.create_evidence_store()
    assert isinstance(store, EvidenceStore)


def test_aaa_settings_resource_returns_settings():
    from aaa.dagster.resources import AAASettingsResource
    from aaa.settings import AAASettings

    resource = AAASettingsResource()
    cfg = resource.get_settings()
    assert isinstance(cfg, AAASettings)


def test_intake_validation_uses_engagement_id_config_and_store_payload():
    import aaa.dagster.assets.intake as mod
    from aaa.api.store import INTAKE_PAYLOADS
    from aaa.platform.evidence import EvidenceStore

    payload = {
        "stage_a": {"provider_name": "Acme", "declared_modality": "ml"},
        "stage_b": {"general_description": "Test system", "model_type": "xgboost"},
    }
    original = dict(INTAKE_PAYLOADS)
    INTAKE_PAYLOADS.clear()
    INTAKE_PAYLOADS["eng-test"] = payload

    ctx = MagicMock()
    ctx.resources.evidence_store = EvidenceStore()
    ctx.op_execution_context.op_config = {"engagement_id": "eng-test"}
    fake_state = {
        "engagement_id": "eng-test",
        "intake_completeness_score": 1.0,
        "declared_risk_tier": "high",
    }

    try:
        with patch("aaa.agents.intake_validator.IntakeValidator") as validator_cls:
            validator_cls.return_value.process = AsyncMock(return_value=fake_state)
            result = mod.intake_validation_asset.op.compute_fn.decorated_fn(ctx)
    finally:
        INTAKE_PAYLOADS.clear()
        INTAKE_PAYLOADS.update(original)

    assert result["engagement_id"] == "eng-test"
    assert result["declared_risk_tier"] == "high"


def test_load_engagement_payload_falls_back_to_persisted_intake():
    import aaa.dagster.assets.intake as mod
    from aaa.api.store import INTAKE_PAYLOADS

    original = dict(INTAKE_PAYLOADS)
    INTAKE_PAYLOADS.clear()

    try:
        with patch("aaa.data.reader.load_intake", return_value={"stage_a": {}, "stage_b": {}}):
            payload = mod._load_engagement_payload("eng-saved")
    finally:
        INTAKE_PAYLOADS.clear()
        INTAKE_PAYLOADS.update(original)

    assert payload["engagement_id"] == "eng-saved"
    assert payload["stage_a"] == {}


def test_dagster_definitions_are_loadable():
    """Dagster code location should validate before `dagster dev` starts."""
    from dagster import Definitions

    from aaa.dagster.definitions import defs

    Definitions.validate_loadable(defs)
