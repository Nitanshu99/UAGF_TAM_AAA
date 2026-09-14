"""An untested metric has no sample size; a measured noise result reaches T11.

T12 blocks and T10 global explanations reported sample_size 0 for work never done
(T-20260913-033, -039); T11 hardcoded noise_robustness null although the probe
measured it (-038).
"""
from __future__ import annotations

from aaa.agents.tier2.model_validator.t11 import build_t11, noise_summary
from aaa.tools.demographic_parity import demographic_parity
from aaa.tools.disparate_impact import disparate_impact
from aaa.tools.equal_opportunity import equal_opportunity
from aaa.tools.subgroup_metrics import subgroup_metrics
from aaa.tools.text_explain import token_importance

PROBES = [
    {"probe_name": "gaussian_noise_eps_0.05", "epsilon": 0.05, "adversarial_accuracy": 0.81},
    {"probe_name": "gaussian_noise_eps_0.2", "epsilon": 0.2, "adversarial_accuracy": 0.64},
    {"probe_name": "fgsm_eps_0.1", "epsilon": 0.1, "adversarial_accuracy": 0.3},
]


def test_untested_fairness_metrics_have_no_sample_size() -> None:
    """Every tool's not-tested stub says None, not 0."""
    for result in (demographic_parity(), equal_opportunity(), disparate_impact(), subgroup_metrics()):
        assert result["verdict"] == "NOT_TESTED" and result["sample_size"] is None


def test_an_unexplained_model_has_no_explanation_sample() -> None:
    """Nothing explained, so no sample."""
    assert token_importance(model=object())["sample_size"] is None


def test_noise_robustness_reports_the_most_severe_noise_tested() -> None:
    """Adversarial probes are not noise; the largest noise epsilon is the summary."""
    assert noise_summary(PROBES) == {"noise_type": "gaussian_noise", "noise_level": 0.2,
                                     "accuracy_under_noise": 0.64}
    assert noise_summary([PROBES[2]]) is None


def test_t11_carries_the_noise_result() -> None:
    """The measured noise result is in the artefact."""
    t11 = build_t11("eng-t", "tabular", {"probes": PROBES, "clean_accuracy": 0.9}, "now")
    assert t11["noise_robustness"]["accuracy_under_noise"] == 0.64


def test_a_forecast_is_not_probed_with_exact_match_accuracy() -> None:
    """Case 02: a continuous target scored 0.0 everywhere and read as an Art. 15 FAIL."""
    import pandas as pd

    from aaa.tools.robustness_probe import robustness_probe

    class _Forecaster:
        def predict(self, frame):
            return [float(v) * 1.01 for v in frame["lag_1"]]

    frame = pd.DataFrame({"lag_1": [100.0 + i * 1.37 for i in range(60)]})
    result = robustness_probe(model=_Forecaster(), X=frame,
                              y_true=[100.5 + i * 1.41 for i in range(60)], modality="time_series")
    assert result["overall_robustness_verdict"] == "NOT_TESTED"
    assert result["probes"] == [] and result["min_adversarial_accuracy"] is None
    assert "continuous" in result["skipped_reason"]


def test_a_cyber_t11_with_nothing_to_extend_still_meets_its_template() -> None:
    from aaa.agents.tier3.cyber_agent.t11_update import update_t11
    from aaa.platform.evidence.contract import artefact_schema_errors

    t11 = update_t11({}, "eng", "time_series", [], None, extended=False, probe_skipped="no model")
    assert t11["clean_accuracy"] is None
    assert not artefact_schema_errors("T11_robustness_report", t11)


def test_t07_can_say_the_data_was_not_examined() -> None:
    """Case 04 had no dataset; its honest INSUFFICIENT_EVIDENCE verdict failed the T07 enum."""
    import json
    from pathlib import Path

    enum = json.loads(Path("templates/T07_data_quality_report.json").read_text(encoding="utf-8"))[
        "properties"]["overall_quality_verdict"]["enum"]
    assert "INSUFFICIENT_EVIDENCE" in enum


def test_every_attack_family_the_probe_writes_is_in_the_t11_enum() -> None:
    """The NLP char-noise probe wrote 'text_perturbation', which T11 did not list (case 05)."""
    import json
    from pathlib import Path

    import pandas as pd

    from aaa.tools.robustness_probe.run_perturbation_probe import _run_perturbation_probe

    enum = json.loads(Path("templates/T11_robustness_report.json").read_text(encoding="utf-8"))[
        "properties"]["probes"]["items"]["properties"]["attack_family"]["enum"]
    for modality in ("tabular", "time_series", "cv", "nlp", "llm"):
        inputs = (pd.Series(["a b c d"] * 4) if modality in ("nlp", "llm")
                  else pd.DataFrame({"x": [0.1, 0.2, 0.3, 0.4]}))
        probe = _run_perturbation_probe(modality, lambda x: [1] * len(x), inputs, [1] * 4, 1.0, 0.1)
        assert probe is not None, modality
        assert probe["attack_family"] in enum, (modality, probe["attack_family"])
