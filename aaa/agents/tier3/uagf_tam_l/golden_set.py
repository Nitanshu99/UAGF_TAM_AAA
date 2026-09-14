"""Resolves the client-submitted golden Q&A evaluation set for the L-branch.

``golden_set_uri`` (Annex IV, LLM/agentic-only) points at a JSON file or CSV of
aligned rows — the RAGAs-standard ``{question, context, answer, expected}``
shape ``eval_inputs``/``ragas_eval``/``run_golden_set`` consume.

Two shapes reach it and only one used to work. Case 04 ships a bare array whose
rows carry ``answer`` and ``expected``. Case 06 ships
``{name, version, count, items: [...]}`` whose 55 rows carry ``question`` and
``reference_answer`` — a *reference* set, with no system answer, because the
system under test has not been run against it yet. Both were rejected: the
wrapper was never opened, and ``reference_answer`` was not recognised. The
audit silently substituted two demo questions about the EU AI Act.

So a client file now resolves to one of three states, and the third is new:

* absent → ``None``; ``eval_inputs`` uses its demo defaults, which is honest
  for a demo and for a client who supplied nothing;
* present and scoreable → the rows;
* **present but carrying no system answers** → the rows, with ``answers`` empty.
  ``run_golden_set`` reports that as unscored rather than inventing a 0 % pass
  rate, because "nobody has answered these 55 questions yet" and "the system
  failed all 55" are different findings.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier3.uagf_tam_l.rows import first_present, unwrap_rows

logger = logging.getLogger(__name__)

#: A row is usable when it has a question and a reference to check against.
#: The system's own answer is optional — a golden set exported before the system
#: has been run against it legitimately has none.
_REQUIRED = ("question", "expected")

#: Field aliases, most specific first. ``reference_answer`` is what case 06's
#: export calls the expected answer.
_QUESTION = ("question", "prompt", "input")
_EXPECTED = ("expected", "reference_answer", "expected_answer", "ground_truth",
             "reference", "gold_answer")
_ANSWER = ("answer", "system_answer", "actual", "output", "response")


def _to_rows(content: Any) -> list[dict[str, Any]]:
    """Normalise a loaded JSON file or CSV DataFrame into row dicts."""
    return unwrap_rows(content)


def _row_tuple(row: dict[str, Any]) -> tuple[str, list[str], str, str] | None:
    """Extract one ``(question, context, answer, expected)`` row, or ``None``."""
    question = first_present(row, _QUESTION)
    expected = first_present(row, _EXPECTED)
    if not question or not expected:
        return None
    context = row.get("context") or row.get("contexts") or []
    context = [context] if isinstance(context, str) else [str(c) for c in context]
    # Empty, not missing: the row is real and the answer is simply not supplied.
    return question, context, first_present(row, _ANSWER), expected


def resolve_golden_set(stage_b: dict[str, Any], store: Any,
                       ) -> tuple[list, list, list, list] | None:
    """Load and validate the golden set referenced by ``golden_set_uri``.

    :param stage_b: The Annex IV dossier (may lack ``golden_set_uri``).
    :type stage_b: dict[str, Any]
    :param store: Evidence store used to resolve ``minio://`` URIs.
    :type store: Any
    :returns: ``(questions, contexts, answers, expected)`` aligned lists, or
        ``None`` when absent/unparseable/empty (caller falls back to demo
        defaults).
    :rtype: tuple[list, list, list, list] | None
    """
    uri = stage_b.get("golden_set_uri")
    if not uri:
        return None
    try:
        from aaa.platform.artifact_loader import load_artifact_from_uri
        content = load_artifact_from_uri(uri, store)
    except Exception as exc:  # noqa: BLE001 — best-effort; caller falls back to demo defaults
        logger.warning("golden_set_uri %s could not be loaded: %s", uri, exc)
        return None
    parsed = [t for t in (_row_tuple(r) for r in _to_rows(content)) if t is not None]
    if not parsed:
        logger.warning("golden_set_uri %s produced no usable Q&A rows; ignoring.", uri)
        return None
    questions, contexts, answers, expected = zip(*parsed)
    return list(questions), list(contexts), list(answers), list(expected)
