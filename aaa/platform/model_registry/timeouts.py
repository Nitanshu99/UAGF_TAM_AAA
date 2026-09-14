"""Per-agent LLM ceilings (findings P6, P8).

Every agent shared one ceiling, ``LLM_TIMEOUT_SECONDS`` (120 s), and the
Verifier is the agent least able to live inside it.  It is the most expensive
call in the system — 47% of the post-fix run's calls, the largest prompts, and
the longest replies, because a critique is a structured judgement rather than a
sentence — and it is the only agent whose failure is silent: a phase agent that
raises produces no report and the phase is recorded as having produced nothing
(F3), while a Verifier that raises falls back to a deterministic rubric that
returns a verdict looking exactly like a real one.

The run's own numbers set the constant.  Of 21 Verifier calls, 16 returned and
5 failed; the failures include four ``litellm.Timeout``\\s reporting
``timeout value=120.0`` at 139.2 s, 140.9 s, 246.6 s and 253.1 s.  The two
slowest *successful* calls took 225.2 s and 240.3 s — from the same provider,
in the same run.  So 120 s abandoned work this provider demonstrably delivers,
and any ceiling at or below 240.3 s would still have abandoned the slowest call
that actually came back.  300 s is the smallest round value above it.

The phase agents keep 120 s deliberately.  Their slowest call was 106.3 s, and
their LLM calls sit *inside* a 120 s / 180 s phase timeout that fix 18's budget
gates are calibrated against — raising their ceiling would let one call spend a
phase's whole budget.  The Verifier runs after ``run_agent_on_state`` returns,
outside that timeout, so a longer ceiling here cannot cost a phase its report.

----

**Fix 37 (finding R6) retires the paragraph above for the phase agents.** Its
reasoning — "raising their ceiling would let one call spend a phase's whole
budget" — assumed the ceiling and the budget were independent numbers that had to
be balanced against each other. They are not, and treating them as such produced
the inversion R6 names: the ReportArchitect was given a **180 s phase budget and
a 120 s client ceiling**, so Phase 6 was structurally unable to use the time it
was allocated, and failed identically in two cases:

    case 01 #044   litellm.Timeout … timeout value=120.0, time taken=186.98 s
    case 03 #045   litellm.Timeout … timeout value=120.0, time taken=186.99 s

Fix 34 then widened the gap rather than closing it: a derived phase budget of
300–695 s above a client ceiling still fixed at 120 s.

:func:`resolve_client_timeout` makes them **one number with two consumers**. A
call made inside a phase is given the time the phase has *left* — never less,
which is R6, and never more, which would be time the runner will not wait for
anyway. "One call spending a phase's whole budget" is now the correct outcome
rather than the risk: if the phase has 200 s left and the call needs all of it,
abandoning at 120 s buys nothing but a lost report.

A call made **outside** a phase deadline is unchanged, and that is what preserves
fix 20: the Verifier runs after ``run_agent_on_state`` returns, binds no
deadline, and keeps the explicit 300 s ceiling this module gives it.

----

**Fix 46 (finding R14): fix 20's premise held; its enforcement did not.** Case 04
call #024 ran **319.7 s against this module's 300 s ceiling and returned ``ok``**,
and a ceiling that does not bound what it names undermines the measurement that
set it. The mechanism is not a guess — it is two lines of the client beneath
litellm:

* ``openai/_base_client.py`` loops ``for retries_taken in range(max_retries + 1)``
  and **builds the request inside that loop**, so ``timeout`` bounds one attempt.
* ``litellm/llms/openai/openai.py`` passes ``max_retries`` straight to
  ``AsyncOpenAI(...)``, defaulted to ``DEFAULT_MAX_RETRIES`` — **2** in both
  packages.

So the wall-clock a ceiling of *N* seconds actually bounded was ``N × 3`` plus
backoff, while ``latency_ms`` recorded the whole sequence. The two were never
commensurable, which is why 17 calls in that run returned ``ok`` past a 120 s
ceiling — one at 347.8 s.

**Fix 20's *rule* does not change; its *number* does.** It derived 300 s from
whole-call latencies — *"the two slowest successful calls took 225.2 s and
240.3 s"* — so a per-attempt reading was never what it meant.
:data:`aaa.platform.flex_retry.logger.CLIENT_MAX_RETRIES` is now ``0``, so the
ceiling bounds the call the trail measures, and fix 39's retry is this codebase's
only one — bounded, budget-aware and recorded as ``attempts``. But a bound that
binds for the first time has to be sized against what it will now cut off, and
the slowest Verifier call that *came back* in this run was 319.7 s, not 240.3 s.
Applying fix 20's own rule to fix 20's own successor data gives **360 s**.
"""
from __future__ import annotations

from aaa.platform.flex_retry.logger import _timeout

#: 6 minutes for the Verifier. Override: ``VERIFIER_TIMEOUT_SECONDS``.
#:
#: Fix 20 set this to 300 s by a rule — *the smallest round value above the
#: slowest call that actually came back* — using the data it had: 240.3 s. Fix 46
#: made the ceiling bind for the first time, and the same rule against the
#: 2026-09-03 run gives a different answer: the Verifier's slowest **successful**
#: call was **319.7 s** (case 04 #024), which a 300 s ceiling now cuts off.
#:
#: 360 s is the smallest round value above it. The number changed because the
#: measurement did; the rule is fix 20's, unaltered.
VERIFIER_TIMEOUT_SECONDS: float = _timeout("VERIFIER_TIMEOUT_SECONDS", 360.0)


