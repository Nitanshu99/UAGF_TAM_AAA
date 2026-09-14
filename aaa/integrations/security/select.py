"""Settings-driven factory for the security & robustness provider."""
from __future__ import annotations

from aaa.integrations.base import EvidenceProvider
from aaa.integrations.security.external import ExternalSecurityProvider
from aaa.integrations.security.internal import InternalSecurityProvider
from aaa.settings import AAASettings, settings


def select_security_provider(cfg: AAASettings | None = None) -> EvidenceProvider:
    """Return the provider selected by ``S7_SEC_MODE``.

    :param cfg: Settings override (tests); defaults to the singleton.
    :type cfg: AAASettings | None
    :returns: External client when the mode is ``external``, else internal.
    :rtype: EvidenceProvider
    """
    cfg = cfg or settings
    if cfg.s7_sec_mode.lower() == "external":
        return ExternalSecurityProvider(cfg.s7_sec_base_url, cfg.s7_sec_bearer_token or None)
    return InternalSecurityProvider()
