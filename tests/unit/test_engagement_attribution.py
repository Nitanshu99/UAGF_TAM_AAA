"""Fix 12 (finding F7): every LLM call of an engagement must name the engagement.

``bind_engagement_id`` wrapped ``agent_runner._invoke`` only, so it covered the
phase agents and nothing else. The Orchestrator's own ReAct turns and every
Verifier critique run *outside* ``_invoke`` — 34 of the assessed run's 37 calls —
and reached the append-only trail with ``engagement_id: None``. In a trail that
never truncates, a record that cannot be attributed to a run cannot be read at
all; separating two runs was the reason the field was added.

The binding now sits in ``orchestrator.runner.run``, the one method the API, the
CLI and the wizard all reach the pipeline through.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import pytest

from aaa.agents.tier1.orchestrator import runner as runner_mod
from aaa.agents.tier1.orchestrator.react import loop as loop_mod
from aaa.agents.tier1.phases.agent_runner.logger import _invoke
from aaa.observability.trace_context import bind_engagement_id, current_engagement_id

_ROOT = Path(__file__).resolve().parents[2]

#: the three production entry points, as fix 1 enumerated them.
_ENTRY_POINTS = (
    "aaa/api/routes/workflow/run.py",
    "aaa/cli/cmd/run.py",
    "aaa/ui/wizard/pipeline.py",
)


class _StubSelf:
    """Stands in for the Orchestrator instance ``runner.run`` is bound to."""

    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}
        self._graph = None

    def _build_graph(self, checkpointer: Any | None = None) -> Any:
        """No compiled graph in this stub."""
        return None


async def _record_seen(seen: dict, *_: Any, **__: Any) -> dict:
    """Stand in for a pipeline runner, recording what is bound when it runs."""
    seen["during"] = current_engagement_id()
    return {}


# --------------------------------------------------------------------------- #
# the replay — the trail F7 was found in
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_the_trail_attributes_the_orchestrator_and_verifier_records(
        monkeypatch, tmp_path):
    """The assessed run's own evidence: 'engagement_id empty on all records'.

    Drives the real ``Orchestrator`` and the real ``Verifier`` — their genuine
    ``acompletion`` → ``write_audit`` path, failing on the blanked provider key
    exactly as an error record would in production — once through
    ``runner.run`` and once through ``run_react`` directly, which is what the
    assessed run's stack amounted to.
    """
    from aaa.agents.tier1.orchestrator.agent import Orchestrator
    from aaa.agents.tier1.verifier import Verifier
    from aaa.observability.llm_audit import record

    monkeypatch.setenv("AAA_ORCHESTRATION_MODE", "react")
    monkeypatch.setattr(loop_mod, "node_stage0", lambda s: s)
    monkeypatch.setattr(loop_mod, "MAX_TURNS", 1)

    async def wrapup(_agents: Any, state: dict, _history: list) -> dict:
        """Stand in for the wrap-up, but critique through the real Verifier."""
        await Verifier().process({"phase_id": "P2", "template_id": "T06_datasheet",
                                  "content": {"num_instances": 100},
                                  "evidence_uris": []})
        return state
    monkeypatch.setattr(loop_mod, "deterministic_wrapup", wrapup)

    orch = Orchestrator()
    state = {"engagement_id": "eng-01_finclear_gmbh"}

    def _ids(trail: Path) -> dict[str, set[str | None]]:
        seen: dict[str, set[str | None]] = {}
        for line in trail.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            seen.setdefault(rec["agent"], set()).add(rec["engagement_id"])
        return seen

    unbound = tmp_path / "assessed.jsonl"
    monkeypatch.setattr(record, "_AUDIT_JSONL", unbound)
    await loop_mod.run_react(orch, {}, dict(state))       # the assessed stack
    assert _ids(unbound) == {"Orchestrator": {None}, "Verifier": {None}}

    bound = tmp_path / "fixed.jsonl"
    monkeypatch.setattr(record, "_AUDIT_JSONL", bound)
    await runner_mod.run(orch, dict(state))               # after fix 12
    assert _ids(bound) == {"Orchestrator": {"eng-01_finclear_gmbh"},
                           "Verifier": {"eng-01_finclear_gmbh"}}


# --------------------------------------------------------------------------- #
# the binding, on both execution paths
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_run_binds_the_engagement_for_the_react_path(monkeypatch):
    """The ReAct loop — where the Orchestrator's own calls are made."""
    seen: dict[str, Any] = {}
    monkeypatch.setenv("AAA_ORCHESTRATION_MODE", "react")
    monkeypatch.setattr(loop_mod, "run_react",
                        lambda *a, **k: _record_seen(seen, *a, **k))
    await runner_mod.run(_StubSelf(), {"engagement_id": "eng-42"})
    assert seen["during"] == "eng-42"


@pytest.mark.asyncio
async def test_run_binds_the_engagement_for_the_deterministic_path(monkeypatch):
    """The offline/CI fallback runs the same agents and must be attributable too."""
    seen: dict[str, Any] = {}
    monkeypatch.setenv("AAA_ORCHESTRATION_MODE", "graph")
    monkeypatch.setattr(runner_mod, "run_sequential",
                        lambda agents, state: seen.setdefault(
                            "during", current_engagement_id()))
    await runner_mod.run(_StubSelf(), {"engagement_id": "eng-42"})
    assert seen["during"] == "eng-42"


