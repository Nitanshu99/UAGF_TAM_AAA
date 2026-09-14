"""Stage a CLI intake bundle's declared documents into the evidence store.

``stage_b.json`` in the mock bundles names its supporting documents as
filesystem paths (``mock/06_…/docs/risk_management_system.txt``).
:func:`aaa.tools.client_doc_ingest.loading._load_document` resolves
``minio://`` URIs and nothing else, so every one of those paths loaded as
``None``: the ingest logged seven warnings and indexed zero chunks, and the
audit then ran with **no client-document evidence at all** — retrieval returning
"Client-doc seed: 0 passage(s)" on every phase that asked.

Nothing failed loudly. The run produced a full report over a dossier it had
never read, which is the same class of defect as F5 (placeholder artefacts
behind a confident verdict), one layer earlier.

The UI never had this problem: an upload goes through ``store_uploaded_file``
into ``customer_uploads`` and *is* a ``minio://`` URI by the time Stage B
records it. This module gives the CLI the same starting point.
"""
from __future__ import annotations

import mimetypes
import pathlib
from typing import TYPE_CHECKING, Any

from aaa.agents.intake_validator.errors import _CLIENT_DOC_URI_FIELDS
from aaa.cli.logger import logger

if TYPE_CHECKING:
    from aaa.platform.evidence import EvidenceStore


def _resolve(value: str, intake_dir: pathlib.Path) -> pathlib.Path | None:
    """Find the file a Stage B path refers to.

    Tried as given (absolute, or relative to the working directory), then
    relative to the intake bundle, then by its trailing ``<dir>/<name>`` — so a
    bundle works whichever directory the CLI was invoked from.

    :param value: The Stage B field's raw value.
    :param intake_dir: The resolved ``--intake-dir``.
    :returns: An existing file, or ``None``.
    """
    raw = pathlib.Path(value)
    tail = pathlib.Path(*raw.parts[-2:]) if len(raw.parts) > 1 else raw
    for candidate in (raw, intake_dir / raw, intake_dir / tail, intake_dir / raw.name):
        if candidate.is_file():
            return candidate
    return None


def seed_client_documents(store: "EvidenceStore", engagement_id: str,
                          stage_b: dict[str, Any], intake_dir: pathlib.Path) -> list[str]:
    """Rewrite Stage B's document paths to stored-artefact URIs, in place.

    :param store: Evidence store receiving the documents.
    :param engagement_id: Engagement the documents belong to.
    :param stage_b: Stage B payload; document fields are rewritten in place.
    :param intake_dir: The resolved ``--intake-dir``.
    :returns: Fields that name a document the bundle does not contain.
    """
    unresolved: list[str] = []
    for field in _CLIENT_DOC_URI_FIELDS:
        value = stage_b.get(field)
        if not isinstance(value, str) or not value or value.startswith("minio://"):
            continue
        path = _resolve(value, intake_dir)
        if path is None:
            unresolved.append(field)
            continue
        stage_b[field] = store.store_file(
            engagement_id=engagement_id,
            phase="customer_uploads",
            artefact_type=field,
            filename=path.name,
            content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            data=path.read_bytes(),
            agent_name="cli",
        )
        logger.info("[cli] staged %s -> %s", field, stage_b[field])
    if unresolved:
        # Loud, because the alternative is an audit that silently reports on a
        # dossier it never opened.
        logger.warning(
            "[cli] %d declared document(s) could not be found in %s and will "
            "NOT be part of the evidence this audit retrieves: %s",
            len(unresolved), intake_dir, ", ".join(unresolved))
    return unresolved


__all__ = ["seed_client_documents"]
