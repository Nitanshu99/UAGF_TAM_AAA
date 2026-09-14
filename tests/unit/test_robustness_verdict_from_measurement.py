"""T-20260914-007: the robustness verdict comes from measured degradation and declared figures.

PASS at adversarial accuracy >= 0.70 and FAIL below 0.50 ignored the clean accuracy,
the sample size, and case 05's declared char-noise accuracy of 0.7375.
"""
from __future__ import annotations

from aaa.tools.robustness_probe.degradation import declared_levels
from aaa.tools.robustness_probe.verdict import decide

_CLEAN = [True] * 190 + [False] * 10


def _probe(kind: str, level: float, right: int) -> dict:
    flags = [True] * right + [False] * (200 - right)
    return {"probe_name": f"{kind}_eps_{level}", "epsilon": level,
            "adversarial_accuracy": right / 200, "_correct": flags}


def test_declared_keys_name_the_probe_they_can_be_checked_against() -> None:
    """Char noise at 0.1 is re-measurable; an L-inf gradient attack is not."""
    declared = {"adversarial_accuracy_char_noise_0_1": 0.7375,
                "adversarial_accuracy_l_inf_0_01": 0.74, "psi_baseline_max": 0.04}
    assert declared_levels(declared) == {("char_noise", 0.1): 0.7375}


def test_no_established_drop_passes_even_below_the_old_floor() -> None:
    """A 0.65 model that noise does not move is robust to that noise."""
    clean = [True] * 130 + [False] * 70
    assert decide([_probe("gaussian_noise", 0.1, 130)], clean, None) == ("PASS", [])


def test_an_established_drop_is_an_observation_and_is_explained() -> None:
    """0.95 → 0.80 on the same rows is a measured degradation."""
    verdict, notes = decide([_probe("gaussian_noise", 0.2, 160)], _CLEAN, None)
    assert verdict == "PASS_WITH_OBSERVATIONS" and "is established" in notes[0]


def test_an_overstated_declaration_fails() -> None:
    """Declared 0.90 under char noise at 0.1, measured 0.60: the declaration is not supported."""
    declared = {"adversarial_accuracy_char_noise_0_1": 0.90}
    verdict, notes = decide([_probe("char_noise", 0.1, 120)], _CLEAN, declared)
    assert verdict == "FAIL" and "Declared adversarial accuracy" in notes[0]


def test_a_corroborated_declaration_is_said() -> None:
    """Case 05 declares 0.7375 under char noise at 0.1; a matching measurement says so."""
    declared = {"adversarial_accuracy_char_noise_0_1": 0.7375}
    clean = [True] * 150 + [False] * 50
    verdict, notes = decide([_probe("char_noise", 0.1, 147)], clean, declared)
    assert verdict == "PASS" and "is corroborated" in notes[0]
    _, under = decide([_probe("char_noise", 0.1, 190)], _CLEAN, declared)
    assert "understates the measurement" in under[0]