@pytest.mark.asyncio
async def test_the_binding_does_not_outlive_the_engagement(monkeypatch):
    """A binding that leaked would attribute the *next* run's calls to this one."""
    monkeypatch.setenv("AAA_ORCHESTRATION_MODE", "react")
    monkeypatch.setattr(loop_mod, "run_react", lambda *a, **k: _record_seen({}, *a))
    await runner_mod.run(_StubSelf(), {"engagement_id": "eng-42"})
    assert current_engagement_id() is None


@pytest.mark.asyncio
async def test_an_engagement_without_an_id_binds_nothing(monkeypatch):
    """Missing id must not raise and must not bind a falsy session tag."""
    seen: dict[str, Any] = {}
    monkeypatch.setenv("AAA_ORCHESTRATION_MODE", "react")
    monkeypatch.setattr(loop_mod, "run_react",
                        lambda *a, **k: _record_seen(seen, *a, **k))
    await runner_mod.run(_StubSelf(), {})
    assert seen["during"] is None


# --------------------------------------------------------------------------- #
# the inner binding must narrow, never clear
# --------------------------------------------------------------------------- #

class _Agent:
    """Stub phase agent recording the engagement id bound during process()."""

    def __init__(self, seen: dict) -> None:
        self._seen = seen

    async def process(self, _dispatch: Any) -> dict:
        """Record the currently-bound engagement id."""
        self._seen["during"] = current_engagement_id()
        return {}


@pytest.mark.asyncio
async def test_a_dispatch_without_an_id_keeps_the_engagement_binding():
    """The trap the outer binding creates: an inner bind(None) that unbinds.

    Phase dispatches carry the engagement id in ``declaration_summary``, but not
    all of them declare one. Before this fix that was harmless — nothing was
    bound outside ``_invoke`` anyway. With the engagement bound around the run,
    setting ``None`` here would strip it for exactly the calls fix 12 exists to
    attribute.
    """
    seen: dict[str, Any] = {}
    with bind_engagement_id("eng-42"):
        await _invoke(_Agent(seen), {"declaration_summary": {}}, timeout=5)
    assert seen["during"] == "eng-42"


@pytest.mark.asyncio
async def test_a_dispatch_with_its_own_id_still_narrows_to_it():
    """Narrowing stays possible — only clearing is refused."""
    seen: dict[str, Any] = {}
    with bind_engagement_id("eng-42"):
        await _invoke(_Agent(seen),
                      {"declaration_summary": {"engagement_id": "eng-99"}}, timeout=5)
        assert seen["during"] == "eng-99"
        assert current_engagement_id() == "eng-42"


def test_the_engagement_binding_survives_the_worker_thread_hop():
    """Phase agents run through ``run_coro_blocking`` when a loop is already up."""
    from aaa.platform.async_timeout import run_coro_blocking

    async def read() -> str | None:
        return current_engagement_id()
    with bind_engagement_id("eng-42"):
        assert run_coro_blocking(read(), timeout=5) == "eng-42"


# --------------------------------------------------------------------------- #
# where the binding lives
# --------------------------------------------------------------------------- #

def test_the_bound_method_is_the_one_the_orchestrator_exposes():
    """Binding inside ``run`` is what makes a new entry point safe by default."""
    from aaa.agents.tier1.orchestrator.agent import Orchestrator

    assert Orchestrator.run is runner_mod.run


@pytest.mark.parametrize("path", _ENTRY_POINTS)
def test_no_entry_point_bypasses_the_bound_method(path):
    """A caller reaching ``run_react``/``run_sequential`` directly is unbound."""
    tree = ast.parse((_ROOT / path).read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"run_react", "run_sequential", "_run"}, path
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr == "run" for node in ast.walk(tree)), path


def test_the_upload_path_makes_no_unbound_model_call():
    """The wizard's pre-Orchestrator path must not reach a model unbound.

    F7 was about ``run_extraction``: the DocIntelligence call ran before the
    Orchestrator bound the engagement, so its completions reached the audit
    trail with no engagement id, and it was wrapped in ``bind_engagement_id``.

    That call is gone — the wizard indexes the uploads and no longer asks a
    model to read them — so the property now holds by there being nothing to
    bind. Asserted as the invariant rather than as the old wrapper, so putting
    an agent back into the upload path without binding it fails here again.
    """
    source = (_ROOT / "aaa/ui/wizard/pipeline.py").read_text(encoding="utf-8")
    # The next definition is `async def run_pipeline`, which legitimately drives
    # agents — splitting on a bare "\ndef " would swallow it and always fail.
    body = source.split("def ingest_documents", 1)[1]
    ingest = re.split(r"\n(?:async )?def ", body, maxsplit=1)[0]
    reaches_a_model = ".process(" in ingest or "Agent(" in ingest
    assert not reaches_a_model or "bind_engagement_id(engagement_id)" in ingest
