"""How large a phase's budget should be — fix 34 (finding R1).

Every constant below is a reading of the 2026-09-03 five-case run, and each is
here because the number it replaces was not.

**`CALLS_PER_PHASE`.** A phase attempt is not one LLM call. The ReAct loop makes
a seed call and is allowed :data:`~aaa.tools.evidence_retrieval.rounds.MAX_ROUNDS`
expansions after it, and fix 18's clock gate refuses any round the remaining
budget will not cover. A budget that funds one call therefore does not fund a
ceiling of two — it silently reduces it to one, and the phase answers on its seed
whether or not the seed was any good. Forty-five of the run's forty-nine phase
attempts made exactly one call, which reads like a model that rarely wants to
expand and is in fact a budget that rarely let it.

**`MIN_PHASE_SECONDS`, the floor and the cold start.** 300 s is not a new number.
Fix 20 chose it for the Verifier by exactly this reasoning — the smallest round
value above the slowest call the provider actually delivered — and the L-branch
has carried it since long before this run and is the one budget that has never
failed. Making it the floor for every phase generalises the one setting the
evidence already supports, and it answers the cold start: Phase 1 runs before
anything has been measured, has the largest payload in the system (52 kB) and had
the *shortest* budget of any phase (120 s). That inversion is the single line of
this fix that matters most. Every Phase 1 call in the run — 216.8 s at the worst
— fits inside 300 s.

**`MAX_PHASE_SECONDS`, the ceiling.** A measured estimator still needs a bound,
or a pathological call teaches the process to wait for pathological calls. The
slowest phase-agent call the run recorded was 347.8 s (and it *delivered* —
11,480 characters of CGSA analysis, discarded at the 180 s mark). Two such calls
is 695.6 s; 900 s is the next quarter-hour above it, and nothing this system has
ever measured comes near it.

**The retry each call may need (T-20260913-102).** The slowest call measures what
a call costs when the provider delivers; it says nothing of the retry the ladder
makes when the provider is failing. Case 05's Phase 2 was sized at 300 s from a
95.3 s call; its seed call failed after 92.6 s, its retry delivered at 216.1 s,
and the re-prompt that followed had 67 s left. Each funded call therefore also
carries the slowest transient failure recently seen in any phase — none seen,
nothing added: 2 × (95.3 + 96.5) = 383.6 s would have covered it.

**What this does not fix.** Phase 6's LiteLLM *client* ceiling is 120 s while its
phase budget is now at least 300 s, so Phase 6 still cannot use the time it is
given. That inversion is finding R6 and fix 37's to close; widening the phase
budget alone does not touch it.
"""
from __future__ import annotations

import logging

from aaa.platform.phase_budget.observed import slowest_call, slowest_failure

logger = logging.getLogger(__name__)

#: LLM calls one phase attempt must be able to afford: the seed call plus the
#: first expansion round the ReAct ceiling allows.
CALLS_PER_PHASE = 2

#: Floor, and the budget of a phase that runs before anything is measured.
MIN_PHASE_SECONDS = 300.0

#: Ceiling. A measured estimator still must not run away.
MAX_PHASE_SECONDS = 900.0

#: Per-agent floors, for agents whose payload is structurally unlike the pool.
#:
#: The estimator reads *recent phase calls*, whoever made them, and that is right
#: while payloads are comparable. The GovernanceAgent's is not: it carries an
#: entire CGSA governance assessment, and on a real S5 export (2026-09-09) that
#: is **181,595 prompt tokens against ~44,700 for the mock fixture** the estimate
#: was calibrated on — four times the prompt, and 289 s per call against 87–123 s.
#:
#: Phase 5 was therefore given 415 s (2 × a 207.8 s ScopeAgent call) for work
#: costing 289 s a call, was abandoned at that budget, and recorded Art. 9, 12,
#: 14, 17 and 72 as INSUFFICIENT_EVIDENCE — five articles unassessed because the
#: phase was funded from a measurement of different work. That is finding R1
#: again, one level up: R1 was a constant that no longer matched the provider,
#: this is an estimator that does not match the *payload*.
#:
#: 600 s is fix 20's rule applied to this agent's own measurement — the smallest
#: round value above ``289 × CALLS_PER_PHASE``. It is a floor, not an override:
#: a higher derived budget still wins, and the ceiling still binds.
#: ModelValidator is under-funded for a different reason: most of its cost is
#: not an LLM call at all. Before it prompts anything it loads the model and the
#: evaluation set, runs the metric suite, runs explainability (SHAP) and runs the
#: adversarial robustness probe — work the estimator, which reads *recent phase
#: calls*, cannot see. On 2026-09-11 Phase 3 was abandoned at its 300 s floor
#: having spent 56 s of that on its single LLM call: the budget funded roughly a
#: fifth of the work, and T09, T10 and T11 were withheld on the strength of it.
#:
#: It also breaks ``CALLS_PER_PHASE``. Healthy runs of this engagement show
#: ModelValidator making **3-4 calls** totalling 128-188 s, not the two the
#: estimator assumes — so even the derived budget is half the LLM cost before a
#: second of tooling is counted. 600 s is that 188 s worst case plus the
#: measured tooling, rounded up; it is a floor, so a higher derived budget still
#: wins and the 900 s ceiling still binds.
AGENT_MIN_PHASE_SECONDS: dict[str, float] = {
    "GovernanceAgent": 600.0,
    "ModelValidator": 600.0,
}


def phase_timeout(agent_name: str | None = None) -> int:
    """Seconds this phase should be allowed, from what its calls have cost.

    :param agent_name: ``BaseAgent.name`` of the agent about to be dispatched;
        its own history is preferred over the pooled one when it has any, and
        :data:`AGENT_MIN_PHASE_SECONDS` floors the result for the agents whose
        work the pooled estimate is known to under-fund.
    :type agent_name: str | None
    :returns: Whole seconds, always within
        ``[MIN_PHASE_SECONDS, MAX_PHASE_SECONDS]``.
    :rtype: int
    """
    floor = max(MIN_PHASE_SECONDS, AGENT_MIN_PHASE_SECONDS.get(agent_name or "", 0.0))
    measured = slowest_call(agent_name)
    if measured is None:
        return int(floor)
    failure = slowest_failure() or 0.0
    derived = (measured + failure) * CALLS_PER_PHASE
    budget = min(MAX_PHASE_SECONDS, max(floor, derived))
    logger.info(
        "%s: phase budget %.0fs — %d × (the slowest recent phase call %.1fs + the slowest "
        "recent transient failure %.1fs), clamped to [%.0f, %.0f].",
        agent_name or "phase", budget, CALLS_PER_PHASE, measured, failure,
        floor, MAX_PHASE_SECONDS)
    return int(budget)


__all__ = ["AGENT_MIN_PHASE_SECONDS", "CALLS_PER_PHASE", "MAX_PHASE_SECONDS",
           "MIN_PHASE_SECONDS", "phase_timeout"]
