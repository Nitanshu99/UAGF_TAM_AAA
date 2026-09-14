"""The client's uploaded system prompt must reach the analyses that ask for it.

``decl["system_prompt_text"]`` was read in two places — the L-branch injection
analysis and the CyberSecurity specialist probes — and written in none. The
client uploads ``system_prompt_uri``, it counts toward the 80 % completeness
gate, the report lists it, and both analyses were handed ``None``. Mariposa's is
kilobytes of real instructions, and it
was never read while that system was audited for injection resilience.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from aaa.tools.prompt_injection_suite import prompt_injection_suite
from aaa.tools.system_prompt_text import resolve_system_prompt

CASE = pathlib.Path("mock/06_mariposa_edu_gmbh")


@pytest.fixture(name="bundle_loader")
def _bundle_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolve the bundle's relative paths the way the evidence store would."""
    def _read(uri: str, _store: Any = None, _kind: str | None = None) -> str:
        path = pathlib.Path(uri)
        if not path.is_file():
            path = CASE / pathlib.Path(*path.parts[1:])
        return path.read_text("utf-8")
    monkeypatch.setattr(
        "aaa.platform.artifact_loader.load_artifact_from_uri", _read)


@pytest.mark.skipif(not CASE.is_dir(), reason="mock bundle not present")
def test_the_uploaded_system_prompt_is_resolved(bundle_loader: None) -> None:
    """The exact regression: a supplied prompt must not resolve to None."""
    stage_b = json.loads((CASE / "stage_b.json").read_text("utf-8"))
    text = resolve_system_prompt(stage_b, None)
    assert text and len(text) > 1000


@pytest.mark.skipif(not CASE.is_dir(), reason="mock bundle not present")
def test_the_resolved_prompt_produces_a_real_observation(
        bundle_loader: None) -> None:
    """Static analysis of the real prompt, not of nothing."""
    stage_b = json.loads((CASE / "stage_b.json").read_text("utf-8"))
    result = prompt_injection_suite(None, resolve_system_prompt(stage_b, None))
    assert result["method"] == "static_prompt_analysis"
    assert result["observations"]


def test_no_uri_resolves_to_none() -> None:
    """Nothing supplied, nothing invented."""
    assert resolve_system_prompt({}, None) is None


def test_an_unreadable_prompt_is_not_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    """The phase must still run when the document cannot be read."""
    def _boom(*_a: object, **_k: object) -> Any:
        raise OSError("gone")
    monkeypatch.setattr(
        "aaa.platform.artifact_loader.load_artifact_from_uri", _boom)
    assert resolve_system_prompt({"system_prompt_uri": "minio://e/p.txt"}, None) is None


@pytest.mark.parametrize("path", [
    "aaa/agents/tier3/uagf_tam_l/gather.py",
    "aaa/agents/tier3/cyber_agent/inputs.py",
])
def test_both_branches_resolve_it(path: str) -> None:
    """Guards the call sites: the field was dead in both."""
    assert "resolve_system_prompt" in pathlib.Path(path).read_text("utf-8")


@pytest.mark.parametrize("source,needle", [
    ("aaa/agents/tier3/cyber_agent/probes.py", 'injection["vulnerability_rate"] >'),
    ("aaa/agents/tier3/uagf_tam_l/evals.py", 'injection["vulnerability_rate"] >'),
])
def test_no_branch_compares_an_unmeasured_rate(source: str, needle: str) -> None:
    """`vulnerability_rate` is None when nothing was probed; `>` would raise."""
    assert needle not in pathlib.Path(source).read_text("utf-8")
