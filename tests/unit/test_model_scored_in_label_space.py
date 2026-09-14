"""The uploaded model must be scored in the labels its evaluation set uses.

Case 03 ships an IsolationForest: ``predict`` answers -1 (outlier) / +1 (inlier)
while ``anomaly_label`` is 1 / 0. Compared raw, no prediction ever equalled a
label, so accuracy read ~0 and robustness FAILED on a model that performs well.
Case 02 is a forecaster, yet metrics were always computed as classification.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression

from aaa.agents.tier2.model_validator.task import metrics_task
from aaa.tools.eval_inputs.label_space import label_space_predictor
from aaa.tools.robustness_probe import robustness_probe


def _anomalies() -> tuple[np.ndarray, list[int], IsolationForest]:
    """A 2-D cloud with a ring of far outliers, labelled 1 = anomaly."""
    rng = np.random.default_rng(7)
    inliers, outliers = rng.normal(0, 1, (190, 2)), rng.uniform(8, 10, (10, 2))
    x = np.vstack([inliers, outliers])
    labels = [0] * 190 + [1] * 10
    # sklearn's stubs type ``contamination`` as str; a float share is the documented form.
    detector = IsolationForest(contamination=0.05, random_state=0)  # pyright: ignore[reportArgumentType]
    return x, labels, detector.fit(x)


def _accuracy(pred: list[int], labels: list[int]) -> float:
    """Share of predictions equal to the label."""
    return sum(int(p == t) for p, t in zip(pred, labels)) / len(labels)


def test_outlier_detector_predictions_are_mapped_to_the_labels() -> None:
    """-1/+1 becomes positive/normal; raw comparison would score ~0."""
    x, labels, model = _anomalies()
    predict = label_space_predictor(model, "anomaly", labels, positive_label=1)
    assert predict is not None
    pred = predict(x)
    assert set(pred) <= {0, 1} and _accuracy(pred, labels) > 0.9
    assert _accuracy(list(model.predict(x)), labels) < 0.1


def test_a_zero_positive_label_flips_the_mapping() -> None:
    """When 0 marks the anomaly, outliers map to 0."""
    x, labels, model = _anomalies()
    predict = label_space_predictor(model, "anomaly", [1 - v for v in labels], positive_label=0)
    assert predict is not None and predict(x)[-1] == 0


def test_other_tasks_and_label_spaces_pass_through() -> None:
    """A classifier, a non-binary target and a missing model are left alone."""
    x, labels, model = _anomalies()
    clf = LogisticRegression().fit(x, labels)
    passthrough = label_space_predictor(clf, "classification", labels)
    assert passthrough is not None and passthrough(x) == list(clf.predict(x))
    raw = label_space_predictor(model, "anomaly", [0, 1, 2])
    assert raw is not None and set(raw(x)) <= {-1, 1}
    assert label_space_predictor(None, "anomaly", labels) is None


def test_robustness_scores_the_same_labels_as_the_metrics() -> None:
    """With the mapped predictor the clean accuracy is the model's real one."""
    x, labels, model = _anomalies()
    result = robustness_probe(model=model, X=x, y_true=labels, modality="tabular",
                              predict_fn=label_space_predictor(model, "anomaly", labels))
    assert result["clean_accuracy"] is not None and result["clean_accuracy"] > 0.9


def test_metrics_follow_the_task_not_a_hardcoded_classification() -> None:
    """Declared task wins; then the inferred task; then Stage B; classification last."""
    assert metrics_task("classification", {"task": "regression"}, {}) == "regression"
    assert metrics_task("regression", {}, {}) == "regression"
    assert metrics_task("anomaly", {}, {"task_type": "regression"}) == "classification"
    assert metrics_task("unknown", {}, {"task_type": "time_series_forecasting"}) == "regression"
    assert metrics_task("unknown", {}, {}) == "classification"