#: 6 minutes for the Orchestrator's decide loop. Override: ``ORCHESTRATOR_TIMEOUT_SECONDS``.
#:
#: It runs *outside* any phase deadline, so fix 37's rule does not reach it and it
#: took the 120 s platform default — while its calls in the 2026-09-03 run ran to
#: **303.7 s** and returned. That worked only because the ceiling was silently
#: tripled underneath (fix 46), and fix 46 removed the tripling. Left alone, the
#: three Orchestrator calls that ran past 120 s in that run would now be cut off,
#: and losing a decide call costs a turn (fix 45) or, twice over, the loop.
#:
#: 360 s by fix 20's rule — the smallest round value above the slowest call that
#: actually came back — applied to this agent's own measurements.
ORCHESTRATOR_TIMEOUT_SECONDS: float = _timeout("ORCHESTRATOR_TIMEOUT_SECONDS", 360.0)


#: 7 minutes for the ClientBrief. Override: ``CLIENT_BRIEF_TIMEOUT_SECONDS``.
#:
#: Measured on the 2026-09-09 Mariposa brief, the first run this agent made: 19
#: calls, of which **17 returned and 2 were cut off** — a ``litellm.Timeout``
#: reporting ``timeout value=120.0`` at 211.6 s (the Art. 17 section) and again
#: at 312.2 s (the opening). Both fell back to their deterministic assembly, so
#: the customer's document lost two of its written sections to a ceiling and not
#: to anything the provider failed to deliver.
#:
#: The slowest call that *did* come back took **385.8 s**, from the same provider
#: in the same run, so any ceiling at or below it would still abandon work this
#: endpoint demonstrably completes — reasoning is on by default across the
#: Nemotron 3 family, and a per-article section is a long structured reply.
#: 420 s is the smallest round value above it. Fix 20's rule, this agent's data.
CLIENT_BRIEF_TIMEOUT_SECONDS: float = _timeout("CLIENT_BRIEF_TIMEOUT_SECONDS", 420.0)


#: Agents whose LLM ceiling differs from the platform default. Absence means
#: "the default", not "no ceiling" — an agent must not be able to opt out of
#: one by being unlisted.
#:
#: The first two run **outside** a phase deadline, which is why they need one:
#: inside a phase, fix 37 makes the ceiling the remaining budget and a second
#: constant beside it is how finding R6 happened.
#:
#: ``ClientBrief`` is the first agent to sit on **both** sides of that rule. In a
#: pipeline run it is dispatched through ``run_agent_on_state`` and takes the
#: remaining phase budget, exactly as fix 37 intends — its entry here changes
#: nothing, because that budget (one call per audited article) is far above
#: 420 s. Regenerated from a saved state by ``python -m aaa brief`` it binds no
#: deadline at all, fell through to the 120 s platform default, and that is the
#: path the two lost sections above were written on.
AGENT_TIMEOUTS: dict[str, float] = {
    "Verifier": VERIFIER_TIMEOUT_SECONDS,
    "Orchestrator": ORCHESTRATOR_TIMEOUT_SECONDS,
    "ClientBrief": CLIENT_BRIEF_TIMEOUT_SECONDS,
}


def resolve_client_timeout(explicit: float | None, default: float) -> float:
    """The seconds this call may take: the phase's remaining budget, or *default*.

    One number, two consumers — fix 37. Inside a phase dispatch the wall-clock
    budget is bound (:func:`aaa.platform.phase_budget.bind_phase_deadline`), and
    the client ceiling is read from it rather than declared beside it, so the two
    cannot drift apart again. Outside one — the Verifier, the Orchestrator's
    decide loop, a unit test — the caller's explicit ceiling or the platform
    default applies, exactly as before.

    :param explicit: A ceiling the caller set (the Verifier's 300 s, fix 20).
    :param default: The platform default for this tier of call.
    :returns: Seconds, always positive.
    """
    from aaa.platform.phase_budget import remaining_seconds

    left = remaining_seconds()
    if left is not None and left > 0:
        # A spent budget (left <= 0) falls through: the runner has already given
        # up, and a zero or negative ceiling is not a number litellm can use.
        return left
    return explicit or default


def resolve_timeout(agent_name: str, override: float | None = None) -> float | None:
    """Return the LLM ceiling for *agent_name*, or ``None`` for the default.

    :param agent_name: ``BaseAgent.name``, as the model registry keys it.
    :param override: An explicit ceiling from the caller, which wins.
    :returns: Seconds, or ``None`` when this agent takes the platform default.
    """
    if override is not None:
        return override
    return AGENT_TIMEOUTS.get(agent_name)


__all__ = ["VERIFIER_TIMEOUT_SECONDS", "ORCHESTRATOR_TIMEOUT_SECONDS",
           "CLIENT_BRIEF_TIMEOUT_SECONDS", "AGENT_TIMEOUTS", "resolve_timeout",
           "resolve_client_timeout"]
