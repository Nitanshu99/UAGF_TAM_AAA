"""An upstream 504 is the provider giving up, not our ceiling being spent.

litellm raises ``litellm.Timeout`` for two unrelated events, and only the message
separates them. The 2026-09-09 Mariposa re-run lost evidence to both: a Verifier
call at **546 s against a 360 s ceiling** and a GovernanceAgent rerun at **486 s
inside a 600 s budget** — neither had spent its ceiling. The terminal-type rule
matched ``Timeout`` first and refused the retry, so the GovernanceAgent fell back
to its deterministic path and the Verifier critique was lost outright.
"""
from __future__ import annotations

import pytest

from aaa.platform.transient_retry import is_transient


class Timeout(Exception):  # noqa: N818 — the name is the fixture
    """Stands in for ``litellm.Timeout``, matched by type *name*.

    The ``Error`` suffix ruff asks for is exactly what must not be here: the
    classifier reads ``type(exc).__name__`` and litellm's real class is
    ``litellm.Timeout``, so renaming it would stop this exercising the branch
    that misfiled the run's two 504s.
    """


class APITimeoutError(Exception):
    """The other spelling litellm uses for the same class of failure."""


class BadRequestError(Exception):
    """A 4xx, which fails identically however often it is retried."""


#: Verbatim from the run's LLM audit trail.
MARIPOSA_504 = ("litellm.Timeout: Timeout Error: Nvidia_nimException - "
                "Error code: 504 - {'status': 504, 'title': 'Gateway Timeout'}")


def test_the_gateway_timeout_that_cost_phase_5_its_llm_pass_is_retried():
    """The acceptance criterion, stated as an assertion."""
    assert is_transient(Timeout(MARIPOSA_504)) is True


@pytest.mark.parametrize("message", [
    "Timeout Error: Nvidia_nimException - Error code: 504",
    "Error code: 502 - Bad Gateway",
    "upstream gateway timeout",
])
def test_every_upstream_gateway_status_survives_the_terminal_type_rule(message):
    """The marker is read from the message, since the type name cannot carry it."""
    assert is_transient(Timeout(message)) is True
    assert is_transient(APITimeoutError(message)) is True


def test_our_own_spent_ceiling_is_still_terminal():
    """Fix 39's rule is unchanged where its premise holds: retrying doubles the loss."""
    assert is_transient(Timeout("Request timed out. timeout value=120.0")) is False
    assert is_transient(APITimeoutError("Request timed out.")) is False


def test_a_bad_request_is_still_never_retried():
    """The allow-list stays an allow-list; this only re-files one misread class."""
    assert is_transient(BadRequestError("Error code: 400 - invalid schema")) is False


def test_an_unrecognised_failure_is_still_treated_as_terminal():
    """The safe default when we cannot recognise a failure is today's behaviour."""
    assert is_transient(RuntimeError("something nobody has seen before")) is False


def test_a_rate_limit_still_belongs_to_the_layers_that_pace_it():
    """A 429 is retried by the Flex path; a second retry here would fight it."""

    class RateLimitError(Exception):
        """Stands in for ``litellm.RateLimitError``."""

    assert is_transient(RateLimitError("Error code: 429 - Too Many Requests")) is False
