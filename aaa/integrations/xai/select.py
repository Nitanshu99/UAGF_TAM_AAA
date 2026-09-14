"""Settings-driven factory for the explainability & fairness provider."""
from __future__ import annotations

from aaa.integrations.base import EvidenceProvider
from aaa.integrations.xai.external import ExternalXAIProvider
from aaa.integrations.xai.internal import InternalXAIProvider
from aaa.settings import AAASettings, settings


def select_xai_provider(cfg: AAASettings | None = None) -> EvidenceProvider:
    """Return the provider selected by ``S6_XAI_MODE``.

    :param cfg: Settings override (tests); defaults to the singleton.
    :type cfg: AAASettings | None
    :returns: External client when the mode is ``external``, else internal.
    :rtype: EvidenceProvider
    """
    cfg = cfg or settings
    if cfg.s6_xai_mode.lower() == "external":
        return ExternalXAIProvider(cfg.s6_xai_base_url, cfg.s6_xai_bearer_token or None)
    return InternalXAIProvider()
