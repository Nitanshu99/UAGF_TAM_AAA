"""The model card's document evidence, gathered once per Phase 3 run."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.t09 import T09_QUESTIONS
from aaa.tools.document_evidence import gather_evidence, searchable


def t09_evidence(decl: dict[str, Any], engagement_id: str, ctx: EvalContext) -> dict[str, Any]:
    """Answer the T09 questions from the declared dossier and the uploaded documents.

    :param decl: Declaration summary (whether documents were ingested).
    :param engagement_id: Engagement identifier.
    :param ctx: Resolved inputs, carrying the Stage B declaration.
    """
    return dict(gather_evidence(searchable(decl, engagement_id), T09_QUESTIONS,
                                declared=ctx.stage_b or ctx.t01b))


__all__ = ["t09_evidence"]
