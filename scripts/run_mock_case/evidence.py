"""Preflight: a real run must deliver URIs that still resolve (P9).

The post-fix run spent 3,756 s and 387k tokens and delivered a T17 and a T18
addressing nineteen artefacts by ``minio://`` URI, over a store that forgot all
of them when the process exited.  Nothing was broken: ``.env.example`` sets
``EVIDENCE_BACKEND=minio``, ``ARCHITECTURE.md`` explains why, and the seam
already refuses to degrade a configured MinIO to memory.  The setting was simply
never copied into the ``.env`` the run read, and nothing asked.

So this asks, once, before the first token is spent — the cost of finding out
afterwards is the whole run.
"""
from __future__ import annotations

import sys

_UNUSABLE = ("Start the local stack with `make up`, or set EVIDENCE_BACKEND=memory to "
             "accept deliverables whose minio:// URIs die with this process.")
_VOLATILE = ("Set EVIDENCE_BACKEND=minio and start the local stack with `make up` "
             "for an evidence chain a reviewer can still follow.")


def preflight_evidence_backend() -> int:
    """Open the configured evidence store before the pipeline spends anything.

    An unusable *configured* backend is fatal: the run would otherwise fail at
    its first artefact, minutes in.  A backend that works but does not persist
    is the operator's call — it is announced here, and the T18 issued at the end
    withholds its signature for the same reason.

    :returns: ``0`` to proceed, or a non-zero exit code.
    :rtype: int
    """
    from aaa.platform.evidence import EvidenceStore
    from aaa.settings import settings

    configured = str(settings.evidence_backend).strip().lower()
    try:
        store = EvidenceStore()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"error: EVIDENCE_BACKEND={configured} is unusable "
              f"({type(exc).__name__}: {exc}).\n{_UNUSABLE}",
              file=sys.stderr, flush=True)
        return 3
    if not store.is_durable:
        print(f"\n⚠ EVIDENCE_BACKEND={configured} does not survive this process: "
              "every minio:// URI in the delivered audit_state / T17 / T18 will "
              "be unresolvable once it exits, and the report will be issued "
              f"unsigned for that reason.\n  {_VOLATILE}\n",
              file=sys.stderr, flush=True)
    else:
        # Q10: this line's whole purpose is to be read *before* the run spends
        # anything, so it does not rely on the caller having line-buffered the
        # stream. Block-buffered, it reached the operator at exit — 5,088 s
        # after the decision it exists to inform.
        print(f"evidence backend: {configured} (durable — delivered URIs will resolve)",
              flush=True)
    return 0
