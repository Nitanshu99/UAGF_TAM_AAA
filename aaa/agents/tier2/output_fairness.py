"""
OutputFairnessTester — Tier-2 Phase 4 Output Fairness Tester (§3.2 #7).

Receives a ``Dispatch`` from the Orchestrator containing intake artefact URIs
and performs the following workflow:

  1. Load T01a / T01b from the Evidence Store; pull predictions, labels,
     sensitive features, and (optional) text predictions from the dispatch.
  2. Call ``demographic_parity`` → group selection-rate parity.
  3. Call ``equal_opportunity``    → TPR gap across groups.
  4. Call ``disparate_impact``     → EEOC four-fifths-rule ratio.
  5. Call ``subgroup_metrics``     → per-group accuracy/SR/TPR/FPR.
  6. Call ``toxicity_classifier``  → 200-prediction sample toxicity scan.
  7. Derive overall fairness verdict.
  8. Build T12 fairness report, T13 sampling log.
  9. Write T12 / T13 to the Evidence Store.
  10. Emit ``Report`` whose ``declaration_verification_delta`` carries the
      two new artefact URIs and any HITL trigger (e.g. fairness FAIL or
      flagged discriminatory pattern).

This agent is SKIPPED on the L-branch — UAGF-TAM-L owns Arts. 10 §2(f) /
15 §1 evidence for generative systems (Group 10).

LLM path:
  - Production: Claude Sonnet via LiteLLM (``AAA_OFFLINE_MODE=false``).
  - Offline: deterministic rule-based path only.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.platform.evidence import EvidenceStore
from aaa.tools.demographic_parity import demographic_parity
from aaa.tools.disparate_impact import disparate_impact
from aaa.tools.equal_opportunity import equal_opportunity
from aaa.tools.subgroup_metrics import subgroup_metrics
from aaa.tools.toxicity_classifier import toxicity_classifier

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
_FAIRNESS_VERDICT_ORDER = ["NOT_TESTED", "PASS", "PASS_WITH_OBSERVATIONS", "FAIL"]
_TOXICITY_SAMPLE_CAP = 200


class OutputFairnessError(Exception):
    """Raised when a hard gate blocks Phase 4."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[OutputFairnessTester] {reason}")


