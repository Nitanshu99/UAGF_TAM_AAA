"""The document and corpus queries the model-validation synthesis retrieves against."""
from __future__ import annotations

PROMPT_NAME = "phase3_model"
_DOC_QUERY = "model architecture training evaluation performance explainability robustness"
_RAG_QUERY = ("Article 15 accuracy robustness cybersecurity Article 13 transparency "
              "explainability model performance")


__all__ = ["PROMPT_NAME", "_DOC_QUERY", "_RAG_QUERY"]
