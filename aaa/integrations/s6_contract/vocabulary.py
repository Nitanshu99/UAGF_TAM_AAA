"""The value sets S6 accepts, as distinct from the ones AAA emits.

Transcribed from ``s5_s4_json_fields_consumed_by_s6.xlsx`` ("Allowed values /
expected range"), and deliberately *not* derived from
:mod:`aaa.platform.state.model_meta`. The two vocabularies are different objects
with different owners: one describes what this system can represent, the other
what the partner will accept. Deriving either from the other is what let four
values reach the hand-off that S6's contract has no branch for.

The 2026-09-05 sweep found five such values in the delivered states, none of
them reported by S6 — because the field was *present*, so every presence check
passed and the mismatch surfaced only as a mis-load one system later:

===============  =========================  ==================================
case             value                      what a consumer does with it
===============  =========================  ==================================
04 legalmind     ``modality: agentic``      no branch — ``agentic`` is a system
                                            type, not a modality
05 talentsift    ``modality: nlp``          no branch — S6 spells this ``text``
04 legalmind     ``model_format:            outside the accepted set
                 safetensors``
02, 04           ``governance_verdict:      a fifth label; S6 has four
                 partially_compliant``
any              ``risk_tier: prohibited``  outside the accepted set
                 ``| gpai``
===============  =========================  ==================================

Values this module cannot translate are **warned about, not rewritten**. A
translation invents agreement that does not exist; a warning is the true
statement and is what a cross-team contract question actually needs.
"""
from __future__ import annotations

from typing import Any, Final

#: S6 ``modality`` — the data a system consumes. See :mod:`.translate` for why
#: AAA's own enum is not a subset of this.
MODALITIES: Final[frozenset[str]] = frozenset({
    "tabular", "time_series", "text", "image", "audio", "multimodal", "unknown"})

#: S6 ``system_type`` — which evaluation pathway to take.
SYSTEM_TYPES: Final[frozenset[str]] = frozenset({"traditional_ml", "llm", "agentic"})

#: S6 ``risk_tier``. AAA also emits ``prohibited`` and ``gpai`` (finding S12,
#: owned by S6): both are reachable and neither has a branch on their side.
RISK_TIERS: Final[frozenset[str]] = frozenset({"minimal", "limited", "high"})

#: S6 ``application_domain``, derived from the Annex III section (see
#: :func:`.translate.application_domain`).
APPLICATION_DOMAINS: Final[frozenset[str]] = frozenset({
    "biometrics", "critical_infrastructure", "education", "employment",
    "essential_services", "law_enforcement", "migration", "justice", "unknown"})

#: S6 ``task_type``. ``anomaly_detection`` was accepted here long before AAA
#: could express it — see the correction in :mod:`aaa.tools.model_meta.backfill`.
TASK_TYPES: Final[frozenset[str]] = frozenset({
    "binary_classification", "multiclass_classification", "regression",
    "forecasting", "llm_generation", "anomaly_detection"})

#: S6 ``model_format``. AAA additionally emits ``pytorch`` and ``safetensors``
#: (finding S9): real formats the sheet does not list, so they warn rather than
#: being silently coerced into ``huggingface``.
MODEL_FORMATS: Final[frozenset[str]] = frozenset({
    "joblib", "pickle", "onnx", "huggingface",
    "huggingface_pretrained", "huggingface_adapter"})

#: S6 ``model_framework``.
MODEL_FRAMEWORKS: Final[frozenset[str]] = frozenset({
    "sklearn", "sklearn_wrapper", "chronos_sklearn_wrapper", "onnxruntime",
    "transformers", "huggingface", "huggingface_transformers", "huggingface_peft"})

#: S6 ``model_artifact_kind``.
ARTIFACT_KINDS: Final[frozenset[str]] = frozenset({"single_file", "directory"})

#: S6 ``governance_verdict``. The sheet notes that lowercase spellings of these
#: four occur, so comparison is case-insensitive. It covers neither
#: ``partially_compliant`` (cases 02 and 04, finding S13) nor ``non_compliant``,
#: which the CGSA vocabulary and T14 both use and every case-06 run hands over.
#: Both are warned about, not mapped: which S6 label they mean is S6's call.
GOVERNANCE_VERDICTS: Final[frozenset[str]] = frozenset({
    "compliant", "compliant_with_observations", "conditional_pass", "fail"})


def unsupported(field: str, value: Any, accepted: frozenset[str]) -> str | None:
    """Describe *value* when S6's contract has no branch for it.

    :param field: The S6 field name, used in the message.
    :param value: The value AAA would hand over; ``None``/empty is not a
        vocabulary problem and is left to the presence checks.
    :param accepted: The value set S6 declares for *field*.
    :returns: A warning naming the value and the accepted set, or ``None``.
    """
    if value in (None, "", []):
        return None
    if str(value).strip().lower() in accepted:
        return None
    return (f"{field}={value!r} is outside the S6 accepted set "
            f"{{{', '.join(sorted(accepted))}}} — S6 has no branch for it")


__all__ = ["MODALITIES", "SYSTEM_TYPES", "RISK_TIERS", "APPLICATION_DOMAINS",
           "TASK_TYPES", "MODEL_FORMATS", "MODEL_FRAMEWORKS", "ARTIFACT_KINDS",
           "GOVERNANCE_VERDICTS", "unsupported"]
