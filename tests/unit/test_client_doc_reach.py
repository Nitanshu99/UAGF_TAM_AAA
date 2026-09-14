"""Which dispatches and spawns can reach the customer's own documents (M13).

Phases 1-4 passed ``client_doc_collection`` in their ``declaration_summary``;
Phase 5 did not, so ``gather_context`` skipped retrieval and the 2026-09-10
Mariposa run assessed Art. 9 governance on ``client_doc_hits: 0`` while Phase 1
read the same dossier successfully. The tier-3 spawns had no retrieval code at
all — the privacy spawn named three documents it needed and could not see.
"""
from __future__ import annotations

import asyncio

import pytest

from aaa.agents.tier1.phases.phase_runners.phase import p1 as phase_1
from aaa.agents.tier1.phases.phase_runners.phase import p2 as phase_2
from aaa.agents.tier1.phases.phase_runners.phase import p3 as phase_3
from aaa.agents.tier1.phases.phase_runners.phase import p4 as phase_4
from aaa.agents.tier1.phases.phase_runners.phase import p5 as phase_5
from aaa.agents.tier3 import client_docs, narrative

_STATE = {"engagement_id": "eng-x", "client_doc_collection": "client_docs_eng_x",
          "client_submission": {"stage_a": {}, "stage_b": {}}}


@pytest.mark.parametrize("module", [phase_1, phase_2, phase_3, phase_4, phase_5])
def test_every_phase_dispatch_carries_the_collection(module):
    """A phase that cannot name the collection cannot open the dossier."""
    source = (module.__file__ or "")
    with open(source, encoding="utf-8") as handle:
        assert "client_doc_collection" in handle.read(), (
            f"{module.__name__} builds a declaration_summary without "
            "client_doc_collection; its client-document retrieval is inert.")


class _Spawn:
    name = "spawn"

    def prompt_note(self, prompt_name, fallback):
        return f"note({prompt_name},{fallback})"


def test_a_spawn_given_no_engagement_searches_nothing(monkeypatch):
    """The default stays the old behaviour: no id, no search."""
    called: list[tuple] = []
    monkeypatch.setattr(client_docs, "seed_client_doc_hits",
                        lambda *a, **k: called.append(a) or [])
    assert narrative._client_docs(_Spawn(), "", "a query") == []
    assert narrative._client_docs(_Spawn(), "eng-x", "") == []
    assert called == []


def test_a_spawn_given_both_searches_the_dossier(monkeypatch):
    monkeypatch.setattr(client_docs, "seed_client_doc_hits",
                        lambda eng, query: [{"text": "…", "source_uri": f"{eng}/{query}"}])
    assert narrative._client_docs(_Spawn(), "eng-x", "retention")[0]["source_uri"] == \
        "eng-x/retention"


def test_a_failing_dossier_costs_hits_not_the_narrative(monkeypatch, caplog):
    """The spawn's measured numbers must survive a retrieval failure."""
    def _boom(*_a, **_k):
        raise RuntimeError("minio down")
    monkeypatch.setattr(client_docs, "seed_client_doc_hits", _boom)
    assert narrative._client_docs(_Spawn(), "eng-x", "retention") == []
    assert "client-document search failed" in caplog.text


def test_the_notice_matches_which_channels_actually_ran(monkeypatch):
    """Telling a model holding hits that no search ran inverts the notice."""
    seen: dict = {}

    async def _fake(_agent, _name, payload, **_kw):
        seen.update(payload)
        return {"summary": "done"}

    monkeypatch.setattr(narrative, "acompletion_json_react", _fake)
    monkeypatch.setattr(client_docs, "seed_client_doc_hits",
                        lambda eng, query: [{"text": "the retention schedule"}])
    asyncio.run(narrative.run_narrative_synthesis(
        _Spawn(), "privacy", {}, keys=("summary",),
        engagement_id="eng-x", client_doc_query="retention"))

    assert seen["client_doc_hits"]
    assert "has been searched for you" in seen["retrieval_expansion"]["notice"]
    assert "no regulatory search" in seen["retrieval_expansion"]["notice"]


def test_a_spawn_with_no_hits_keeps_the_original_closed_notice(monkeypatch):
    seen: dict = {}

    async def _fake(_agent, _name, payload, **_kw):
        seen.update(payload)
        return {"summary": "done"}

    monkeypatch.setattr(narrative, "acompletion_json_react", _fake)
    asyncio.run(narrative.run_narrative_synthesis(
        _Spawn(), "cyber", {}, keys=("summary",), engagement_id="", client_doc_query=""))
    assert seen["client_doc_hits"] == []
    assert seen["retrieval_expansion"] == narrative.SPAWN_RETRIEVAL_CLOSED
