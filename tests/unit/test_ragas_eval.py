"""ragas_eval must measure or abstain — never invent, never crash the verdict."""
from __future__ import annotations

import pytest

from aaa.agents.tier3.uagf_tam_l.ragas_run import derive_verdict
from aaa.tools.ragas_eval import ragas_eval
from aaa.tools.ragas_eval.compute import metrics as metrics_mod
from aaa.tools.ragas_eval.compute import ragas as ragas_mod

T16_FIELDS = ("faithfulness", "answer_relevance", "context_precision",
              "context_recall", "answer_similarity", "answer_correctness")

CLEAN_INJECTION = {"vulnerability_rate": 0.0, "total_probes": 50, "successful_attacks": 0}


def test_ragas_library_imports():
    """ragas must import: langchain-community 0.4 removed a module it needs."""
    ragas = pytest.importorskip("ragas")
    assert ragas.evaluate is not None


def test_metric_set_grows_with_references():
    """Reference-scored metrics are only requested when references exist."""
    bare, bare_keys = metrics_mod.build_metrics(with_reference=False)
    full, full_keys = metrics_mod.build_metrics(with_reference=True)

    assert len(bare) == 3
    assert len(full) == 6
    assert set(bare_keys) == {"faithfulness", "answer_relevance", "context_precision"}
    assert set(full_keys) == set(T16_FIELDS)
    assert bare_keys["context_precision"].endswith("without_reference")
    assert full_keys["context_precision"].endswith("with_reference")


def test_empty_inputs_report_not_computed():
    result = ragas_eval([], [], [])
    assert result["computed"] is False
    assert all(result[field] is None for field in T16_FIELDS)


def test_compute_maps_ragas_names_to_t16_fields(monkeypatch):
    """The 0.4 result keys are translated back to the T16 field names."""
    scored = {
        "faithfulness": 0.9,
        "answer_relevancy": 0.8,
        "llm_context_precision_with_reference": 0.7,
        "context_recall": 0.6,
        "answer_similarity": 0.5,
        "answer_correctness": 0.4,
    }
    monkeypatch.setattr(ragas_mod, "_samples", lambda *a, **k: [])
    monkeypatch.setattr(ragas_mod, "build_judge", lambda: (None, None))
    monkeypatch.setattr(
        ragas_mod, "build_metrics",
        lambda with_reference: ([], metrics_mod.build_metrics(with_reference)[1]))
    monkeypatch.setattr(
        "ragas.evaluate", lambda dataset, **kwargs: scored, raising=False)
    monkeypatch.setattr("ragas.EvaluationDataset", lambda samples: samples, raising=False)

    out = ragas_mod._compute_ragas(["q"], [["c"]], ["a"], ["ref"])

    assert out["computed"] is True
    assert out["answer_relevance"] == 0.8      # from answer_relevancy
    assert out["context_precision"] == 0.7     # from llm_context_precision_with_reference
    assert out["answer_correctness"] == 0.4


@pytest.mark.parametrize("raw,expected", [
    ([0.8, 0.6], 0.7),                       # per-row scores are averaged
    ([0.5], 0.5),
    (0.4, 0.4),                              # a bare scalar still works
    ([0.9, float("nan")], 0.9),              # unscored rows are dropped
    ([float("nan")], None),                  # all-NaN is not a zero
    ([], None),
    (None, None),
])
def test_score_aggregates_rows_nan_safely(raw, expected):
    """``result[key]`` is per-row in ragas 0.4; the mean must skip NaN rows."""
    got = ragas_mod._score({"m": raw}, "m")
    assert got == pytest.approx(expected) if expected is not None else got is None


def test_score_missing_key_is_none():
    assert ragas_mod._score({}, "absent") is None


def test_failure_reports_not_computed_never_fabricates(monkeypatch):
    monkeypatch.setattr(
        ragas_mod, "build_metrics",
        lambda with_reference: (_ for _ in ()).throw(RuntimeError("no api key")))

    result = ragas_eval(["q"], [["c"]], ["a"], ["ref"])

    assert result["computed"] is False
    assert "RuntimeError" in result["reason"]
    assert all(result[field] is None for field in T16_FIELDS)


def test_verdict_survives_uncomputed_ragas():
    """A missing faithfulness must not raise, and must not read as a pass."""
    uncomputed = {"computed": False, "faithfulness": None}

    verdict = derive_verdict({"pass_rate": 0.95}, uncomputed, CLEAN_INJECTION)

    assert verdict == "PASS_WITH_OBSERVATIONS"


@pytest.mark.parametrize("faithfulness,failed,expected", [
    (0.95, 0, "PASS"),
    (0.95, 3, "PASS_WITH_OBSERVATIONS"),
    (0.50, 0, "FAIL"),
])
def test_verdict_follows_declared_targets(faithfulness, failed, expected):
    """Below the declared faithfulness target fails; wrong golden answers are observations."""
    verdict = derive_verdict({"pass_rate": 0.9, "failed_samples": failed, "total_samples": 30},
                             {"computed": True, "faithfulness": faithfulness},
                             CLEAN_INJECTION, {"ragas_faithfulness_target": 0.9})
    assert verdict == expected
