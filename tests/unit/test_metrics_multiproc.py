"""Multiprocess Prometheus mode: a child process's counter reaches the API view."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from prometheus_client import REGISTRY

from aaa.observability.metrics.multiproc import build_registry, exposition_registry, multiproc_dir

_ROOT = Path(__file__).resolve().parents[2]
_CHILD = (
    "from aaa.observability.metrics import LLM_CALL_COUNTER;"
    "LLM_CALL_COUNTER.labels(agent='child', model='m', status='ok').inc(3)"
)


def test_child_process_counter_is_merged(tmp_path):
    """A value written by another process is read back through the merged registry."""
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"}
    env["PROMETHEUS_MULTIPROC_DIR"] = str(tmp_path)
    subprocess.run([sys.executable, "-c", _CHILD], check=True, env=env, cwd=_ROOT, timeout=120)

    value = build_registry(tmp_path).get_sample_value(
        "aaa_llm_calls_total", {"agent": "child", "model": "m", "status": "ok"})
    assert value == 3.0


def test_single_process_mode_uses_default_registry(monkeypatch):
    """Without the directory, /metrics renders this process's own registry."""
    monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)
    assert multiproc_dir() is None
    assert exposition_registry() is REGISTRY


def test_multiproc_mode_builds_a_merged_registry(tmp_path, monkeypatch):
    """With the directory set, /metrics renders a merged registry, not REGISTRY."""
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", str(tmp_path))
    assert multiproc_dir() == tmp_path
    assert exposition_registry() is not REGISTRY


def test_build_registry_creates_a_missing_directory(tmp_path):
    """A configured-but-absent directory is created, not a 500 on first scrape."""
    missing = tmp_path / "metrics"
    assert not missing.exists()
    build_registry(missing)
    assert missing.is_dir()
