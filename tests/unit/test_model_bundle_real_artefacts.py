"""Every shipped case artefact must unwrap to something Phase 3 can score.

``test_model_bundle_unwrap`` covers the unwrapping logic with synthetic stubs.
This pins the other half: the *actual shapes* the five case studies ship. Three
of them (01/02/03) save a bundle dict rather than a bare estimator, so a
regression in either the unwrapper or a re-saved fixture would silently turn
those audits into P3-MODEL-INVALID findings — declared accuracy, robustness and
fairness all unverifiable — without any test failing.
"""
from __future__ import annotations

import glob

import joblib
import pytest

from aaa.tools.eval_inputs.model_utils import _unwrap_model_bundle

_ARTEFACTS = sorted(glob.glob("mock/*/model/*.joblib") + glob.glob("mock/*/model/*.pkl"))


@pytest.mark.skipif(not _ARTEFACTS, reason="mock case artefacts not present")
@pytest.mark.parametrize("path", _ARTEFACTS)
def test_shipped_artefact_unwraps_to_a_scoreable_estimator(path):
    """The artefact yields an estimator exposing a callable .predict."""
    estimator, _, _ = _unwrap_model_bundle(joblib.load(path))

    assert estimator is not None, f"{path} did not yield an estimator"
    assert callable(getattr(estimator, "predict", None)), (
        f"{path} unwrapped to {type(estimator).__name__}, which cannot be scored"
    )


@pytest.mark.skipif(not _ARTEFACTS, reason="mock case artefacts not present")
def test_bundle_artefacts_expose_their_feature_columns():
    """Bundled artefacts must carry feature_cols, or scoring builds a wrong matrix."""
    for path in _ARTEFACTS:
        raw = joblib.load(path)
        if not isinstance(raw, dict):
            continue
        _, _, feature_cols = _unwrap_model_bundle(raw)
        assert feature_cols, f"{path} is a bundle but declares no feature_cols"
