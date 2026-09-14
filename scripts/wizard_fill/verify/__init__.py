"""Checks around a fill: labels against the UI source before, the form's state after.

``sources`` says which module must render which label, ``labels`` does the
comparison, and ``state`` reads the filled form back.
"""
from scripts.wizard_fill.verify.labels import verify_labels
from scripts.wizard_fill.verify.sources import CORE_UPLOAD_FIELDS, IMPORTED, SOURCES
from scripts.wizard_fill.verify.state import report_state

__all__ = ["CORE_UPLOAD_FIELDS", "IMPORTED", "SOURCES", "report_state", "verify_labels"]
