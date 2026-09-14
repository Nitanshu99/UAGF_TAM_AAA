"""Executing one decided turn, and the constants the loop's breaker reads."""
from __future__ import annotations

#: Consecutive failed decisions the loop absorbs before giving up on the model.
#: One, because the decide call is **idempotent** — a failure changes nothing, so
#: the next turn asks the same question of the same state — and because two in a
#: row is no longer a transient: it is a provider or a contract that is down.
MAX_DECISION_FAILURES: int = 2
#: The history action recorded for a turn whose decision call failed. Deliberately
#: not one of the model's own actions: `_dispatch_count`, `_asked_for` and the
#: no-progress guard all read this history, and a failed turn must not look to
#: them like a move that was made.
DECISION_FAILED_ACTION = "DECISION_FAILED"


__all__ = ["DECISION_FAILED_ACTION", "MAX_DECISION_FAILURES"]
