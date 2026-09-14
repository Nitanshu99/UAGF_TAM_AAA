"""The Tier-3 cyber audit adds evidence, never copies of Phase 3's (T-20260914-037, case 01)."""
from __future__ import annotations

from aaa.agents.tier3.cyber_agent import probes as cyber_probes
from aaa.platform.prompt_registry.extract_agent_section import load_prompt

_PHASE3 = [{"probe_name": "noise_and_category_flip_eps_0.1", "attack_family": "feature_perturbation",
            "adversarial_accuracy": 0.905, "attack_success_rate": 0.047}]


def test_phase_3_probes_stand_and_are_not_repeated(monkeypatch) -> None:
    """The same seeded probe on the same rows is not run again or appended."""
    called: list = []
    monkeypatch.setattr(cyber_probes, "robustness_probe", lambda **kw: called.append(kw) or {})
    probes = list(_PHASE3)
    injection, findings, skipped, verdict = cyber_probes.run_specialist_probes(
        {}, "tabular", "eng-01", probes)
    assert (called, probes, injection, findings, verdict) == ([], _PHASE3, None, [], None)
    assert "not repeated" in skipped and "gradient- or query-based" in skipped


def test_without_phase_3_probes_the_probe_still_runs(monkeypatch) -> None:
    """With nothing to extend, the spawn's own probe is the evidence."""
    result = {"probes": [dict(_PHASE3[0])], "overall_robustness_verdict": "PASS"}
    monkeypatch.setattr(cyber_probes, "robustness_probe", lambda **kw: result)
    probes: list = []
    _injection, _findings, skipped, verdict = cyber_probes.run_specialist_probes(
        {}, "tabular", "eng-01", probes)
    assert (len(probes), skipped, verdict) == (1, "", "PASS")
    assert not probes[0]["probe_name"].startswith("CyberAgent_")


def test_the_cyber_prompt_carries_no_fixed_accuracy_share() -> None:
    """"Below 70% of clean accuracy → critical gap" is gone; the interval rule replaces it."""
    prompt = load_prompt("cyber")
    assert "70% of clean accuracy" not in prompt and "interval" in prompt
