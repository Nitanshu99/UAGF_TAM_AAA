"""External security & robustness provider — POSTs the hand-off to the S7 API."""
from __future__ import annotations

import logging
from typing import Any

from aaa.integrations.handoff import build_handoff
from aaa.integrations.http_post import post_json
from aaa.integrations.postprocess import extract_partner_sections

logger = logging.getLogger(__name__)


class ExternalSecurityProvider:
    """HTTP client for the external security service's ``/api/v1/evaluate`` endpoint.

    :param base_url: Service root, e.g. ``http://localhost:8007``.
    :type base_url: str
    :param bearer_token: Optional bearer token.
    :type bearer_token: str | None
    :param timeout: Per-request timeout in seconds.
    :type timeout: float
    """

    def __init__(self, base_url: str, bearer_token: str | None = None,
                 timeout: float = 60.0) -> None:
        self._url = f"{base_url.rstrip('/')}/api/v1/evaluate"
        self._token = bearer_token or None
        self._timeout = timeout

    def evaluate(self, state: dict[str, Any]) -> dict[str, Any]:
        """POST the hand-off for *state* and return the service's evidence.

        :param state: The (JSON-serialisable) audit state.
        :type state: dict[str, Any]
        :returns: Evidence document with ``evidence_source: "external"``.
        :rtype: dict[str, Any]
        :raises aaa.integrations.base.ProviderError: On permanent HTTP failure.
        """
        payload, warnings = build_handoff(state)
        for warning in warnings:
            logger.warning("security handoff: %s", warning)
        response = post_json(self._url, payload, self._token, self._timeout)
        evidence = extract_partner_sections(response, "security_evidence", "security")
        evidence.setdefault("evidence_source", "external")
        return evidence
