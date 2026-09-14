"""toxicity_classifier — Discriminatory / toxic-output detector (§4.4).

Returns a structured dict compatible with the T13_output_sampling_log
``toxicity_results`` block.  Operates on up to ``sample_size`` model
predictions (200 by default per §4A T13 spec); each entry above the
``threshold`` is flagged as a discriminatory-pattern hit.

Production path:  ``detoxify`` ``Detoxify("original")`` — returns
                  toxicity, severe_toxicity, identity_attack, insult,
                  obscene, threat, sexual_explicit scores per prediction.
Fallback: regex/keyword heuristic over a small lexicon of
                  discriminatory / hateful tokens.

Usage
-----
    from src.tools.toxicity_classifier import toxicity_classifier

    result = toxicity_classifier(
        predictions=["...", "..."],
        sample_size=200,
        threshold=0.5,
    )"""
from aaa.tools.toxicity_classifier.compute.detoxify import _compute_detoxify  # noqa: F401
from aaa.tools.toxicity_classifier.compute.python import (  # noqa: F401
    _compute_python,
    _empty_result,
)
from aaa.tools.toxicity_classifier.core import toxicity_classifier  # noqa: F401
from aaa.tools.toxicity_classifier.logger import (  # noqa: F401
    _DEFAULT_SAMPLE_SIZE,
    _DEFAULT_THRESHOLD,
    _DISCRIMINATORY_KEYWORDS,
    _DISCRIMINATORY_RE,
    _assemble,
    logger,
)

__all__ = [
    'logger',
    '_DEFAULT_SAMPLE_SIZE',
    '_DEFAULT_THRESHOLD',
    '_DISCRIMINATORY_KEYWORDS',
    '_DISCRIMINATORY_RE',
    '_assemble',
    '_compute_detoxify',
    '_compute_python',
    '_empty_result',
    'toxicity_classifier',
]
