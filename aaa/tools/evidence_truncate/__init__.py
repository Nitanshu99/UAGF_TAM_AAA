"""evidence_truncate — deterministic prompt-payload compressor (§8.1).

When :class:`aaa.platform.token_guard.ensure_within_budget` rejects an
oversized prompt, the caller can route the artefact payload through this
tool to drop the least-relevant top-level entries while always keeping
schema-required keys.

Ranking strategy (deterministic in both branches):

* **Dense branch** — when an OpenAI client + ``OPENAI_API_KEY`` are
  available: each top-level value is serialised, embedded with
  ``text-embedding-3-large`` (3072-dim), and ranked by cosine similarity
  against the query embedding.
* **Lexical branch** — token-overlap (Jaccard on lowercased ASCII word
  tokens). Produces stable scores from the same inputs without network.

The function never mutates the input; it returns a new dict containing
``preserve_keys`` plus as many ranked keys as fit inside ``max_tokens``,
annotated with ``_truncated`` + ``_dropped_keys`` markers so the Verifier
records that compression occurred."""
from aaa.tools.evidence_truncate.dense_scores import _dense_scores, _rank_keys  # noqa: F401
from aaa.tools.evidence_truncate.logger import (  # noqa: F401
    _DENSE_MODEL,
    _WORD_RE,
    TruncationResult,
    _cosine,
    _jaccard,
    _serialise,
    _tokens,
    logger,
)
from aaa.tools.evidence_truncate.truncate_payload import truncate_payload  # noqa: F401

__all__ = [
    'logger',
    '_DENSE_MODEL',
    '_WORD_RE',
    'TruncationResult',
    '_tokens',
    '_jaccard',
    '_serialise',
    '_cosine',
    '_dense_scores',
    '_rank_keys',
    'truncate_payload',
]
