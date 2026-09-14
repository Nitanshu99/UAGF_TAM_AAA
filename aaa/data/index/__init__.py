"""aaa.data.index — Lightweight JSON index of all stored engagements.

The index lives at ``data/index.json`` and holds a summary row for every
engagement that has been persisted.  It is the fast lookup used by the
"list all stored engagements" query without scanning every sub-directory.

Schema (each entry in the ``engagements`` list)::

    {
        "engagement_id": "eng-001",
        "provider_name": "Acme",
        "system_name":   "CreditBot",
        "declared_risk_tier": "high",
        "status": "completed",
        "final_verdict": "PASS_WITH_OBSERVATIONS",   # null until audit runs
        "created_at":   "2025-06-01T10:00:00+00:00",
        "completed_at": "2025-06-01T10:42:00+00:00"  # null until audit runs
    }

Thread-safety note: writes use a file-level lock (``fcntl`` on POSIX,
``msvcrt`` on Windows) so concurrent FastAPI requests don't corrupt the file."""
from aaa.data.index.lock import _lock, _read_index, _unlock, _write_index  # noqa: F401
from aaa.data.index.upsert import delete, get, list_all, upsert  # noqa: F401

__all__ = [
    '_lock',
    '_unlock',
    '_read_index',
    '_write_index',
    'upsert',
    'get',
    'list_all',
    'delete',
]
