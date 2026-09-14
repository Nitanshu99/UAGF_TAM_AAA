"""Model-bundle unwrap + matrix-build (fixes P3-MODEL-INVALID on saved bundles)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from aaa.tools.eval_inputs import _build_model_matrix, _predict, _unwrap_model_bundle


class _Estimator:
    """Minimal estimator with a .predict (stands in for a fitted sklearn model)."""

    def predict(self, X):
        return [0] * len(X)


class _LabelEncoder:
    def __init__(self, classes):
        self.classes_ = np.array(classes)


def test_bare_estimator_passes_through():
    est = _Estimator()
    model, enc, fcols = _unwrap_model_bundle(est)
    assert model is est and enc is None and fcols is None


def test_bundle_with_model_key_is_unwrapped():
    est = _Estimator()
    bundle = {"model": est, "encoders": {"c": _LabelEncoder(["a", "b"])}, "feature_cols": ["c", "n"]}
    model, enc, fcols = _unwrap_model_bundle(bundle)
    assert model is est and fcols == ["c", "n"] and "c" in enc


def test_bundle_finds_estimator_under_any_key():
    est = _Estimator()
    model, _, _ = _unwrap_model_bundle({"pipeline": est, "meta": 1})
    assert model is est


def test_dict_without_estimator_returns_none():
    model, _, _ = _unwrap_model_bundle({"version": "1.0", "algorithm": "xgb"})
    assert model is None


def test_build_matrix_label_encodes_and_orders_columns():
    df = pd.DataFrame({"n": [1, 2], "c": ["a", "b"], "extra": [9, 9]})
    enc = {"c": _LabelEncoder(["a", "b"])}
    X = _build_model_matrix(df, ["c", "n"], enc)
    assert list(X.columns) == ["c", "n"]          # feature_cols order, 'extra' dropped
    assert list(X["c"]) == [0, 1]                  # label-encoded


def test_build_matrix_unseen_label_maps_to_minus_one():
    df = pd.DataFrame({"c": ["a", "zzz"]})
    X = _build_model_matrix(df, ["c"], {"c": _LabelEncoder(["a", "b"])})
    assert list(X["c"]) == [0, -1]                 # 'zzz' unseen → -1, no crash


def test_predict_path_end_to_end():
    df = pd.DataFrame({"n": [1, 2, 3], "c": ["a", "b", "a"]})
    bundle = {"model": _Estimator(), "encoders": {"c": _LabelEncoder(["a", "b"])}, "feature_cols": ["c", "n"]}
    model, enc, fcols = _unwrap_model_bundle(bundle)
    X = _build_model_matrix(df, fcols, enc)
    y_pred, _ = _predict(model, X)
    assert y_pred == [0, 0, 0]
