"""When another retrieval round is worth running — fix 18.

``rounds=1`` gave every phase agent exactly one chance to say *these passages do
not answer my question, fetch me these instead*. Raising that ceiling is the
obvious remedy and the dangerous one: the phase timeout covers every LLM call,
a timed-out phase returns **no report at all**, and in the post-fix run a phase
agent's call cost a median of 52.1 s and as much as 106.3 s. Phase 3's rerun
already spent 184.8 s of a 180 s budget on two calls. A plain ``rounds=2`` would
have added a third to every phase and bought more of finding P4.

So the ceiling stops being a count that always runs and becomes one the clock
arbitrates, through two gates asked before each round.

*Can it finish?* Compare the budget left
(:func:`~aaa.platform.phase_budget.remaining_seconds`) against the slowest call
this loop has already made. That estimator is deliberately not a constant: it is
a direct measurement of this model, this payload size and this provider, taken
seconds ago, and it degrades correctly when any of them changes. The gate makes
the higher ceiling free — and it repairs the *existing* ceiling too, because
Phase 3's rerun would have declined its one round (71 s left, 106.3 s last call)
and answered on its seed instead of timing out with nothing.

*Is it paying?* The loop already stopped when retrieval returned literally
nothing. It did not stop when retrieval returned only chunks already in hand,
which costs a full LLM call to learn nothing. After the merge, if no new hit
survived into either list, the model asked a question it already had the answer
to. This gate did not fire in the post-fix run — both observed expansions were
productive — so it is insurance on the second round, where a model that has
already asked its best question is likeliest to repeat itself, rather than a fix
for something observed.

A round refused by either gate is the *final* round, and the model is told so:
:data:`~aaa.tools.evidence_retrieval.terminal_round.TERMINAL_NOTICE` is what
makes answering-from-what-you-have a fair instruction rather than a trap, and it
has to be stamped on the round that actually turns out to be last, not on the
one the ceiling predicted.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.phase_budget import remaining_seconds

logger = logging.getLogger(__name__)

#: Expansion rounds a phase agent may run when the clock allows. Two, because
#: one round gives a miss no second chance and the gates above mean a round that
#: will not fit is not attempted; the budget, not this number, is the binding
#: constraint on every phase the post-fix run measured.
MAX_ROUNDS = 2


def rounds_fit(costs: list[float], ahead: int = 1) -> bool:
    """Whether *ahead* more LLM rounds fit in what is left of the phase's budget.

    :param costs: Wall-clock seconds of each LLM call this loop has made.
    :param ahead: How many further rounds must fit.
    :returns: ``True`` when there is no deadline, nothing measured to judge by,
        or the budget covers *ahead* calls as slow as the slowest so far.
    """
    left = remaining_seconds()
    if left is None or not costs:
        # No budget declared (a unit test, a direct dispatch, or an `_invoke`
        # path that applies no timeout), or nothing measured yet to judge by.
        return True
    return left >= max(costs) * ahead


def round_fits(costs: list[float], agent_name: str = "agent") -> bool:
    """Whether the round about to run fits the budget; says so in the trail if not.

    :param costs: Wall-clock seconds of each LLM call this loop has made.
    :param agent_name: Agent name, for the trail.
    :returns: ``True`` when the round may run.
    """
    if rounds_fit(costs, 1):
        return True
    logger.info(
        "%s: declining a further retrieval round — %.1fs of phase budget left, "
        "and this phase's slowest call took %.1fs. Answering on the evidence in "
        "hand rather than timing out with no report at all.",
        agent_name, remaining_seconds() or 0.0, max(costs))
    return False


def is_final_round(round_idx: int, last: int, costs: list[float]) -> bool:
    """Whether the round now being dispatched is the last one that will run.

    The ceiling is only half the answer. A round is also last when the budget
    will not cover *another* after it — which is why this looks two rounds
    ahead rather than one: the flag is stamped on the payload *before* the call
    it describes, so "can this round run" is already settled and the open
    question is whether anything can follow it. Getting that wrong tells the
    model more retrieval is coming and then runs none, which is precisely the
    unannounced deadline F15 and fix 4 were about.

    :param round_idx: 1-based round being dispatched now.
    :param last: The configured ceiling.
    :param costs: Wall-clock seconds of each LLM call this loop has made.
    :returns: ``True`` when no further round can follow this one.
    """
    return round_idx >= last or not rounds_fit(costs, 2)


def learned_something(before: set[Any], after: set[Any], agent_name: str = "agent") -> bool:
    """Whether a round put any chunk in front of the model that was not there.

    Identity, not length: a round can leave the list the same size while
    displacing a weaker hit at the cap, which *is* new evidence, and a round can
    return a dozen chunks that are all duplicates, which is not.

    :param before: Hit identities held before this round's merge.
    :param after: Hit identities held after it.
    :param agent_name: Agent name, for the trail.
    :returns: ``True`` when at least one identity is new.
    """
    gained = after - before
    if gained:
        return True
    logger.info("%s: retrieval round returned only chunks already in hand; "
                "closing retrieval rather than spending a call to re-read them.",
                agent_name)
    return False


__all__ = ["MAX_ROUNDS", "is_final_round", "learned_something", "round_fits", "rounds_fit"]
