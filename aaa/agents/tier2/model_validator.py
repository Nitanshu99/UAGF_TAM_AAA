"""
ModelValidator — Tier-2 Phase 3 Model Validation Agent (§3.2 #6).

Receives a ``Dispatch`` from the Orchestrator containing intake artefact URIs
and performs the following workflow:

  1. Load T01a / T01b from the Evidence Store; load optional model + dataset.
  2. Call ``metric_suite`` → performance metrics dict.
  3. Route to ``shap_explain`` (tabular / nlp) / ``gradcam_explain`` (cv) and
     ``lime_explain`` (tabular / nlp) for explainability evidence.
  4. Call ``robustness_probe`` for adversarial / perturbation results.
  5. Derive quality + robustness verdicts.
  6. Build T09 model card, T10 explainability report, T11 robustness report.
  7. Write T09 / T10 / T11 to the Evidence Store.
  8. Emit ``Report`` with ``declaration_verification_delta`` recording the
     three new artefact URIs and any HITL trigger (e.g. robustness FAIL).

This agent is SKIPPED for ``llm`` / ``agentic`` / ``gpai`` modalities — the
CSP routes those to UAGF-TAM-L in Group 10.

LLM path:
  - Production: Claude Opus via LiteLLM (``AAA_OFFLINE_MODE=false``).
  - Offline: deterministic rule-based path only.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.platform.evidence import EvidenceStore
from aaa.tools.client_doc_ingest import client_doc_search
from aaa.tools.eval_inputs import load_scored_evaluation
from aaa.tools.findings import make_finding, make_positive_finding
from aaa.tools.gradcam_explain import gradcam_explain
from aaa.tools.lime_explain import lime_explain
from aaa.tools.metric_suite import metric_suite
from aaa.tools.robustness_probe import robustness_probe
from aaa.tools.shap_explain import shap_explain

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
_SKIPPED_MODALITIES = {"llm", "agentic", "gpai"}
_PROMPT_NAME = "phase3_model"


class ModelValidatorError(Exception):
    """Raised when a hard gate blocks Phase 3."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[ModelValidator] {reason}")


