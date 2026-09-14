"""Critiquing a phase's artefacts — concurrently, since they are independent.

**Finding R16.** The Verifier is the most expensive agent in the system, in every
case of the 2026-09-03 run: 43 % to 61 % of each engagement's LLM wall-clock, and
in case 05 eighteen of thirty-six calls with four of them over 200 s. A phase's
artefacts were critiqued in a ``for`` loop, one call each, waiting for each before
starting the next.

**Why concurrency rather than the alternatives.** The backlog offered three, and
two of them buy time with something an audit cannot spend:

* *Batching* — one call carrying a phase's three artefacts — cuts tokens, and
  couples the verdicts. The Verifier would read T09, T10 and T11 together and
  return one judgement over all of them, so a weakness in one could colour
  another and no verdict would be independently attributable. Independence is
  most of what an independent check is.
* *An aggregate budget with a stated degradation* reintroduces exactly what fix 20
  spent a whole fix removing: a critique that did not happen, recorded as
  something other than "did not happen".
* *Concurrency* trades nothing. Each artefact still gets its own call, its own
  verdict, its own audit record and its own ``unverified`` path on failure. What
  changes is only that the calls wait for the provider at the same time.

Replayed over the run's own critique latencies, this halves the Verifier's
wall-clock — 10,152 s of critique across the five cases becomes 5,101 s — without
removing a single call.

**Why it is safe here.** The critiques share no state a task could race on: each
writes ``state["verifier_critiques"][tid]`` under its own key, reads the artefact
store read-only, and the worst-verdict fold runs afterwards in ``tid_articles``
order, so the result does not depend on which call returned first.
:data:`MAX_CONCURRENT_CRITIQUES` bounds the burst — a phase emits at most three
artefacts today, and the provider's free tier allows forty requests a minute, but
a cap that is stated cannot be exceeded by a phase that grows.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

from aaa.agents.tier1.phases.verification.critique_artefact import _critique_artefact  # noqa: F401
from aaa.agents.tier1.phases.verification.finish_phase import _finish_phase  # noqa: F401
from aaa.agents.tier1.phases.verification.logger import (  # noqa: F401
    _REPORT_TIDS,
    _VERDICT_ORDER,
    _VERIFIER,
    _artefact_content,
    _artefact_uri,
    _get_verifier,
    _worse,
    logger,
)
from aaa.agents.tier1.phases.verification.merge_critique import _merge_critique  # noqa: F401
from aaa.agents.tier1.verifier import Verifier


def _max_concurrent() -> int:
    """Critiques a phase may have in flight. Override: ``MAX_CONCURRENT_CRITIQUES``.

    Three, because that is the most artefacts any phase emits, so the default
    never truncates a phase that exists today. An operator on a tighter provider
    quota can lower it to 1 and get the old serial behaviour back exactly.
    """
    raw = os.getenv("MAX_CONCURRENT_CRITIQUES")
    if not raw:
        return 3
    try:
        return max(1, int(raw))
    except ValueError:
        logger.warning("MAX_CONCURRENT_CRITIQUES=%r is not an integer; using 3.", raw)
        return 3


MAX_CONCURRENT_CRITIQUES: int = _max_concurrent()


async def _verify_artefacts(verifier: Verifier, agent: Any, dispatch: Any,
                            state: dict, tid_articles: dict[str, list[str]],
                            phase_label: str, confidence: float,
                            rerun_count: int) -> str:
    """Critique every produced artefact concurrently; return the worst verdict.

    :returns: The worst verdict across the phase's artefacts, folded in
        ``tid_articles`` order so it does not depend on completion order.
    """
    gate = asyncio.Semaphore(MAX_CONCURRENT_CRITIQUES)

    async def _one(tid: str, articles: list[str]) -> str:
        async with gate:
            return await _critique_artefact(
                verifier, agent, state, tid, articles, phase_label, confidence,
                phase_id=dispatch.get("phase_id", ""),
                evidence_uris=list(dispatch.get("evidence_uris", []) or []),
                rerun_count=rerun_count,
                declaration_summary=dict(dispatch.get("declaration_summary", {}) or {}))

    if len(tid_articles) > 1:
        logger.info("%s: critiquing %d artefact(s), up to %d at a time.",
                    phase_label, len(tid_articles), MAX_CONCURRENT_CRITIQUES)
    verdicts = await asyncio.gather(
        *(_one(tid, articles) for tid, articles in tid_articles.items()))

    worst = "accept"
    for verdict in verdicts:
        worst = _worse(worst, verdict)
    return worst
