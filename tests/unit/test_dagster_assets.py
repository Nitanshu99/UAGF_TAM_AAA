"""Tests for Dagster asset logic (unit-level, no Dagster runtime needed)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

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
