"""T-20260914-014: RAGAS_MAX_WORKERS sets the judge concurrency; unset keeps ragas's default."""
from __future__ import annotations

import pytest

from aaa.tools.ragas_eval.compute.run_config import run_config

pytest.importorskip("ragas")


def test_the_setting_is_read_and_a_bad_value_is_ignored(monkeypatch) -> None:
    """4 → 4; unset or nonsense → ragas's own 16."""
    monkeypatch.delenv("RAGAS_MAX_WORKERS", raising=False)
    assert run_config().max_workers == 16
    monkeypatch.setenv("RAGAS_MAX_WORKERS", "4")
    assert run_config().max_workers == 4
    monkeypatch.setenv("RAGAS_MAX_WORKERS", "many")
    assert run_config().max_workers == 16
