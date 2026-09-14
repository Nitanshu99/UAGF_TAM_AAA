"""Populates the audit-state evidence landing zones via the selected providers.

Runs after the tier-2 phases so the internal adapters can reference the
artefacts those phases produced; external providers receive the full audit
state as the hand-off. Fail-soft: a provider error never interrupts the
pipeline — the landing zone records the failure instead.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.integrations.base import ProviderError
from aaa.integrations.gating import security_required, xai_required
from aaa.integrations.security import select_security_provider
from aaa.integrations.xai import select_xai_provider
from aaa.settings import AAASettings

logger = logging.getLogger(__name__)


def _evaluate(provider: Any, state: dict, label: str) -> dict[str, Any]:
    """Run one provider fail-soft; errors become an evidence stub.

    :param provider: The selected :class:`EvidenceProvider`.
    :type provider: Any
    :param state: The audit state.
    :type state: dict
    :param label: Log label (``xai`` / ``security``).
    :type label: str
    :returns: The evidence document, or an error stub on ProviderError.
    :rtype: dict[str, Any]
    """
    try:
        return provider.evaluate(state)
    except ProviderError as exc:
        logger.warning("%s provider failed: %s %s", label, exc.reason, exc.details)
        return {"evidence_source": "external", "error": exc.reason}


def _dispatch_one(state: dict, cfg: AAASettings | None, label: str,
                  required: bool, reason: str, select) -> dict[str, Any]:
    """Gate, then either evaluate the provider or record a not-required stub.

    :param state: The audit state.
    :type state: dict
    :param cfg: Settings override (tests); defaults to the singleton.
    :type cfg: AAASettings | None
    :param label: Log label (``xai`` / ``security``).
    :type label: str
    :param required: The gating decision from :mod:`aaa.integrations.gating`.
    :type required: bool
    :param reason: The gating reason (recorded either way is not-required).
    :type reason: str
    :param select: The provider factory (``select_xai_provider`` etc.).
    :type select: Any
    :returns: The evidence document.
    :rtype: dict[str, Any]
    """
    if not required:
        logger.info("%s not required: %s", label, reason)
        return {"evidence_source": "not_required", "reason": reason}
    return _evaluate(select(cfg), state, label)


def apply_provider_evidence(state: dict, cfg: AAASettings | None = None) -> dict:
    """Populate the xai/security evidence landing zones on *state*.

    Consults :mod:`aaa.integrations.gating` first — a provider is only
    invoked (internal or external) when the engagement's scope actually
    requires its evidence.

    :param state: The audit state, mutated and returned.
    :type state: dict
    :param cfg: Settings override (tests); defaults to the singleton.
    :type cfg: AAASettings | None
    :returns: *state* with ``xai_evidence`` / ``security_evidence`` populated.
    :rtype: dict
    """
    xai_ok, xai_reason = xai_required(state)
    xai = _dispatch_one(state, cfg, "xai", xai_ok, xai_reason, select_xai_provider)
    state["xai_evidence"] = xai
    state["xai_evidence_source"] = xai.get("evidence_source")

    sec_ok, sec_reason = security_required(state)
    security = _dispatch_one(state, cfg, "security", sec_ok, sec_reason,
                             select_security_provider)
    state["security_evidence"] = security
    state["security_evidence_source"] = security.get("evidence_source")
    return state
