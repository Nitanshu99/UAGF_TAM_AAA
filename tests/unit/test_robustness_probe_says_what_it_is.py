"""The robustness probe states what it measured, on every row (T-20260914-036, case 01)."""
from __future__ import annotations

import numpy as np

from aaa.agents.tier2.model_validator.t11 import build_t11
from aaa.tools.robustness_probe import robustness_probe
from aaa.tools.template_render.logger import _load_schema, _validate_payload


class _Threshold:
    """A model that predicts 1 where the first feature is positive."""

    def predict(self, X):  # noqa: N803 - scikit-learn's argument name
        """Label by the sign of the first column."""
        return (np.asarray(X)[:, 0] > 0).astype(int)


def _result(n: int = 300, declared: dict | None = None) -> dict:
    rng = np.random.default_rng(7)
    X = rng.normal(size=(n, 3))
    return robustness_probe(model=_Threshold(), X=X, y_true=list((X[:, 0] > 0).astype(int)),
                            modality="tabular", declared=declared)


def test_every_evaluation_row_is_probed() -> None:
    """No 200-row cap: case 01's 300 rows are all used."""
    assert _result(300)["evaluation_sample_size"] == 300


def test_random_noise_is_not_labelled_an_attack() -> None:
    """No ``l_inf`` norm and no "fallback" tool name on the designed probe."""
    for probe in _result()["probes"]:
        assert probe["norm"] is None
        assert "fallback" not in probe["tool"]


def test_a_declared_attack_no_probe_runs_is_named_as_not_judged() -> None:
    """Case 01's adversarial_accuracy_l_inf_0_01 is stated as not judged, with why."""
    notes = " ".join(_result(declared={"adversarial_accuracy_l_inf_0_01": 0.74})["degradation_notes"])
    assert "under l_inf at 0.01 (0.740) is not judged" in notes


def test_t11_carries_the_threat_model_and_validates() -> None:
    """The Art. 15 note says the probes are not gradient- or query-based attacks."""
    t11 = build_t11("eng-01", "tabular", _result(), "2026-09-14T00:00:00Z")
    assert "not gradient- or query-based adversarial attacks" in t11["art15_compliance_notes"]
    assert not _validate_payload(t11, _load_schema("T11_robustness_report"), "T11_robustness_report")
