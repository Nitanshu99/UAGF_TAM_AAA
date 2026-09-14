"""Kind-specific deserialisation for the artifact loader."""
from __future__ import annotations

import io
import json

from aaa.platform.artifact_loader.errors import ArtifactUnavailable
from aaa.tools.client_doc_ingest import _extract_docx_pages


def deserialise(data: bytes, kind: str, uri: str | None):
    """Deserialize *data* according to *kind*.

    :param data: Raw artifact bytes.
    :param kind: Validated kind from :data:`aaa.platform.artifact_loader.errors.KINDS`.
    :param uri: Original URI (for error context and csv/tsv detection).
    :returns: The deserialized object.
    :raises ArtifactUnavailable: When deserialisation fails.
    """
    try:
        if kind == "bytes":
            return data
        if kind == "text":
            return data.decode("utf-8", errors="replace")
        if kind == "json":
            return json.loads(data.decode("utf-8"))
        if kind == "docx":
            pages = _extract_docx_pages(data)
            return "\n".join(text for _, text in pages if text)
        if kind == "joblib":
            try:
                import joblib  # type: ignore
            except ImportError as exc:  # pragma: no cover - environment gap
                raise ArtifactUnavailable(uri, kind, "joblib not installed") from exc
            return joblib.load(io.BytesIO(data))
        if kind == "csv":
            import pandas as pd
            sep = "\t" if (uri or "").lower().endswith(".tsv") else ","
            return pd.read_csv(io.BytesIO(data), sep=sep)
        if kind == "parquet":
            import pandas as pd
            return pd.read_parquet(io.BytesIO(data))
    except ArtifactUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 - any deserialisation failure → unavailable
        raise ArtifactUnavailable(
            uri, kind, f"deserialisation failed: {type(exc).__name__}: {exc}") from exc
    raise ArtifactUnavailable(uri, kind, "unreachable kind dispatch")
