"""Vendor-specific provenance questions, keyed by provider.

Every question stores into a :class:`ModelReference` key, so the schema stays
uniform across vendors while the wording changes: what Azure calls a
deployment name and Bedrock calls an ARN both land in ``model_id``, and S6
parses one shape regardless of who the customer buys from.
"""
from __future__ import annotations

from aaa.ui.wizard.step3.provenance.vendors.apis import API_QUESTIONS
from aaa.ui.wizard.step3.provenance.vendors.gateways import GATEWAY_QUESTIONS
from aaa.ui.wizard.step3.provenance.vendors.registries import REGISTRY_QUESTIONS

#: provider → ordered ``(model_reference key, label, help)`` questions.
VENDOR_QUESTIONS: dict[str, tuple[tuple[str, str, str], ...]] = {
    **REGISTRY_QUESTIONS, **API_QUESTIONS, **GATEWAY_QUESTIONS,
}

#: provider → the identifier that cannot change, shown as a hint.
VENDOR_PINS: dict[str, str] = {
    "huggingface": "commit SHA",
    "self_hosted": "server image digest + weight revision",
    "other": "whatever your vendor offers that cannot change",
    "openai": "dated snapshot id",
    "azure_openai": "deployment + model snapshot + api-version",
    "anthropic": "dated model id",
    "google_gemini": "pinned model version",
    "openrouter": "route slug + pinned variant + upstream provider",
    "nvidia_nim": "container image digest",
    "aws_bedrock": "model ARN",
    "mistral": "dated model id",
    "cohere": "dated model id",
}

def questions_for(provider: str) -> tuple[tuple[str, str, str], ...]:
    """Return the questions to ask for *provider*.

    Providers without a tailored branch fall back to the generic set, so a
    vendor added to the vocabulary is always askable — never a blank form.

    :param provider: A :data:`ModelProvider` value.
    :type provider: str
    :returns: Ordered ``(model_reference key, label, help)`` questions.
    :rtype: tuple[tuple[str, str, str], ...]
    """
    return VENDOR_QUESTIONS.get(provider) or VENDOR_QUESTIONS["other"]


def pin_for(provider: str) -> str:
    """Return the immutable-pin hint shown for *provider*.

    :param provider: A :data:`ModelProvider` value.
    :type provider: str
    :returns: Short description of what cannot change.
    :rtype: str
    """
    return VENDOR_PINS.get(provider, VENDOR_PINS["other"])


__all__ = ["VENDOR_QUESTIONS", "VENDOR_PINS", "questions_for", "pin_for"]
