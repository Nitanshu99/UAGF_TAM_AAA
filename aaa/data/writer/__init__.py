"""aaa.data.writer — Persist user inputs and audit results to ``data/``.

Every public function writes (or appends) one logical record to disk and
updates the master ``data/index.json``.  Writes are atomic: data is written
to a ``.tmp`` sibling first, then renamed over the target file.
"""
from __future__ import annotations

from aaa.data.writer.atomic import normalized_company_name
from aaa.data.writer.customer import save_customer_artefacts
from aaa.data.writer.inputs import save_engagement, save_intake, save_uploaded_file
from aaa.data.writer.results import save_result

__all__ = [
    "save_engagement", "save_intake", "save_uploaded_file",
    "save_result", "save_customer_artefacts", "normalized_company_name",
]
