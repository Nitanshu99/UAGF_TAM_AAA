"""Unit tests for :mod:`aaa.tools.model_meta` filename/modality inference."""
from __future__ import annotations

from aaa.platform.state.model_vocab import MODEL_FORMATS, SUPERVISED_TASK_TYPES, TASK_TYPES
from aaa.tools.model_meta import infer_model_format, suggest_task_type


def test_joblib_extension() -> None:
    """A ``.joblib`` artefact maps to joblib/sklearn."""
    assert infer_model_format("creditguard_v2.1.joblib") == ("joblib", "sklearn")


def test_pickle_extensions() -> None:
    """``.pkl`` and ``.pickle`` both map to pickle/sklearn."""
    assert infer_model_format("harboursense_v1.4.pkl") == ("pickle", "sklearn")
    assert infer_model_format("m.pickle") == ("pickle", "sklearn")


def test_onnx_pytorch_safetensors() -> None:
    """ONNX, PyTorch, and safetensors extensions map to their formats."""
    assert infer_model_format("net.onnx") == ("onnx", "onnxruntime")
    assert infer_model_format("weights.pt") == ("pytorch", None)
    assert infer_model_format("weights.pth") == ("pytorch", None)
    assert infer_model_format("model.safetensors") == ("safetensors", "transformers")


def test_huggingface_directory_and_zip() -> None:
    """Extension-less names and ``.zip`` bundles map to huggingface/transformers."""
    assert infer_model_format("lexai_v2_stub") == ("huggingface", "transformers")
    assert infer_model_format("lexai_v2_stub.zip") == ("huggingface", "transformers")


def test_uri_paths_use_basename() -> None:
    """MinIO-style URIs infer from the final path component."""
    uri = "minio://eng-01/customer_uploads/model_artifact_uri_0ac0_creditguard.joblib"
    assert infer_model_format(uri) == ("joblib", "sklearn")


def test_unknown_and_empty_inputs() -> None:
    """Unknown extensions and empty/None inputs yield ``(None, None)``."""
    assert infer_model_format("model.xyz") == (None, None)
    assert infer_model_format("") == (None, None)
    assert infer_model_format(None) == (None, None)


def test_suggest_task_type_by_modality() -> None:
    """Each declared modality maps to a valid default task type."""
    assert suggest_task_type("tabular") == "binary_classification"
    assert suggest_task_type("time_series") == "forecasting"
    assert suggest_task_type("llm") == "llm_generation"
    assert suggest_task_type("agentic") == "llm_generation"
    assert suggest_task_type("unknown_modality") is None
    assert suggest_task_type(None) is None


def test_vocabularies_consistent() -> None:
    """Supervised task types are a subset of the full vocabulary."""
    assert set(SUPERVISED_TASK_TYPES) <= set(TASK_TYPES)
    assert "joblib" in MODEL_FORMATS


def test_loader_kind_mapping() -> None:
    """joblib/pickle/undeclared map to joblib; non-executable formats to bytes."""
    from aaa.tools.eval_inputs.load.model import _loader_kind
    assert _loader_kind(None) == "joblib"
    assert _loader_kind("joblib") == "joblib"
    assert _loader_kind("pickle") == "joblib"
    assert _loader_kind("onnx") == "bytes"
    assert _loader_kind("huggingface") == "bytes"
