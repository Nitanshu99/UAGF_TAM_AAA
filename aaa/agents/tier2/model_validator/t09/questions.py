"""What T09 asks of the provider's documents (Model Cards, Annex IV §2)."""
from __future__ import annotations

from aaa.tools.document_evidence import DENIALS, Question

T09_QUESTIONS = (
    Question("output_shape", "embedding vector dimensions output",
             (("*dimensional", "dimension*"), ("vector*", "embedding*", "output*")),
             DENIALS),
)

__all__ = ["T09_QUESTIONS"]
