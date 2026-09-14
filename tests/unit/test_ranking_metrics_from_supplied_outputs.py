"""Declared ranking metrics are recomputed from the evaluation set's ranked rows (T-20260914-029)."""
from __future__ import annotations

import pandas as pd
import pytest

from aaa.agents.tier2.model_validator import ranking as ranking_module
from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.declared import unverified_declared_finding
from aaa.tools.ranking_metrics import ndcg_at, precision_at, ranking_metrics

_RANKING = {"query_column": "job", "rank_column": "rank"}


def _frame(queries: int = 30) -> pd.DataFrame:
    """Each query ranks five candidates; the top two are relevant, then one of the last three."""
    pairs = [(q, r) for q in range(queries) for r in range(1, 6)]
    return pd.DataFrame({"job": [q for q, _ in pairs], "rank": [r for _, r in pairs],
                         "advanced": [int(r <= 2 or r == 5) for _, r in pairs]})


def test_per_query_metrics() -> None:
    """P@k over the items the list holds; NDCG with the query's own ideal ordering."""
    assert precision_at([True, True, False], 2) == 1.0
    assert precision_at([True, False], 5) == 0.5
    assert ndcg_at([False, False], 5) is None
    assert ndcg_at([True, True, False], 3) == pytest.approx(1.0)


def test_ranking_metrics_carry_query_level_intervals() -> None:
    """Identical queries give a degenerate interval; the value is exact."""
    result = ranking_metrics(_frame(), _RANKING, "advanced", 1, ["precision_at_2", "precision_at_5"])
    assert (result["computed"], result["n_queries"], result["n_rows"]) == (True, 30, 150)
    assert result["metrics"] == {"precision_at_2": 1.0, "precision_at_5": pytest.approx(0.6)}
    assert result["intervals"]["precision_at_5"] == pytest.approx((0.6, 0.6))


def test_undeclared_columns_are_not_guessed() -> None:
    """A ranking column the evaluation set lacks leaves the metrics uncomputed, with the reason."""
    result = ranking_metrics(_frame(), {"query_column": "vacancy", "rank_column": "rank"},
                             "advanced", 1, ["precision_at_2"])
    assert result["computed"] is False and "vacancy" in result["reason"]


def test_phase_3_judges_declared_ranking_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """A figure inside the interval is corroborated, one above it overstated; baselines stay unverified."""
    frame = _frame().assign(advanced=lambda d: [
        int(r <= 2 or (r == 5 and q % 2 == 0)) for q, r in zip(d["job"], d["rank"])])
    monkeypatch.setattr(ranking_module, "_frame", lambda store, ctx: frame)
    stage_b = {"accuracy_metrics": {"precision_at_2": 1.0, "precision_at_5": 0.9,
                                    "lexical_baseline_precision_at_5": 0.25},
               "data_dictionary": {"target_column": "advanced", "positive_label": 1,
                                   "ranking": _RANKING}, "model_access_mode": "not_provided"}
    ctx = EvalContext(t01a={}, t01b={}, stage_b=stage_b, insufficient={"Art.15", "Art.15§1"})
    metrics_result: dict = {"metrics": {}, "primary_metric_value": None}
    ranking_module.measure_ranking(None, ctx, metrics_result)
    assert [p["finding_id"] for p in ctx.positives] == ["P3-METRIC-PRECISION_AT_2"]
    assert [(f["finding_id"], f["materiality"]) for f in ctx.findings] == [
        ("P3-METRIC-PRECISION_AT_5", "material")]
    assert metrics_result["primary_metric"] == "precision_at_2"
    assert ctx.insufficient == {"Art.15"}
    unverified = unverified_declared_finding(stage_b, metrics_result, "not_provided") or {}
    assert "lexical_baseline_precision_at_5" in unverified["description"]
    assert "precision_at_2 " not in unverified["description"]
