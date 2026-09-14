"""The T10 interpretation: what was explained, of which output, and on what basis."""
from __future__ import annotations

from aaa.agents.tier2.model_validator.context import Explainability


def build_interpretation(modality: str, expl: Explainability) -> str:
    """Compose a short human-readable interpretation string.

    :param modality: Normalised system modality.
    :param expl: Explainability evidence from step 3.
    :returns: Interpretation paragraph for T10.
    """
    if expl.techniques == ["none"]:
        cause = (" ".join(expl.degraded) if expl.degraded
                 else "model artefact unavailable in this engagement.")
        return (f"No explainability techniques could be executed for {modality} "
                f"modality — {cause}")
    top = [f["feature"] for f in expl.global_expl.get("feature_importance", [])[:5]]
    caveat = ("" if not expl.degraded else
              " Not every technique ran; no attribution was reported for those that "
              "did not: " + " ".join(expl.degraded))
    explained = expl.local_expl[0].get("explained_output") if expl.local_expl else None
    of_output = f" of the model's {explained}" if explained else ""
    terms = expl.global_expl.get("vocabulary_size")
    basis = (f" Global importances are the model's own coefficients over its {terms} "
             "vectorizer terms; no instances were sampled for them." if terms else "")
    return (
        f"{modality} explainability: techniques={expl.techniques}. "
        f"Top global features: {', '.join(top) if top else 'n/a'}.{basis} "
        f"Local explanations{of_output} generated for {len(expl.local_expl)} representative "
        "instances. Reviewers should confirm feature attributions align with "
        "documented intended use." + caveat)


__all__ = ["build_interpretation"]
