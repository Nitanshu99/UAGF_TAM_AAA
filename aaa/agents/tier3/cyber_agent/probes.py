"""Specialist probe execution and verdict rules for the Cyber sub-agent."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.cyber_agent.injection import _injection, injection_finding
from aaa.tools.robustness_probe import robustness_probe


def _probe_matrix(scored: Any) -> Any:
    """Return the matrix the model can actually be scored on.

    ``X_model`` when the loader built one (fix 15), else the raw frame — the
    same precedence :attr:`EvalContext.x_probe` applies in Phase 3.
    """
    x_model = getattr(scored, "X_model", None)
    return getattr(scored, "X_eval", None) if x_model is None else x_model


def run_specialist_probes(decl: dict[str, Any], modality: str, engagement_id: str,
                          probes: list[dict], scored: Any = None,
                          ) -> tuple[dict | None, list[dict], str, str | None]:
    """Run the deeper adversarial + injection probes.

    :param decl: Declaration summary carrying model/eval handles.
    :param modality: Verified modality (injection only for generative kinds).
    :param engagement_id: Engagement identifier (finding ids).
    :param probes: Existing probe list — extended in place.
    :param scored: Loaded :class:`ScoredEvaluation`, when the spawn resolved the
        model and evaluation set from Stage B. Direct injection through *decl*
        still wins, which is what a unit test supplies.
    :returns: ``(injection_results_or_None, blocking_findings, skipped_reason,
        robustness_verdict)`` — *skipped_reason* is empty when the adversarial probe
        measured something (P5); the verdict is the probe's own (T-20260914-007).
    """
    blocking_findings: list[dict] = []
    # Specialist probe 1 re-ran Phase 3's seeded perturbation probe on the same rows
    # and appended identical "CyberAgent_" copies as deeper evidence (case 01,
    # 2026-09-14). No gradient- or query-based attack tooling exists here, so when
    # Phase 3 already probed the model its probes stand and none is repeated.
    if probes:
        skipped = (f"Phase 3 already probed this {modality} model with the seeded perturbation "
                   "probe; no deeper gradient- or query-based attack tooling is available, so "
                   "the probe was not repeated and Phase 3's results stand.")
        return _injection(decl, modality, engagement_id, blocking_findings), \
            blocking_findings, skipped, None
    # No dispatch has ever carried `trained_model` / `X_eval` / `y_eval`; `scored` is
    # the Stage B fallback Phase 3 has always used.
    rob_results = robustness_probe(
        model=decl.get("trained_model") or getattr(scored, "model", None),
        X=(decl.get("X_eval") if decl.get("X_eval") is not None
           else _probe_matrix(scored)),
        y_true=decl.get("y_eval") or getattr(scored, "y_true", None),
        modality=modality,
        # Label-space predictions (outlier detectors mapped) whenever the spawn loaded the model.
        predict_fn=None if decl.get("trained_model") else getattr(scored, "predict_fn", None),
        categorical_features=getattr(scored, "categorical_features", None),
        declared=(decl.get("stage_b") or {}).get("robustness_metrics"),
    )
    probes.extend(rob_results.get("probes", []))
    skipped_reason = "" if rob_results.get("probes") else str(
        rob_results.get("skipped_reason")
        or "the adversarial probe measured nothing on the supplied inputs")
    injection = _injection(decl, modality, engagement_id, blocking_findings)
    return injection, blocking_findings, skipped_reason, rob_results.get("overall_robustness_verdict")


__all__ = ["_injection", "injection_finding", "run_specialist_probes"]
