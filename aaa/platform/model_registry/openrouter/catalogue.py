"""OpenRouter's endpoint catalogue as this repo has read it — the numbers a pin sizes against.

Windows come from OpenRouter's ``/models/…/endpoints`` catalogue on 2026-09-10,
not estimated; an unrecognised slug or endpoint is refused by
:mod:`aaa.platform.model_registry.openrouter.provider` rather than guessed.
"""
from __future__ import annotations

#: The model the OpenRouter roster serves unless ``OPENROUTER_MODEL`` says otherwise.
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

#: model slug → {endpoint slug → the context window that endpoint publishes}.
PINNABLE_ENDPOINTS: dict[str, dict[str, int]] = {
    "nvidia/nemotron-3-ultra-550b-a55b": {
        "baseten/fp4": 202_800,
        "deepinfra/fp4": 262_144,
        "venice/fp8": 256_000,
    },
    "z-ai/glm-5.3-flash": {
        "novita/fp8": 1_048_576,
        "deepinfra/fp4": 1_048_576,
        "relace/fp4": 1_048_576,
    },
    "z-ai/glm-5.3": {
        "novita/fp8": 1_048_576,
    },
    # CoreWeave serves the smallest window of this model's twelve endpoints, and
    # registering it here is what makes that true for the token guard: LiteLLM's
    # map answers 1,048,576 for the *model*, so an unregistered pin would let the
    # guard permit prompts four times larger than this endpoint accepts.
    "minimax/minimax-m3": {
        "coreweave/fp4": 262_144,
        "gmicloud/fp8": 1_048_576,
    },
}
