"""The known per-company model metadata, and the corrections applied to a declaration."""
from __future__ import annotations

from typing import Any

#: company-name fragment → (task_type, model_format, model_framework)
#:
#: Each entry names what the model *is*, cross-checked against its own
#: ``model_type`` string in ``mock/<case>/stage_b.json``.
COMPANY_META: dict[str, tuple[str, str, str]] = {
    # model_type: sklearn_gradient_boosting_classifier_v2.1
    "finclear": ("binary_classification", "joblib", "sklearn"),
    "acme_credit": ("binary_classification", "joblib", "sklearn"),
    # model_type: time_series_transformer_chronos_tiny_rf_wrapper — a Chronos
    # transformer wrapped in a random forest, not a plain sklearn estimator.
    "retailiq": ("forecasting", "joblib", "chronos_sklearn_wrapper"),
    # model_type: isolation_forest_anomaly_detection — unlabelled, so neither a
    # binary classifier nor a carrier of `positive_label`.
    "harbourlogistik": ("anomaly_detection", "pickle", "sklearn"),
    # model_type: llm_rag_agentic_mistral_7b_lora — a PEFT adapter over a base
    # model, which is what `model_access_mode: base_plus_adapter` already says.
    "legalmind": ("llm_generation", "huggingface_adapter", "huggingface_peft"),
    # model_type: tfidf_logistic_regression_sklearn_v1.2 (added F9; the map had
    # no entry, so case 05 was backfilled by nothing).
    "talentsift": ("binary_classification", "joblib", "sklearn"),
}
_DD_PROMOTE = ("target_column", "positive_label", "sensitive_feature_columns")
#: company-name fragment → columns a counterfactual must hold fixed (fix F7).
#:
#: Only declared where the source states it. The S6 field sheet gives FinClear's
#: set verbatim — ``"immutable_feature_columns": ["age", "credit_history"]`` —
#: and both columns exist in that case's evaluation set. Nothing is guessed for
#: the others: the field is optional, and an invented actionability constraint
#: would silently steer every counterfactual the auditor generates.
COMPANY_IMMUTABLE: dict[str, list[str]] = {
    "finclear": ["age", "credit_history"],
    "acme_credit": ["age", "credit_history"],
}
#: Declarations known to be wrong, as ``fragment → {field: (wrong, right)}``.
#:
#: Separate from :func:`patch_stage_b` on purpose. That function's contract is
#: *fill-only* — it never overwrites a value someone set — and these three cases
#: are not empty, they are **mis-declared**, each because
#: :mod:`aaa.platform.state.model_meta` could not express the truth until fix F9.
#: A correction is only applied when the current value is still the known-wrong
#: one, so a deliberate later edit is never clobbered and re-running is a no-op.
CORRECTIONS: dict[str, dict[str, tuple[str, str]]] = {
    # A Chronos transformer behind a random-forest wrapper, declared as if it
    # were a bare sklearn estimator. Loading it as one gets the wrong object.
    "retailiq": {"model_framework": ("sklearn", "chronos_sklearn_wrapper")},
    # An isolation forest declared as a binary classifier, because `TaskType`
    # had no `anomaly_detection` — which S6's sheet had accepted all along.
    "harbourlogistik": {"task_type": ("binary_classification", "anomaly_detection")},
    # A LoRA adapter over a base model. `model_access_mode: base_plus_adapter`
    # already said so; the format and framework did not agree with it.
    "legalmind": {"model_format": ("safetensors", "huggingface_adapter"),
                  "model_framework": ("transformers", "huggingface_peft")},
}
def correct_stage_b(stage_b: dict[str, Any], company_key: str) -> list[str]:
    """Replace declarations known to be wrong, and only those (fix F9).

    :param stage_b: Stage B dossier dict, mutated in place.
    :param company_key: Folder / company name matched against :data:`CORRECTIONS`.
    :returns: Human-readable descriptions of the corrections applied; empty when
        the payload already holds the right values.
    """
    fixes = next((v for k, v in CORRECTIONS.items() if k in company_key.lower()), None)
    applied: list[str] = []
    for field, (wrong, right) in (fixes or {}).items():
        if stage_b.get(field) == wrong:
            stage_b[field] = right
            applied.append(f"{field}: {wrong!r} -> {right!r}")
    return applied


__all__ = ["COMPANY_IMMUTABLE", "COMPANY_META", "CORRECTIONS", "_DD_PROMOTE", "correct_stage_b"]
