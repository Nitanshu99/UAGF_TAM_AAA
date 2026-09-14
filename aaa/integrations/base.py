"""Shared provider contract and error type for partner integrations."""
from __future__ import annotations

from typing import Any, Protocol


class EvidenceProvider(Protocol):
    """A component that turns the audit state into an evidence document."""

    def evaluate(self, state: dict[str, Any]) -> dict[str, Any]:
        """Produce an evidence JSON document for *state*.

        :param state: The (JSON-serialisable) audit state.
        :type state: dict[str, Any]
        :returns: Evidence document with an ``evidence_source`` marker.
        :rtype: dict[str, Any]
        """
        # Protocol stub body: pyright requires the ellipsis, pylint dislikes it.
        ...  # pylint: disable=unnecessary-ellipsis


class ProviderError(Exception):
    """Raised when an external provider call fails permanently.

    :param reason: Machine-readable failure category.
    :type reason: str
    :param details: Context for logs / findings.
    :type details: dict[str, Any] | None
    """

    def __init__(self, reason: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.details = details or {}