class ModelValidator(BaseAgent):
    """
    Phase 3 — Model Validation Agent.

    Verifies model performance, explainability, and adversarial robustness
    against EU AI Act Art. 13 / 15 requirements.  Emits T09, T10, T11.
    """

    def __init__(
        self,
        evidence_store: EvidenceStore,
        model: str | None = None,
        service_tier: str | None = None,
    ):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        super().__init__(
            name="ModelValidator",
            model=resolve_model("ModelValidator", model),
            service_tier=resolve_service_tier("ModelValidator", service_tier),
        )
        self.store = evidence_store

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """
        Run Phase 3 model validation and return a Report.

        Parameters
        ----------
        message : Dispatch
            Must include ``declaration_summary`` with at minimum
            ``engagement_id``, ``modality``.  May include ``trained_model``,
            ``X_eval``, ``y_eval``, ``y_proba``, ``feature_names``,
            ``image_batch``, ``target_layer`` — all optional offline.
        """
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]
        modality: str = (decl.get("modality") or "tabular").lower()
        task: str = (decl.get("task") or "classification").lower()

        # ── 1. Load intake bundle + the REAL model / eval artefacts ──────────
        t01a, t01b = self._load_intake(message.get("evidence_uris", []))
        stage_b: dict[str, Any] = decl.get("stage_b") or t01b or {}

        findings: list[dict[str, Any]] = []
        positives: list[dict[str, Any]] = []
        insufficient: set[str] = set()

        # Direct injection (unit tests) wins; otherwise load from the store.
        trained_model = decl.get("trained_model")
        X_eval = decl.get("X_eval")
        y_eval = decl.get("y_eval")
        y_proba = decl.get("y_proba")
        y_pred = decl.get("y_pred")
        feature_names = decl.get("feature_names")
        image_batch = decl.get("image_batch")
        image_ids = decl.get("image_ids")
        target_layer = decl.get("target_layer")

        model_uri = (
            t01b.get("model_artifact_uri")
            or stage_b.get("model_artifact_uri")
            or decl.get("model_artifact_uri")
        )
        eval_uri = (
            t01b.get("evaluation_dataset_uri")
            or stage_b.get("evaluation_dataset_uri")
            or t01b.get("training_dataset_uri")
            or stage_b.get("training_dataset_uri")
            or decl.get("evaluation_dataset_uri")
        )

        if modality != "cv" and trained_model is None and (model_uri or eval_uri):
            scored = load_scored_evaluation(self.store, stage_b, t01b, source_phase="P3")
            trained_model = scored.model
            X_eval = scored.X_eval
            y_eval = scored.y_true
            y_pred = scored.y_pred
            y_proba = scored.y_proba
            if scored.data_dict:
                feature_names = feature_names or scored.data_dict.feature_columns
            findings.extend(scored.findings)

        # Whether an independently-scored evaluation set is available for Art. 15.
        eval_scored = (
            y_eval is not None and y_pred is not None
            and len(y_eval) > 0 and len(y_pred) == len(y_eval)
        )
        if modality != "cv" and not eval_scored:
            insufficient.update({"Art.15", "Art.15§1"})

        # ── 2. Metric suite (independent re-computation) ─────────────────────
        metrics_result = metric_suite(
            y_true=y_eval, y_pred=y_pred, y_proba=y_proba, task=task,
        )

        # ── 2b. Declaration diff: declared vs independently-computed metrics ──
        if eval_scored:
            diff_findings, diff_positives = self._diff_declared_metrics(
                stage_b.get("accuracy_metrics") or {}, metrics_result,
            )
            findings.extend(diff_findings)
            positives.extend(diff_positives)

        # ── 3. Explainability (route by modality) ────────────────────────────
        techniques: list[str] = []
        global_expl: dict[str, Any] = {
            "technique": "none", "feature_importance": [],
            "sample_size": 0, "tool": None,
        }
        local_expl: list[dict[str, Any]] = []
        visual_expl: list[dict[str, Any]] = []

        if modality == "cv":
            visual_expl = gradcam_explain(
                model=trained_model, images=image_batch, image_ids=image_ids,
                target_layer=target_layer,
            )
            if visual_expl:
                techniques.append("gradcam")
        else:
            global_expl = shap_explain(
                model=trained_model, X=X_eval, feature_names=feature_names,
            )
            if global_expl.get("feature_importance"):
                techniques.append("shap" if global_expl.get("technique") == "shap"
                                  else "feature_importance")
            local_expl = lime_explain(
                model=trained_model, X=X_eval, feature_names=feature_names,
                class_names=decl.get("class_names"),
            )
            if local_expl:
                techniques.append("lime")

        if not techniques:
            techniques = ["none"]

        # ── 4. Robustness probe ──────────────────────────────────────────────
        robustness_result = robustness_probe(
            model=trained_model, X=X_eval, y_true=y_eval, modality=modality,
        )

        # ── 5. Build artefacts ───────────────────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()
        client_doc_hits: list[dict[str, Any]] = []
        if decl.get("client_doc_collection"):
            client_doc_hits = client_doc_search(
                engagement_id,
                "model architecture training evaluation performance explainability robustness",
                top_k=3,
            )
        llm_payload: dict[str, Any] = {}
        llm_fallback_mode = _OFFLINE
        if not _OFFLINE:
            try:
                llm_payload = await self.acompletion_json(
                    _PROMPT_NAME,
                    {
                        "task": message.get("task_brief")
                        or "Execute Phase 3 model validation per the Phase 3 Protocol.",
                        "evidence_uris": message.get("evidence_uris", []),
                        "declaration_summary": decl,
                        "client_doc_hits": client_doc_hits,
                        "rerun_context": None,
                        "tool_outputs": {
                            "metrics_result": metrics_result,
                            "techniques": techniques,
                            "global_explanation": global_expl,
                            "local_explanations": local_expl[:5],
                            "visual_explanations": visual_expl[:5],
                            "robustness_result": robustness_result,
                        },
                    },
                )
                llm_fallback_mode = False
            except Exception as exc:
                logger.warning("ModelValidator prompt runtime failed (%s); using deterministic fallback.", exc)
        prompt_note = self.prompt_note(_PROMPT_NAME, llm_fallback_mode)
        llm_summary = llm_payload.get("summary") or llm_payload.get("rationale_summary")
        t09 = self._build_t09(engagement_id, t01a, t01b, modality, metrics_result, now)
        t10 = self._build_t10(
            engagement_id, modality, techniques, global_expl, local_expl, visual_expl, now,
        )
        t11 = self._build_t11(engagement_id, modality, robustness_result, now)
        t09["art13_compliance_notes"] = f"{t09['art13_compliance_notes']} {prompt_note}".strip()
        t10["interpretation"] = f"{t10['interpretation']} {prompt_note}".strip()
        t11["robustness_narrative"] = f"{llm_summary or t11['robustness_narrative']} {prompt_note}".strip()

        # ── 6. Store artefacts ───────────────────────────────────────────────
        t09_uri = self.store.store_artefact(
            engagement_id, "phase_3", "T09_model_card", t09, self.name)
        t10_uri = self.store.store_artefact(
            engagement_id, "phase_3", "T10_explainability_report", t10, self.name)
        t11_uri = self.store.store_artefact(
            engagement_id, "phase_3", "T11_robustness_report", t11, self.name)

        # ── 7. Emit Report ───────────────────────────────────────────────────
        robustness_verdict = t11["overall_robustness_verdict"]
        if robustness_verdict == "FAIL":
            findings.append(make_finding(
                finding_id="P3-ROBUST",
                description=(
                    "Independent adversarial robustness probe FAILED "
                    f"(min adversarial accuracy {t11.get('min_adversarial_accuracy')})."
                ),
                materiality="material",
                articles=["Art.15"],
                source_phase="P3",
                recommendation="Harden the model against perturbation; re-probe before deployment.",
                evidence_uris=[t11_uri],
            ))

        material = any(f.get("materiality") == "material" for f in findings)
        hitl_required = material or bool(insufficient)
        confidence = 0.85 if not hitl_required else 0.6

        delta: dict[str, Any] = {
            "phase_artefacts": {
                "T09_model_card": {
                    "uri": t09_uri, "sha256": "", "template_id": "T09_model_card"},
                "T10_explainability_report": {
                    "uri": t10_uri, "sha256": "",
                    "template_id": "T10_explainability_report"},
                "T11_robustness_report": {
                    "uri": t11_uri, "sha256": "", "template_id": "T11_robustness_report"},
            },
        }
        if findings:
            delta["blocking_findings"] = findings
        if positives:
            delta["positive_findings"] = positives
        if insufficient:
            delta["insufficient_evidence_articles"] = sorted(insufficient)
        if hitl_required:
            reasons = []
            if robustness_verdict == "FAIL":
                reasons.append(
                    f"robustness verdict FAIL (min_adversarial_accuracy={t11.get('min_adversarial_accuracy')})"
                )
            if material:
                reasons.append("material model-validation finding(s) raised")
            if insufficient:
                reasons.append(
                    "model/eval artefacts could not be independently verified: "
                    + ", ".join(sorted(insufficient))
                )
            delta["hitl_required"] = True
            delta["hitl_reason"] = "Phase 3 — " + "; ".join(reasons) + "."

        primary_value = metrics_result.get("primary_metric_value")
        primary_str = (
            f"{metrics_result.get('primary_metric')}={primary_value:.3f}"
            if isinstance(primary_value, (int, float)) else
            f"{metrics_result.get('primary_metric')}=n/a"
        )
        return Report(
            phase_id="P3",
            artefact_uri=t09_uri,
            summary=(
                llm_summary
                or
                f"Phase 3 complete. {primary_str}, "
                f"explainability={','.join(techniques)}, "
                f"robustness={robustness_verdict}."
            ),
            confidence=confidence,
            tool_calls=[
                {"tool": "metric_suite",
                 "result": f"{metrics_result.get('metric_suite_tool')}: {primary_str}"},
                {"tool": "explainability",
                 "result": f"techniques={techniques}, "
                           f"global_features={len(global_expl.get('feature_importance', []))}, "
                           f"local_instances={len(local_expl)}, "
                           f"visual_maps={len(visual_expl)}"},
                {"tool": "robustness_probe",
                 "result": f"verdict={robustness_verdict}, "
                           f"probes={len(robustness_result.get('probes', []))}"},
                {"tool": "client_doc_search", "result": f"hits={len(client_doc_hits)}"},
                {"tool": "prompt_runtime", "result": prompt_note},
            ],
            declaration_verification_delta=delta,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_intake(self, evidence_uris: list[str]) -> tuple[dict, dict]:
        """Load T01a and T01b from the Evidence Store."""
        t01a: dict[str, Any] = {}
        t01b: dict[str, Any] = {}
        for uri in evidence_uris:
            content = self.store.get_artefact(uri)
            if content is None:
                continue
            if "declared_modality" in content or "provider_name" in content:
                t01a = content
            elif "general_description" in content or "model_type" in content:
                t01b = content
        return t01a, t01b

    # ── Declaration diff (Phase-3 specific) ─────────────────────────────────

    # Declared key → computed metrics-key + human label.
    _METRIC_MAP = {
        "accuracy": ("accuracy", "accuracy"),
        "auc_roc": ("roc_auc", "AUC-ROC"),
        "f1_score": ("f1_macro", "F1"),
    }

    def _diff_declared_metrics(
        self,
        declared: dict[str, Any],
        metrics_result: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Compare declared performance metrics vs independently-computed ones.

        A real auditor does not take the provider's numbers on faith. Gaps beyond
        tolerance become findings; corroborated metrics become positive findings.
        """
        findings: list[dict[str, Any]] = []
        positives: list[dict[str, Any]] = []
        computed = metrics_result.get("metrics", {}) or {}

        for decl_key, (comp_key, label) in self._METRIC_MAP.items():
            decl_val = declared.get(decl_key)
            comp_val = computed.get(comp_key)
            if not isinstance(decl_val, (int, float)) or not isinstance(comp_val, (int, float)):
                continue
            gap = abs(float(decl_val) - float(comp_val))
            if gap > 0.10:
                materiality = "material"
            elif gap > 0.05:
                materiality = "possibly_material"
            else:
                positives.append(make_positive_finding(
                    finding_id=f"P3-METRIC-{comp_key.upper()}",
                    description=(
                        f"Declared {label} {decl_val:.3f} corroborated by independent "
                        f"re-computation ({comp_val:.3f}; gap {gap:.3f})."
                    ),
                    articles=["Art.15"],
                    source_phase="P3",
                ))
                continue
            note = (
                f"Declared {label} {decl_val:.3f} is not supported by independent "
                f"re-computation on the evaluation set ({comp_val:.3f}; gap {gap:.3f})."
            )
            if decl_key == "auc_roc" and float(decl_val) >= 0.95 and gap > 0.10:
                note += (
                    " The declared near-perfect AUC combined with the large gap is a "
                    "data-leakage / overfitting red flag warranting investigation."
                )
            findings.append(make_finding(
                finding_id=f"P3-METRIC-{comp_key.upper()}",
                description=note,
                materiality=materiality,
                articles=["Art.15"],
                source_phase="P3",
                recommendation="Reconcile the declared metric with an audited evaluation protocol.",
                declared=float(decl_val),
                observed=float(comp_val),
            ))
        return findings, positives

    # ── Artefact builders ──────────────────────────────────────────────────

    def _build_t09(
        self,
        engagement_id: str,
        t01a: dict,
        t01b: dict,
        modality: str,
        metrics_result: dict,
        now: str,
    ) -> dict:
        """Build T09 Model Card from dossier + metric_suite output."""
        provider = t01a.get("provider_name", "Unknown")
        system_name = t01a.get("system_name", "Unknown")
        version = t01a.get("version", "0.0.0")
        model_type = t01b.get("model_type") or modality

        return {
            "engagement_id": engagement_id,
            "model_identity": {
                "model_name": system_name,
                "model_version": str(version),
                "model_type": model_type,
                "modality": modality,
                "provider": provider,
            },
            "architecture": {
                "description": t01b.get("design_process",
                    f"{model_type} model — architecture inherited from Annex IV §1–§2."),
                "framework": t01b.get("framework"),
                "parameter_count": t01b.get("parameter_count"),
                "input_shape": t01b.get("input_shape"),
                "output_shape": t01b.get("output_shape"),
            },
            "training_regime": {
                "training_data_description": t01b.get("training_data_description",
                    "Not provided — see Annex IV §2."),
                "optimiser": t01b.get("optimiser"),
                "loss_function": t01b.get("loss_function"),
                "epochs": t01b.get("epochs"),
                "batch_size": t01b.get("batch_size"),
                "hyperparameters": t01b.get("hyperparameters"),
                "compute_resources": t01b.get("compute_resources"),
            },
            "performance_metrics": {
                "primary_metric": metrics_result.get("primary_metric", "accuracy"),
                "primary_metric_value": metrics_result.get("primary_metric_value"),
                "metrics": metrics_result.get("metrics", {}),
                "calibration_error": metrics_result.get("calibration_error"),
                "evaluation_dataset_description": t01b.get(
                    "evaluation_dataset_description",
                    "Inherited from declared evaluation set; see Annex IV §4."),
                "evaluation_sample_size": metrics_result.get("evaluation_sample_size", 0),
                "metric_suite_tool": metrics_result.get("metric_suite_tool"),
            },
            "intended_use": {
                "primary_use_cases": [t01a.get("intended_purpose",
                    "Intended purpose inherited from system card.")],
                "out_of_scope_use_cases": [
                    "Any use outside the declared intended purpose.",
                    "Any use violating EU AI Act Art. 5 prohibitions.",
                ],
            },
            "known_limitations": self._derive_limitations(modality, metrics_result, t01b),
            "ethical_considerations": (
                "Subject to ongoing risk-management process per Art. 9."
            ),
            "art13_compliance_notes": (
                "Model card populated from Annex IV dossier + metric_suite. "
                "Phase 3 ModelValidator — Art. 13 §3, Art. 15."
            ),
            "generated_at": now,
        }

    def _derive_limitations(
        self,
        modality: str,
        metrics_result: dict,
        t01b: dict,
    ) -> list[str]:
        """Derive a baseline list of known limitations."""
        limits: list[str] = []
        primary_val = metrics_result.get("primary_metric_value")
        if primary_val is None:
            limits.append(
                "Performance metrics could not be computed in offline mode — "
                "rerun against a live evaluation set required."
            )
        elif isinstance(primary_val, (int, float)) and primary_val < 0.7:
            limits.append(
                f"{metrics_result.get('primary_metric')} below 0.70 — "
                "review training regime and evaluation coverage."
            )
        if modality == "cv":
            limits.append("Domain-shift sensitivity not characterised; see T11.")
        if not t01b.get("robustness_metrics"):
            limits.append("No provider-supplied robustness metrics; relying on Phase 3 probes.")
        return limits or ["No automated limitations detected."]

    def _build_t10(
        self,
        engagement_id: str,
        modality: str,
        techniques: list[str],
        global_expl: dict,
        local_expl: list[dict],
        visual_expl: list[dict],
        now: str,
    ) -> dict:
        """Build T10 Explainability Report."""
        skipped_reason: str | None = None
        if techniques == ["none"]:
            skipped_reason = (
                "No trained model accessible — explainability techniques "
                "could not be executed offline."
            )

        interpretation = self._build_interpretation(modality, techniques, global_expl, local_expl)

        return {
            "engagement_id": engagement_id,
            "modality": modality,
            "techniques_applied": techniques,
            "global_explanation": global_expl,
            "local_explanations": local_expl or None,
            "visual_explanations": visual_expl or None,
            "interpretation": interpretation,
            "skipped_reason": skipped_reason,
            "art13_compliance_notes": (
                "Explainability evidence collected per Art. 13 §1–§2. "
                f"Modality-appropriate techniques applied: {techniques}."
            ),
            "generated_at": now,
        }

    def _build_interpretation(
        self,
        modality: str,
        techniques: list[str],
        global_expl: dict,
        local_expl: list[dict],
    ) -> str:
        """Compose a short human-readable interpretation string."""
        if techniques == ["none"]:
            return (
                f"No explainability techniques could be executed for {modality} "
                "modality — model artefact unavailable in this engagement."
            )
        top_features = [f["feature"] for f in global_expl.get("feature_importance", [])[:5]]
        feature_str = ", ".join(top_features) if top_features else "n/a"
        return (
            f"{modality} explainability: techniques={techniques}. "
            f"Top global features: {feature_str}. "
            f"Local explanations generated for {len(local_expl)} representative instances. "
            "Reviewers should confirm feature attributions align with documented intended use."
        )

    def _build_t11(
        self,
        engagement_id: str,
        modality: str,
        robustness_result: dict,
        now: str,
    ) -> dict:
        """Build T11 Robustness Report."""
        narrative = self._build_robustness_narrative(modality, robustness_result)
        return {
            "engagement_id": engagement_id,
            "modality": modality,
            "clean_accuracy": robustness_result.get("clean_accuracy"),
            "evaluation_sample_size": robustness_result.get("evaluation_sample_size", 0),
            "probes": robustness_result.get("probes", []),
            "noise_robustness": None,
            "overall_robustness_verdict": robustness_result.get(
                "overall_robustness_verdict", "NOT_TESTED"),
            "min_adversarial_accuracy": robustness_result.get("min_adversarial_accuracy"),
            "robustness_narrative": narrative,
            "skipped_reason": robustness_result.get("skipped_reason"),
            "art15_compliance_notes": (
                "Robustness probes executed per Art. 15. "
                f"Verdict: {robustness_result.get('overall_robustness_verdict', 'NOT_TESTED')}."
            ),
            "generated_at": now,
        }

    def _build_robustness_narrative(self, modality: str, result: dict) -> str:
        """Compose a free-text narrative for T11."""
        verdict = result.get("overall_robustness_verdict", "NOT_TESTED")
        if verdict == "NOT_TESTED":
            return (
                f"Robustness probes were not executed for {modality} modality "
                f"({result.get('skipped_reason') or 'no model/data available'})."
            )
        clean = result.get("clean_accuracy")
        min_adv = result.get("min_adversarial_accuracy")
        return (
            f"{modality} robustness verdict: {verdict}. "
            f"Clean accuracy: {clean:.3f}. " if isinstance(clean, float) else
            f"{modality} robustness verdict: {verdict}. "
        ) + (
            f"Worst-case adversarial accuracy: {min_adv:.3f} across "
            f"{len(result.get('probes', []))} probes."
            if isinstance(min_adv, float) else
            f"Adversarial accuracy could not be measured across "
            f"{len(result.get('probes', []))} probes."
        )
