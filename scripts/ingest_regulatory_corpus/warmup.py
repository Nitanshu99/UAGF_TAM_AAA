"""Eager imports of heavy optional dependencies before the long pipeline run."""
from __future__ import annotations

from scripts.ingest_regulatory_corpus.deps import require


def warm_imports(dry_run: bool) -> None:
    """Cache heavy optional deps in ``sys.modules`` before corpus loading.

    This avoids a cold-import delay happening mid-run (which can appear as a
    silent hang or SIGINT delivery from a watching process).  llama_index's
    SentenceSplitter lazily loads NLTK → sklearn → numpy on first *use*, and
    sklearn's ``array_api_compat`` does ``from numpy import *`` which is slow
    on macOS cold-start — pre-importing numpy caches it.

    :param dry_run: When true, skip the embedding / Qdrant client imports.
    """
    print("  warming up imports …", end=" ", flush=True)
    try:
        import nltk  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
        import numpy  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
        import sklearn  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
    except ImportError:
        pass
    require("llama_index.core.node_parser")
    if not dry_run:
        require("qdrant_client")
        require("fastembed")
    print("ok", flush=True)
