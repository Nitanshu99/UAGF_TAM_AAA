"""Finding Q4 — a tier-3 spawn's narrative has to be an answer, not a plan.

Both spawns replied with retrieval plans where a report was due.
``CyberSecurityAgent`` returned ``{"regulatory_queries": ["Article 15 accuracy
robustness cybersecurity requirements EU AI Act"]}`` — 97 characters — and
``PrivacyDPOAgent`` returned ``{"retrieval_plan": {...}}``.  Neither is a report.
Both artefacts recorded ``llm_fallback_mode=true`` and their
``tier3_llm_narrative`` read, in full, *"Prompt metadata: source=PROMPT.md,
agent_prompt=privacy, …"*.  The numbers in those artefacts are real — the probes
and the PII scan ran — but the reasoning the spawn exists to contribute did not
happen.

This is finding F15's failure mode surviving in the one place fix 10 did not
reach.  Fix 10 gave the phase agents a terminal notice and a closing re-prompt
through :func:`~aaa.tools.evidence_retrieval.acompletion_json_react`; the spawns
called ``agent.acompletion_json`` directly, so they got neither, and a plan in
the answer position was filed without complaint.

Two things change here.  The spawns go through the same wrapper Phase 6 uses
(``rounds=0`` — like Phase 6 they compose from artefacts already in hand), so a
plan-shaped reply is re-prompted once with retrieval explicitly closed and
refused if it comes back.  And the notice is stamped from the **first** call
rather than only on the re-prompt: a spawn has no RAG wired at all, so retrieval
is closed before the first token, and saying so up front is the same courtesy
fix 4 gave the Orchestrator — a model cannot answer to a constraint it was never
given.

What remained open was the other half of the promise: the Agent 11 and Agent 12
prompt sections still tell the model to *"request … via
retrieval_plan.regulatory_queries"*, a channel these spawns do not have.

Half of that is now wired (M13).  Client-document search needs no RAG handle —
:func:`~aaa.tools.evidence_retrieval.seed_client_doc_hits` searches the
engagement's own dossier from an engagement id and a query — so a spawn given
one gets the customer's documents.  It is the half that was costing most: at
call #066 of the 2026-09-10 Mariposa run the privacy spawn named three client
documents it needed, on ``client_doc_hits: 0``, and reduced its confidence to
0.62 for want of them.  Regulatory retrieval stays closed, because that does
need the RegulatoryRAG these spawns are not given, and the notice now says
which of the two channels ran rather than asserting neither did.
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

from aaa.agents.tier3.client_docs import SPAWN_CLIENT_DOCS_SEARCHED, _client_docs
from aaa.tools.evidence_retrieval import acompletion_json_react
from aaa.tools.evidence_retrieval.terminal_round import TERMINAL_NOTICE

logger = logging.getLogger(__name__)

#: Stamped into the spawn's payload before the first call. A tier-3 spawn has no
#: retrieval channel, so its "final round" is its only round.
SPAWN_RETRIEVAL_CLOSED: dict[str, Any] = {
    "round": 0, "final_round": True, "retrieval_closed": True,
    "regulatory_queries": [], "client_doc_queries": [],
    "notice": ("This sub-agent has no retrieval channel: no regulatory or "
               "client-document search will run for it at any point. " + TERMINAL_NOTICE),
}





async def run_narrative_synthesis(agent: Any, prompt_name: str, payload: dict[str, Any],
                                  *, keys: Sequence[str], engagement_id: str,
                                  client_doc_query: str) -> tuple[str | None, str]:
    """Ask a tier-3 spawn's prompt for its narrative, with retrieval closed.

    :param agent: The spawn instance (provides ``acompletion_json``, ``name``
        and ``prompt_note``).
    :param prompt_name: PROMPT.md section name (``cyber`` / ``privacy``).
    :param payload: The user payload for the call.
    :param keys: Reply keys to read the narrative from, in order of preference.
    :param engagement_id: Engagement whose dossier to search; ``""`` disables.
    :param client_doc_query: The spawn's client-document question; ``""``
        disables. Both are required for the search to run (M13), and both are
        required *arguments*: when they had defaults, the L-branch omitted them and
        its search silently never ran (T-20260913-029). Disabling is now a
        visible choice at the call site.
    :returns: ``(narrative or None, prompt_note)`` — ``None`` puts the artefact
        in declared fallback mode, as it always did.
    """
    narrative: str | None = None
    hits = _client_docs(agent, engagement_id, client_doc_query)
    expansion = SPAWN_CLIENT_DOCS_SEARCHED if hits else SPAWN_RETRIEVAL_CLOSED
    try:
        reply = await acompletion_json_react(
            agent, prompt_name,
            {**payload, "client_doc_hits": hits,
             "retrieval_expansion": dict(expansion)},
            rounds=0,
            # Fix 42: the keys this spawn reads *are* its output contract, and
            # asserting them here is what covers all three spawns and the six
            # phase agents with one mechanism rather than three.
            contract=tuple(keys))
        narrative = next(
            (str(reply[key]) for key in keys if str(reply.get(key) or "")), None)
    except Exception as exc:  # noqa: BLE001 — any LLM failure falls back
        logger.warning("%s synthesis failed (%s); deterministic fallback.",
                       getattr(agent, "name", prompt_name), exc)
    if narrative is None:
        logger.warning(
            "%s: no narrative in the reply — the artefact keeps its measured "
            "numbers and declares llm_fallback_mode (Q4).",
            getattr(agent, "name", prompt_name))
    return narrative, agent.prompt_note(prompt_name, narrative is None)


def with_narrative(artefact: dict[str, Any], narrative: str | None,
                   note: str) -> dict[str, Any]:
    """Attach the synthesis narrative + prompt note to *artefact*.

    :param artefact: The T11/T08 extension about to be stored.
    :param narrative: LLM narrative, or ``None`` in fallback mode.
    :param note: Prompt provenance note (records fallback mode).
    :returns: The same artefact, annotated.
    """
    artefact["tier3_llm_narrative"] = f"{narrative} {note}".strip() if narrative else note
    return artefact


__all__ = ["SPAWN_CLIENT_DOCS_SEARCHED", "SPAWN_RETRIEVAL_CLOSED",
           "run_narrative_synthesis", "with_narrative"]
