"""Token explainability for traditional-NLP pipelines (T10): global importances and
per-instance contributions."""
from aaa.tools.text_explain.core import token_importance  # noqa: F401
from aaa.tools.text_explain.local import token_contributions  # noqa: F401

__all__ = ["token_contributions", "token_importance"]
