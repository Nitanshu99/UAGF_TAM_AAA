"""Which provider failures are worth a second attempt — fix 39 (finding R7).

Seven calls in the 2026-09-03 five-case run failed, and five of them carried
``litellm.ServiceUnavailableError: Nvidia_nimException - Service temporarily
overloaded``.  A 503 is a statement about the provider's load in that second.
It says nothing about the artefact, and the run paid for reading it as evidence:
a critique that failed closed its artefact ``unverified`` and cost Art. 15 an
admitting artefact, and an Orchestrator turn that failed ended LLM-driven
sequencing for a whole engagement (finding R13).

The classifier is a **positive allow-list**, not an exclusion list, for the same
reason fix 42 exists: a provider has more ways to fail than a deny-list can
hold, and the safe default when we cannot recognise a failure is to treat it as
terminal — exactly as the code behaved before this fix.

Two classes are deliberately outside it:

* **A timeout is not transient.**  ``litellm.Timeout`` means the call already
  spent its whole ceiling.  Retrying it does not recover the phase, it doubles
  the loss — which is finding R1 made worse.  The two ``ReportArchitect``
  timeouts in the run (187.0 s each against a 120 s client ceiling) are
  finding R6's to fix, not this one's.

  **Unless the provider's gateway is the one that gave up.**  litellm raises
  ``litellm.Timeout`` for two different events, and only the message separates
  them: our ceiling expiring, and an upstream ``504``.  The 2026-09-09 Mariposa
  re-run failed twice this way — a Verifier call at **546 s against a 360 s
  ceiling** and a GovernanceAgent rerun at **486 s inside a 600 s budget**.
  Neither had spent its ceiling, so the paragraph above does not describe them:
  they are the NIM gateway abandoning a long generation, which is a statement
  about the provider in that second and nothing about the artefact.  Both cost
  real evidence — the GovernanceAgent fell back to its deterministic path, and
  the Verifier critique was lost — for a failure the retry above already exists
  to absorb.  ``"gateway timeout"`` was in :data:`_TRANSIENT_MESSAGES` from the
  start; the terminal-type check simply reached it first.
* **A 429 stays with the layers that own it.**  Rate limiting is paced by
  :mod:`aaa.platform.rate_limit` before the call and retried with backoff by
  the Flex path in :mod:`aaa.platform.flex_retry`.  A second retry here would
  fight both.

  **Unless the provider behind the router is the one saturated.**  OpenRouter
  answers "<model> is temporarily rate-limited upstream. Please retry shortly"
  with a 429 that is neither our pacing nor our quota — neither layer above sees
  it. On 2026-09-14 (11:30, case 03 on MiniMax) every call in two phases made one
  attempt, critiques closed ``unverified`` and three agents fell back. That 429 is
  retried here; a daily-limit or credit 429 is not, because waiting seconds does
  not restore a quota.
"""
from __future__ import annotations

#: Exception type names that mean "the provider was momentarily unable", never
#: "the request was wrong". Substring-matched against ``type(exc).__name__``.
_TRANSIENT_TYPES: tuple[str, ...] = (
    "ServiceUnavailable",       # litellm.ServiceUnavailableError — the run's 5
    "APIConnectionError",       # socket dropped before a reply
    "InternalServerError",      # 500 from the gateway, not from the request
)

#: Type names that are never retried even if a message looks transient. A
#: timeout has already spent its budget (R1); a 4xx will fail identically.
_TERMINAL_TYPES: tuple[str, ...] = (
    "Timeout", "BadRequest", "Authentication", "PermissionDenied",
    "NotFound", "RateLimit", "ContextWindowExceeded", "UnprocessableEntity",
)

#: Message fragments carrying the same meaning when the type name does not.
_TRANSIENT_MESSAGES: tuple[str, ...] = (
    "service temporarily overloaded", "temporarily unavailable",
    "service unavailable", "connection reset", "connection aborted",
    "bad gateway", "gateway timeout",
    # The host could not be reached at all — a dropped network or failed DNS lookup
    # is a statement about that second, not the request (2026-09-13, 14:50–15:04:
    # every call failed once and was never retried; T-20260913-080).
    "cannot connect to host", "nodename nor servname", "name or service not known",
    "temporary failure in name resolution", "connection refused", "network is unreachable",
)

#: Markers of an *upstream* gateway giving up, which litellm reports wearing the
#: same ``Timeout`` type as our own expired ceiling. Matched against the message
#: before :data:`_TERMINAL_TYPES`, because the type name cannot tell them apart
#: and the terminal rule would otherwise claim both.
_UPSTREAM_GATEWAY_MARKERS: tuple[str, ...] = (
    "error code: 504", "gateway timeout", "error code: 502", "bad gateway",
)


#: A router's word for a saturated upstream provider: momentary, and says so.
_UPSTREAM_RATE_LIMIT_MARKERS: tuple[str, ...] = (
    "rate-limited upstream", "rate limited upstream", "temporarily rate-limited",
    "temporarily rate limited",
)
#: A 429 that is a spent quota: no backoff restores it within an audit.
_QUOTA_MARKERS: tuple[str, ...] = ("per-day", "per day", "quota", "credits", "insufficient")


def is_upstream_rate_limit(exc: BaseException) -> bool:
    """Whether *exc* is a router's temporary 429 for a saturated upstream, not a spent quota."""
    message = str(exc).lower()
    return (any(marker in message for marker in _UPSTREAM_RATE_LIMIT_MARKERS)
            and not any(marker in message for marker in _QUOTA_MARKERS))


def is_transient(exc: BaseException) -> bool:
    """Return True when *exc* is a momentary provider failure, worth one retry.

    :param exc: The exception raised by the provider call.
    :type exc: BaseException
    :returns: True only for a recognised transient class; False for anything
        unrecognised, so an unknown failure keeps today's terminal behaviour.
    :rtype: bool
    """
    type_name = type(exc).__name__
    message = str(exc).lower()
    # Asked before the terminal rule, not after: an upstream 504 arrives as
    # ``litellm.Timeout``, so the type name alone would file the provider's
    # failure as our own spent ceiling and refuse the retry it deserves.
    if any(marker in message for marker in _UPSTREAM_GATEWAY_MARKERS):
        return True
    if is_upstream_rate_limit(exc):
        return True
    if any(terminal in type_name for terminal in _TERMINAL_TYPES):
        return False
    if any(transient in type_name for transient in _TRANSIENT_TYPES):
        return True
    return any(fragment in message for fragment in _TRANSIENT_MESSAGES)


__all__ = ["is_transient", "is_upstream_rate_limit"]
