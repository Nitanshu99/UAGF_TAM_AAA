"""Check the driver's labels against the source that renders them.

A UI driver fails in one characteristic way: a label changes, its locator finds
nothing, the field is quietly left blank, and the run that follows is compared
against a baseline it no longer matches. That is not hypothetical — the uploader
this driver fills as "Risk management documentation" was "Risk management file"
one rename ago.

So the labels are grepped out of the rendering modules and compared with what
``form_spec`` holds, before a browser is launched. A mismatch stops the driver.
"""
from __future__ import annotations

import pathlib
import re

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.verify.sources import CORE_UPLOAD_FIELDS, SOURCES


def _normalise(text: str) -> str:
    """Collapse whitespace so a label split across source lines still matches."""
    return re.sub(r"\s+", " ", text)


def verify_labels() -> list[str]:
    """Every label the spec expects that its module no longer renders.

    :returns: Human-readable mismatches; empty when the spec is current.
    """
    problems: list[str] = []
    for target, labels in SOURCES.items():
        path = pathlib.Path(target.split(":", 1)[0])
        if not path.is_file():
            problems.append(f"{path} is gone — the wizard has been restructured")
            continue
        body = _normalise(path.read_text(encoding="utf-8"))
        for label in labels:
            if _normalise(label) not in body:
                problems.append(f"{path} no longer renders {label!r}")
    # The uploader labels come from a dict the spec imports, so the only thing
    # worth asserting is that the mapping is not empty and still covers the
    # Annex IV core the audit gates on.
    for field in CORE_UPLOAD_FIELDS:
        if spec.uploader_for(field) is None:
            problems.append(f"no uploader is declared for {field}")
    return problems


__all__ = ["verify_labels"]
