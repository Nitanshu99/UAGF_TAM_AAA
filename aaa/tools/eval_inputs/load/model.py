"""Step 3 of the evaluation loader: model artefact resolution."""
from __future__ import annotations

from typing import Any

from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri
from aaa.tools.eval_inputs.load.missing import record_absent_model
from aaa.tools.eval_inputs.model_utils import _unwrap_model_bundle
from aaa.tools.eval_inputs.types import FindingSink
from aaa.tools.findings import make_finding


def _loader_kind(model_format: str | None) -> str:
    """Map a declared ``model_format`` to an artifact-loader kind.

    :param model_format: Declared format from the Stage B dossier, or ``None``.
    :type model_format: str | None
    :returns: ``"joblib"`` for joblib/pickle (joblib reads plain pickles) or
        when undeclared; ``"bytes"`` for formats not executable in-process
        (onnx/pytorch/huggingface/safetensors), which then surface the
        existing not-executable finding instead of a load error.
    :rtype: str
    """
    return "joblib" if model_format in (None, "", "joblib", "pickle") else "bytes"


def load_model(store: Any, model_uri: str | None, sink: FindingSink,
               source_phase: str, model_format: str | None = None,
               access_mode: str | None = None) -> tuple[Any, Any, Any, Any]:
    """Load and unwrap the model artefact, recording findings on failure.

    :param access_mode: Declared ``model_access_mode``; decides which finding
        describes an absent artefact, since under the reference modes absence
        is expected rather than a gap.
    :returns: ``(model, encoders, feature_cols, raw_loaded)`` — ``model`` is
        ``None`` when nothing scoreable could be resolved.
    """
    model, encoders, feature_cols, raw_loaded = None, None, None, None
    if model_uri:
        try:
            raw_loaded = load_artifact_from_uri(model_uri, store, _loader_kind(model_format))
        except ArtifactUnavailable as exc:
            sink.add(make_finding(
                finding_id="P3-MODEL-LOAD",
                description=f"Model artefact could not be loaded; accuracy/robustness/fairness "
                            f"claims could not be independently verified: {exc.reason}.",
                materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
                recommendation="Provide the trained model artefact (joblib/pickle).",
            ), load=True)
        else:
            # Unwrap a saved bundle ({'model': estimator, 'encoders', 'feature_cols'}).
            model, encoders, feature_cols = _unwrap_model_bundle(raw_loaded)
    else:
        record_absent_model(sink, source_phase, access_mode)

    if raw_loaded is not None and model is None:
        # Loaded, but neither a bare estimator nor a bundle carrying one.
        sink.add(make_finding(
            finding_id="P3-MODEL-INVALID",
            description=(
                f"Submitted model artefact is not an executable model "
                f"(loaded type={type(raw_loaded).__name__}, no .predict method or "
                "bundled estimator); the declared performance, robustness and fairness "
                "metrics are entirely unverifiable from this artefact."
            ),
            materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
            recommendation="Submit the fitted model (or a bundle with a 'model' estimator).",
            evidence_uris=[model_uri] if model_uri else None,
        ), load=True)
    return model, encoders, feature_cols, raw_loaded
