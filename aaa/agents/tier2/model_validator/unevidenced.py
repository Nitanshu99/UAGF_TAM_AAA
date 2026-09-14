"""Flagging a model-based technique the run has no artefact for, and the robustness finding."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext, Explainability
from aaa.tools.findings import make_finding

#: Techniques that interrogate the model itself — the only ones Phase 3 reports.
#: Model-free proxies (column variance, raw feature snapshots) describe the
#: *data* and are no longer produced at all (T-20260913-061).
_MODEL_BASED_TECHNIQUES = frozenset({"shap", "lime", "gradcam", "token_importance"})
def flag_unevidenced(ctx: EvalContext, modality: str, expl: Explainability,
                     robustness_result: dict[str, Any]) -> None:
    """Mark Art. 13 / Art. 15 unevidenced when their tools produced no evidence.

    A tool that fails soft still returns a well-formed result, so a phase can
    report ``confidence=0.85`` over three stubs and carry an article to PASS on
    nothing. The confidence gate cannot see this — the agent *was* confident,
    and it was the tools beneath it that returned proxies. This is the check
    that reads the tool output rather than the agent's opinion of it.

    :param ctx: Evaluation context; ``insufficient`` and ``findings`` are
        extended in place.
    :param modality: Normalised system modality.
    :param expl: Explainability evidence from step 3.
    :param robustness_result: Output of ``robustness_probe``.
    """
    if not _MODEL_BASED_TECHNIQUES.intersection(expl.techniques):
        ctx.insufficient.add("Art.13")
        detail = (" ".join(expl.degraded) if expl.degraded
                  else f"no explainability technique executed for {modality} modality")
        ctx.findings.append(make_finding(
            finding_id="P3-EXPLAIN-UNEVIDENCED",
            description=("No model-based explainability could be produced, so Art. 13 "
                         f"interpretability is unevidenced: {detail}"),
            materiality="possibly_material", articles=["Art.13"], source_phase="P3",
            recommendation="Ship the model with the preprocessing its explainers need, "
                           "or supply a technique appropriate to the modality."))
    if robustness_result.get("overall_robustness_verdict") == "NOT_TESTED":
        ctx.insufficient.add("Art.15")
        ctx.findings.append(make_finding(
            finding_id="P3-ROBUST-UNEVIDENCED",
            description=("The adversarial robustness probe measured nothing, so Art. 15 "
                         "robustness is unevidenced: "
                         f"{robustness_result.get('skipped_reason') or 'no probe executed'}"),
            materiality="possibly_material", articles=["Art.15"], source_phase="P3",
            recommendation="Supply a model and evaluation set the probe can score."))
def append_robustness_finding(ctx: EvalContext, t11: dict[str, Any],
                              t11_uri: str) -> None:
    """Record what the robustness probe established: material on FAIL, else an observation.

    FAIL means a declared robustness figure is overstated; PASS_WITH_OBSERVATIONS
    means a probe established an accuracy drop (T-20260914-007). The narrative carries
    the measured intervals.

    :param ctx: Evaluation context whose findings list is extended in place.
    :param t11: T11 robustness-report content.
    :param t11_uri: Stored T11 artefact URI.
    """
    verdict = t11["overall_robustness_verdict"]
    if verdict not in ("FAIL", "PASS_WITH_OBSERVATIONS"):
        return
    failed = verdict == "FAIL"
    ctx.findings.append(make_finding(
        finding_id="P3-ROBUST" if failed else "P3-ROBUST-DEGRADATION",
        description=str(t11.get("robustness_narrative") or ""),
        materiality="material" if failed else "possibly_material",
        articles=["Art.15"], source_phase="P3",
        recommendation=("Restate the declared robustness with its test protocol, or harden "
                        "the model until it holds." if failed else
                        "Assess whether the measured degradation is acceptable for the intended "
                        "purpose, and state it in the instructions for use."),
        evidence_uris=[t11_uri]))


__all__ = ["_MODEL_BASED_TECHNIQUES", "append_robustness_finding", "flag_unevidenced"]
