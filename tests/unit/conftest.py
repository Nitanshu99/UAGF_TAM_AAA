"""Network and infrastructure isolation for the unit suite.

Unit tests exercise real agent code paths, and those agents call an LLM when a
provider key is present. Because :class:`AAASettings` is configured with
``env_file=".env"``, a developer's repo-root ``.env`` reaches the settings
singleton even when the shell exports nothing — so the suite would issue live
NIM/OpenAI calls and export OTEL spans, turning a ~5s run into minutes and
spending real quota. This fixture blanks both layers (process environment and
the already-constructed settings singleton) for every unit test.

``EVIDENCE_BACKEND`` leaks the same way and is pinned for the same reason. Once
fix 22 made ``minio`` the right setting for a real run, an unpinned suite reached
the developer's live object store and *wrote* to it — one run left 77 objects in
``aaa-evidence``. A unit test must not depend on infrastructure, and must
certainly not put anything in it.

Scoped to ``tests/unit`` on purpose: e2e / contract tests legitimately need
live credentials and are selected by their own markers.
"""
from __future__ import annotations

import pytest

#: Credentials whose presence causes an agent, tracer, or vector client to
#: reach the network. Blanked rather than deleted so code that reads them
#: unconditionally still finds a (falsy) value.
_CREDENTIAL_VARS = (
    "OPENAI_API_KEY", "OPENAI_API_BASE",
    "NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY", "NVIDIA_NIM_API_BASE",
    # Absent until 2026-09-09, when `.env` moved to `PROVIDER=openrouter` and
    # the omission stopped being theoretical: the suite issued live calls on the
    # OpenRouter route, ran **17m30s instead of 2m20s**, and spent real quota —
    # the exact failure this fixture's docstring describes. A roster is only
    # isolated here if *every* key it can resolve through is blanked.
    "OPENROUTER_API_KEY", "OPENROUTER_API_BASE",
    "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY",
    "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY",
    "QDRANT_URL", "QDRANT_API_KEY",
)

#: Matching fields on the settings singleton (populated from ``.env``).
_SETTINGS_FIELDS = (
    "openai_api_key", "nvidia_api_key", "anthropic_api_key", "deepseek_api_key",
    "langfuse_public_key", "langfuse_secret_key", "qdrant_url", "qdrant_api_key",
)


@pytest.fixture(autouse=True)
def _no_live_providers(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Blank every provider credential for the duration of one unit test.

    Also redirects the LLM audit trail to a temp file: agents still exercise
    their real fallback paths (which log an error entry), but the production
    ``logs/audit/llm_audit.jsonl`` — the cost-analysis artefact — stays clean.

    :param monkeypatch: pytest's environment/attribute patcher.
    :type monkeypatch: pytest.MonkeyPatch
    :param tmp_path: Per-test temporary directory.
    :type tmp_path: pathlib.Path
    :returns: None
    """
    for name in _CREDENTIAL_VARS:
        monkeypatch.setenv(name, "")

    # Single patch point: record.py owns the JSONL path for every writer
    # (BaseAgent.write_audit delegates to its _write_jsonl).
    from aaa.observability.llm_audit import record
    monkeypatch.setattr(record, "_AUDIT_JSONL", tmp_path / "llm_audit.jsonl")
    # Force the deterministic orchestration path: the ReAct loop is selected
    # by the presence of a provider key, which tests must never rely on.
    monkeypatch.setenv("AAA_ORCHESTRATION_MODE", "graph")
    # The evidence store is process-local for a unit test, whatever `.env` says.
    monkeypatch.setenv("EVIDENCE_BACKEND", "memory")
    # And so is the roster, for determinism rather than for speed: which models a
    # test resolves must not depend on which provider a developer's `.env`
    # happens to select, and `openai` is the value `active_provider()` already
    # returns when `PROVIDER` is unset. Measured, so the reason stays honest:
    # pinning this is worth *nothing* in wall-clock — one API test ran 2m22s
    # under `openai` and 2m22s under `nvidia` — because a blanked key costs the
    # same ~5s per call whichever roster names the model. The suite's cost is the
    # *number* of doomed calls, which is why the ClientBrief breaker
    # (`FAILURES_BEFORE_GIVING_UP`) mattered here and this line does not.
    monkeypatch.setenv("PROVIDER", "openai")

    from aaa.settings import settings
    for field in _SETTINGS_FIELDS:
        if hasattr(settings, field):
            monkeypatch.setattr(settings, field, "", raising=False)
    monkeypatch.setattr(settings, "evidence_backend", "memory", raising=False)

    from aaa.observability import tracing
    tracing.reset_llm_tracing_state()