class OutputFairnessTester(BaseAgent):
    """
    Phase 4 — Output Fairness Tester.

    Verifies model outputs for bias and discriminatory patterns against
    EU AI Act Art. 10 §2(f) / Art. 15 §1 requirements.  Emits T12, T13.
    """

    def __init__(
        self,
        evidence_store: EvidenceStore,
        model: str = "claude-sonnet-4-5",
    ):
        super().__init__(name="OutputFairnessTester", model=model)
        self.store = evidence_store

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """
        Run Phase 4 output fairness testing and return a Report.

        Parameters
        ----------
        message : Dispatch
            Must include ``declaration_summary`` with at minimum
            ``engagement_id``, ``modality``.  May include ``y_true``,
            ``y_pred``, ``sensitive_features``, ``sensitive_feature_names``,
            ``privileged_group``, ``positive_label``, ``prediction_texts``,
            ``prediction_ids`` — all optional offline.
        """
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]
        modality: str = (decl.get("modality") or "tabular").lower()

        # ── 1. Load intake bundle + payload ──────────────────────────────────
        t01a, t01b = self._load_intake(message.get("evidence_uris", []))
        y_true = decl.get("y_true")
        y_pred = decl.get("y_pred")
        sensitive_features = decl.get("sensitive_features")
        sensitive_feature_names = decl.get("sensitive_feature_names") or []
        privileged_group = decl.get("privileged_group")
        positive_label = decl.get("positive_label", 1)
        prediction_texts = decl.get("prediction_texts")
        prediction_ids = decl.get("prediction_ids")
        sampling_strategy = decl.get("sampling_strategy", "first_n")

        # ── 2–5. Fairness tools ──────────────────────────────────────────────
        dp_result = demographic_parity(
            y_pred=y_pred, sensitive_features=sensitive_features,
            positive_label=positive_label,
        )
        eo_result = equal_opportunity(
            y_true=y_true, y_pred=y_pred, sensitive_features=sensitive_features,
            positive_label=positive_label,
        )
        di_result = disparate_impact(
            y_pred=y_pred, sensitive_features=sensitive_features,
            privileged_group=privileged_group, positive_label=positive_label,
        )
        sg_result = subgroup_metrics(
            y_true=y_true, y_pred=y_pred, sensitive_features=sensitive_features,
            positive_label=positive_label,
        )

        # ── 6. Toxicity probe over up to 200-prediction sample ───────────────
        tox_input = prediction_texts if prediction_texts is not None else y_pred
        tox_result = toxicity_classifier(
            predictions=tox_input,
            prediction_ids=prediction_ids,
            sample_size=_TOXICITY_SAMPLE_CAP,
        )

        # ── 7. Derive overall verdict ────────────────────────────────────────
        overall_verdict = self._aggregate_verdict(
            [dp_result["verdict"], eo_result["verdict"],
             di_result["verdict"], sg_result["verdict"]]
        )
        sample_size = max(
            dp_result.get("sample_size", 0),
            eo_result.get("sample_size", 0),
            di_result.get("sample_size", 0),
            sg_result.get("sample_size", 0),
        ) or None
        skipped_reason = (
            "No predictions or sensitive features provided — fairness suite "
            "could not be executed offline."
            if overall_verdict == "NOT_TESTED" else None
        )

        # ── 8. Build artefacts ───────────────────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()
        t12 = self._build_t12(
            engagement_id, modality, sensitive_feature_names, sample_size,
            dp_result, eo_result, di_result, sg_result,
            overall_verdict, skipped_reason, now,
        )
        t13 = self._build_t13(
            engagement_id, modality, sampling_strategy,
            y_true, y_pred, sensitive_features, sensitive_feature_names,
            prediction_texts, prediction_ids, tox_result, now,
        )

        # ── 9. Store artefacts ───────────────────────────────────────────────
        t12_uri = self.store.store_artefact(
            engagement_id, "phase_4", "T12_output_fairness_report", t12, self.name)
        t13_uri = self.store.store_artefact(
            engagement_id, "phase_4", "T13_output_sampling_log", t13, self.name)

        # ── 10. Emit Report ──────────────────────────────────────────────────
        discriminatory_flag = t13["discriminatory_pattern_detected"]
        hitl_required = (overall_verdict == "FAIL") or discriminatory_flag
        confidence = 0.85 if not hitl_required else 0.6

        delta: dict[str, Any] = {
            "phase_artefacts": {
                "T12_output_fairness_report": {
                    "uri": t12_uri, "sha256": "",
                    "template_id": "T12_output_fairness_report"},
                "T13_output_sampling_log": {
                    "uri": t13_uri, "sha256": "",
                    "template_id": "T13_output_sampling_log"},
            },
        }
        if hitl_required:
            delta["hitl_required"] = True
            reasons = []
            if overall_verdict == "FAIL":
                reasons.append(f"Phase 4 fairness verdict is FAIL ({overall_verdict}).")
            if discriminatory_flag:
                reasons.append(
                    f"Discriminatory pattern flagged in output sample "
                    f"({t13['toxicity_results']['flagged_count']} entries)."
                )
            delta["hitl_reason"] = " ".join(reasons) or "Phase 4 escalation."

        return Report(
            phase_id="P4",
            artefact_uri=t12_uri,
            summary=(
                f"Phase 4 complete. fairness_verdict={overall_verdict}, "
                f"toxicity_flagged={tox_result.get('flagged_count', 0)} / "
                f"{tox_result.get('sample_size', 0)}."
            ),
            confidence=confidence,
            tool_calls=[
                {"tool": "demographic_parity",
                 "result": f"verdict={dp_result['verdict']}, "
                           f"difference={dp_result.get('difference')}"},
                {"tool": "equal_opportunity",
                 "result": f"verdict={eo_result['verdict']}, "
                           f"difference={eo_result.get('difference')}"},
                {"tool": "disparate_impact",
                 "result": f"verdict={di_result['verdict']}, "
                           f"ratio={di_result.get('ratio')}"},
                {"tool": "subgroup_metrics",
                 "result": f"verdict={sg_result['verdict']}, "
                           f"accuracy_gap={sg_result.get('accuracy_gap')}"},
                {"tool": "toxicity_classifier",
                 "result": f"verdict={tox_result['verdict']}, "
                           f"flagged={tox_result.get('flagged_count', 0)}"},
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

    def _aggregate_verdict(self, verdicts: list[str]) -> str:
        """Aggregate per-metric verdicts using the worst-band rule."""
        seen = [v for v in verdicts if v in _FAIRNESS_VERDICT_ORDER]
        if not seen or all(v == "NOT_TESTED" for v in seen):
            return "NOT_TESTED"
        ranked = [v for v in seen if v != "NOT_TESTED"]
        if not ranked:
            return "NOT_TESTED"
        worst_idx = max(_FAIRNESS_VERDICT_ORDER.index(v) for v in ranked)
        return _FAIRNESS_VERDICT_ORDER[worst_idx]

    # ── Artefact builders ──────────────────────────────────────────────────

    def _build_t12(
        self,
        engagement_id: str,
        modality: str,
        sensitive_feature_names: list[str],
        sample_size: int | None,
        dp: dict,
        eo: dict,
        di: dict,
        sg: dict,
        overall_verdict: str,
        skipped_reason: str | None,
        now: str,
    ) -> dict:
        """Build T12 Output Fairness Report."""
        narrative = self._build_fairness_narrative(modality, dp, eo, di, sg, overall_verdict)
        return {
            "engagement_id": engagement_id,
            "modality": modality,
            "sensitive_features": list(sensitive_feature_names),
            "evaluation_sample_size": sample_size,
            "demographic_parity": dp,
            "equal_opportunity": eo,
            "disparate_impact": di,
            "subgroup_metrics": sg,
            "overall_fairness_verdict": overall_verdict,
            "fairness_narrative": narrative,
            "skipped_reason": skipped_reason,
            "art10_2f_compliance_notes": (
                "Bias detection performed per Art. 10 §2(f): four metric families "
                "(demographic parity, equal opportunity, disparate impact, "
                "subgroup performance)."
            ),
            "art15_1_compliance_notes": (
                "Non-discrimination assessed per Art. 15 §1; "
                f"aggregate verdict: {overall_verdict}."
            ),
            "generated_at": now,
        }

    def _build_fairness_narrative(
        self,
        modality: str,
        dp: dict,
        eo: dict,
        di: dict,
        sg: dict,
        overall_verdict: str,
    ) -> str:
        """Compose a short human-readable narrative for T12."""
        if overall_verdict == "NOT_TESTED":
            return (
                f"Fairness suite could not be executed for {modality} modality — "
                "no predictions or sensitive features supplied."
            )
        return (
            f"{modality} fairness verdict: {overall_verdict}. "
            f"Demographic parity: {dp['verdict']} (diff={dp.get('difference')}). "
            f"Equal opportunity: {eo['verdict']} (diff={eo.get('difference')}). "
            f"Disparate impact: {di['verdict']} (ratio={di.get('ratio')}). "
            f"Subgroup performance: {sg['verdict']} (accuracy_gap={sg.get('accuracy_gap')})."
        )

    def _build_t13(
        self,
        engagement_id: str,
        modality: str,
        sampling_strategy: str,
        y_true: Any,
        y_pred: Any,
        sensitive_features: Any,
        sensitive_feature_names: list[str],
        prediction_texts: Any,
        prediction_ids: Any,
        tox_result: dict,
        now: str,
    ) -> dict:
        """Build T13 Output Sampling Log."""
        cap = _TOXICITY_SAMPLE_CAP
        preds = list(y_pred or [])[:cap]
        trues = list(y_true or [])
        feats = list(sensitive_features or [])
        texts = list(prediction_texts or [])
        ids = list(prediction_ids or list(range(len(preds))))[:len(preds)]
        if len(ids) < len(preds):
            ids.extend(range(len(ids), len(preds)))

        predictions_sample: list[dict[str, Any]] = []
        for i, pred in enumerate(preds):
            entry: dict[str, Any] = {
                "prediction_id": str(ids[i]),
                "predicted_value": self._coerce_jsonable(pred),
            }
            if i < len(trues):
                entry["true_value"] = self._coerce_jsonable(trues[i])
            if i < len(feats) and sensitive_feature_names:
                entry["sensitive_attributes"] = {
                    sensitive_feature_names[0]: self._coerce_jsonable(feats[i])
                }
            if i < len(texts):
                entry["input_excerpt"] = str(texts[i])[:200]
            predictions_sample.append(entry)

        flagged_entries = [e for e in tox_result.get("entries", []) if e.get("flagged")]
        examples = [
            {
                "prediction_id": e["prediction_id"],
                "category": (e.get("flagged_categories") or ["unknown"])[0],
                "excerpt": e.get("text_excerpt"),
            }
            for e in flagged_entries[:10]
        ]
        discriminatory = bool(flagged_entries)
        if tox_result.get("verdict") == "FAIL":
            overall = "FAIL"
        elif discriminatory:
            overall = "PASS_WITH_OBSERVATIONS"
        elif tox_result.get("verdict") == "NOT_TESTED":
            overall = "NOT_TESTED"
        else:
            overall = "PASS"

        return {
            "engagement_id": engagement_id,
            "modality": modality,
            "sampling_strategy": sampling_strategy,
            "sample_size": len(predictions_sample),
            "predictions_sample": predictions_sample,
            "toxicity_results": tox_result,
            "discriminatory_pattern_detected": discriminatory,
            "discriminatory_pattern_examples": examples,
            "overall_verdict": overall,
            "hitl_review_required": discriminatory,
            "hitl_review_reason": (
                f"{len(flagged_entries)} sampled predictions flagged for "
                "discriminatory patterns; HITL review required."
                if discriminatory else None
            ),
            "sampling_narrative": (
                f"Sampled {len(predictions_sample)} predictions via "
                f"'{sampling_strategy}' strategy; toxicity verdict: "
                f"{tox_result.get('verdict', 'NOT_TESTED')}."
            ),
            "art15_1_compliance_notes": (
                "Output sample inspected for discriminatory patterns per Art. 15 §1."
            ),
            "generated_at": now,
        }

    @staticmethod
    def _coerce_jsonable(value: Any) -> Any:
        """Coerce arbitrary values to JSON-safe scalars for T13 entries."""
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        try:
            return str(value)
        except Exception:
            return None
