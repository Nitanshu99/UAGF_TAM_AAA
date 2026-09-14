"""
aaa.data — File-based persistence layer for user inputs and audit results.

Data is written to the directory configured by ``AAA_DATA_DIR`` (default: ``data/``).

Layout::

    data/
      index.json                 # master engagement index
      inputs/<engagement_id>/
        engagement.json          # user-entered engagement metadata
        intake.json              # Stage A/B/C payloads
        files.json               # uploaded-file metadata list
      results/<engagement_id>/
        audit_result.json        # final verdict + KPIs
        artefacts.json           # phase artefact URI map
        findings.json            # blocking / positive findings + remediation
        compliance_matrix.json   # article → verdict map

Public API (import from here)::

    from aaa.data import writer, reader, index
"""
from aaa.data import index, reader, writer

__all__ = ["writer", "reader", "index"]
