"""aaa.tools.eval_inputs — Load + independently score a client's evaluation set.

Phase 3 (model validation) and Phase 4 (output fairness) both need the same
thing: the real model, the real evaluation set split into X / y, and the
model's predictions on it — plus the protected-attribute columns for
fairness.  Centralising that here keeps the "trust nothing, recompute
everything" contract in one place and avoids two agents drifting apart.

Loading/validity findings (missing dataset, stub model, schema mismatch) are
owned by Phase 3 (``emit_load_findings=True``); Phase 4 consumes the result
with ``emit_load_findings=False`` so a single root cause is not
double-reported.
"""
from __future__ import annotations

from aaa.tools.eval_inputs.core import load_scored_evaluation
from aaa.tools.eval_inputs.model_utils import (  # noqa: F401 (test access)
    _build_model_matrix,
    _unwrap_model_bundle,
)
from aaa.tools.eval_inputs.scoring import _infer_task_type, _predict  # noqa: F401 (test access)
from aaa.tools.eval_inputs.types import ScoredEvaluation

__all__ = ["ScoredEvaluation", "load_scored_evaluation"]
