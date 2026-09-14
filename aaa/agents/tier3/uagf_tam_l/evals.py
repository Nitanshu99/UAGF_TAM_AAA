"""Golden-set evaluation and verdict heuristics for the L-branch."""
from __future__ import annotations

from typing import Any


def eval_inputs(decl: dict[str, Any],
                golden_set: tuple[list, list, list, list] | None = None,
                ) -> tuple[list, list, list, list]:
    """Resolve evaluation inputs from a real golden set, or demo defaults.

    :param decl: Declaration summary from the dispatch.
    :param golden_set: Resolved ``(questions, contexts, answers, expected)``
        from ``golden_set_uri``
        (:func:`aaa.agents.tier3.uagf_tam_l.golden_set.resolve_golden_set`);
        takes precedence over ``decl`` keys and the hardcoded demo defaults
        when non-empty.
    :returns: ``(questions, contexts, answers, expected)``; all four empty when
        the client supplied no golden set and the caller named no evaluation
        data, which ``run_golden_set`` reports as unsupplied.
    """
    if golden_set and golden_set[0]:
        return golden_set
    # No hardcoded pairs. Two demo questions about the EU AI Act used to stand in
    # whenever a client supplied no golden set, and the pass rate computed from
    # them was published in the client's report as if it measured their system.
    # A caller may still supply evaluation data explicitly; absent that, the
    # honest answer is that there is nothing to evaluate.
    questions = decl.get("eval_questions") or []
    contexts = decl.get("eval_contexts") or []
    answers = decl.get("eval_answers") or []
    expected = decl.get("eval_expected") or []
    return questions, contexts, answers, expected
