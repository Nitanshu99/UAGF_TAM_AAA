"""T-20260913-099: T09's known limitations are measurements, never a claim of none.

Case 05's model card said "No automated limitations detected." beside an 80-row
evaluation; a fixed 0.70 flagged any primary metric whatever the provider targeted.
"""
from __future__ import annotations

from aaa.agents.tier2.model_validator.t09.limits import derive_limitations

_DOSSIER = {"robustness_metrics": {"char_noise": 0.9}}


def test_the_evaluation_size_bounds_what_the_metrics_establish() -> None:
    """80 rows: a rate is known to within about ±11% at worst."""
    limits = derive_limitations("nlp", {"primary_metric_value": 0.8, "metrics": {},
                                        "evaluation_sample_size": 80}, _DOSSIER)
    assert limits == [next(x for x in limits if "80 evaluation rows" in x)]
    assert "±11.0%" in limits[0]


def test_a_missed_declared_target_is_the_limitation_not_a_fixed_threshold() -> None:
    """A 0.65 F1 with no target is not flagged; a missed FNR target is."""
    metrics = {"primary_metric": "f1", "primary_metric_value": 0.65, "metrics": {"fnr": 0.12},
               "confusion": {"tp": 88, "fn": 12, "fp": 0, "tn": 100}}
    assert not any("0.70" in x for x in derive_limitations("tabular", metrics, _DOSSIER))
    declared = {"source": "declared", "verified": False, "values": {"target_fnr": 0.05}}
    limits = derive_limitations("tabular", metrics, _DOSSIER, declared)
    assert any("false-negative rate 0.120 (95% interval" in x and "exceeds the declared target" in x
               for x in limits)


def test_no_limitation_raised_is_not_no_limitation() -> None:
    """Nothing flagged says which checks ran and that it proves nothing more."""
    limits = derive_limitations("tabular", {"primary_metric_value": 0.9, "metrics": {}},
                                _DOSSIER)
    assert len(limits) == 1 and "does not establish that the model has none" in limits[0]
    assert "No automated limitations detected" not in limits[0]
