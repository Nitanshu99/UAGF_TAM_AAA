"""Behavioural tests for the NLP text perturbation behind the T11 probe."""
from __future__ import annotations

import random

import pandas as pd

from aaa.tools.robustness_probe.logger import _perturb
from aaa.tools.robustness_probe.run_perturbation_probe import _run_perturbation_probe
from aaa.tools.robustness_probe.text_perturb import corrupt_text, perturb_text


def test_perturb_changes_text_for_positive_epsilon():
    """eps > 0 corrupts non-empty string cells (no more identity stub)."""
    texts = ["senior python engineer with ml pipeline experience"] * 5
    out = perturb_text(texts, 0.2)
    assert out != texts
    assert len(out) == len(texts)


def test_perturb_is_deterministic_for_fixed_seed():
    """Same seed → same corruption, so T11 re-runs are reproducible."""
    src = ["curriculum vitae of a warehouse logistics coordinator"] * 3
    assert perturb_text(src, 0.1, seed=7) == perturb_text(src, 0.1, seed=7)


def test_dataframe_numeric_columns_untouched():
    """nlp perturbation corrupts text columns only; numerics pass through."""
    df = pd.DataFrame({"cv_text": ["experienced data analyst"] * 3,
                       "years": [3, 5, 7]})
    out = _perturb(df, 0.3, "nlp")
    assert list(out["years"]) == [3, 5, 7]
    assert any(a != b for a, b in zip(out["cv_text"], df["cv_text"]))


def test_llm_and_agentic_stay_identity():
    """Prompt-level modalities keep the identity behaviour (UAGF-TAM-L's job)."""
    df = pd.DataFrame({"prompt": ["hello world"]})
    for modality in ("llm", "agentic"):
        assert _perturb(df, 0.5, modality) is df


def test_empty_string_and_zero_epsilon_unchanged():
    """Degenerate inputs return unchanged text."""
    rng = random.Random(1)
    assert corrupt_text("", 0.3, rng) == ""
    assert corrupt_text("stable", 0.0, rng) == "stable"


def test_probe_entry_reports_honest_nlp_labels():
    """nlp probe entries carry text_perturbation/char-noise, not textattack."""
    texts = ["applicant with strong sql and reporting background"] * 20
    labels = [1] * 10 + [0] * 10

    def predictor(X):
        return [1 if "sql" in t else 0 for t in X]

    entry = _run_perturbation_probe("nlp", predictor, texts, labels,
                                    clean_acc=0.5, epsilon=0.2)
    assert entry["attack_family"] == "text_perturbation"
    assert entry["tool"] == "char-noise"
    assert entry["probe_name"].startswith("char_noise_eps_")
