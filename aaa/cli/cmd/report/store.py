"""Evidence-store access for the batch report renderer.

Figures are embedded from ``minio://`` URIs recorded during the audit run, so
they only resolve when the store persists across processes. Kept separate from
the rendering loop because "can we reach the evidence?" is a different question
from "how is the PDF assembled?".
"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aaa.platform.evidence import EvidenceStore


def try_store() -> EvidenceStore | None:
    """Open the configured evidence store, or ``None`` if unavailable.

    Figures resolve only from a store that outlives the process that wrote
    them, so the question is put to the store — ``is_durable`` — rather than
    re-derived here from ``EVIDENCE_BACKEND``, which was this module's own copy
    of a predicate the store already owns.  Either mismatch is reported rather
    than passed off as "no figures".

    :returns: An ``EvidenceStore``, or ``None`` when figures cannot be resolved.
    :rtype: EvidenceStore | None
    """
    try:
        from aaa.platform.evidence import EvidenceStore
        store = EvidenceStore()
    except Exception as exc:  # noqa: BLE001 — degrade, but say so
        print(f"[report] evidence store unavailable ({type(exc).__name__}: {exc}); "
              f"rendering without figures.", file=sys.stderr)
        return None
    if not store.is_durable:
        print("[report] the configured evidence backend does not persist across "
              "processes — figures stored by the pipeline cannot be resolved "
              "from here; rendering without them.", file=sys.stderr)
        return None
    return store


def store_or_memory(store: EvidenceStore | None) -> EvidenceStore:
    """Return *store*, or an empty in-memory store when there is none.

    Agents that persist their own output (the brief writer stores the rendered
    document as an artefact) need a store object even when figures cannot be
    resolved; an empty memory store gives them one without pretending that
    anything in it survives the process.

    :param store: The result of :func:`try_store`.
    :returns: A usable ``EvidenceStore``.
    """
    from aaa.platform.evidence import EvidenceStore as _Store
    from aaa.platform.evidence.backend.memory import MemoryBackend

    return store if store is not None else _Store(backend=MemoryBackend())
