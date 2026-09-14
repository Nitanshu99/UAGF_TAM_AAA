"""The case-06 bundle: where it is, what it says, and which file each uploader can take.

One bundle/UI mismatch is handled rather than hidden: the Annex IV §5, §8 and §9
uploaders accept ``pdf/doc/docx`` only, while the bundle names the ``.txt``
siblings. :func:`uploadable` swaps in the PDF that sits beside it and says so;
without that the run silently loses three documents and reads as thinner than
the baseline.
"""
from __future__ import annotations

import json
import pathlib

from scripts.wizard_fill import form_spec as spec

#: Each step's own heading, as ``section_title`` renders it — the only reliable
#: signal that a transition has landed.
HEADINGS = {
    1: "What have you got?",
    2: "A few things only you can tell us",
    3: "Tell us about your system",
}

CASE_DIR = pathlib.Path("mock/06_mariposa_edu_gmbh")

#: Documents the bundle ships that no Stage B field names. They are real audit
#: evidence — the Annex IV §1 technical documentation, the model card and the
#: system description — and nothing in the pipeline reads them unless they go in
#: here, where ``ingest_documents`` puts them in the collection phases 1-5 query.
#: ``answers.md`` is excluded: it is the sheet Stage A and Stage B were written
#: from for this harness, not a document Mariposa supplied.
FREE_FORM_DOCS = (
    "docs/mariposa_technical_documentation.txt",
    "docs/model_card.md",
    "docs/evidence.txt",
    "docs/performance_metrics.json",
)


def load_case(case_dir: pathlib.Path = CASE_DIR) -> tuple[dict, dict]:
    """Read the case's Stage A and Stage B declarations.

    :param case_dir: The intake bundle.
    :returns: ``(stage_a, stage_b)``.
    """
    def read(name: str) -> dict:
        with (case_dir / name).open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return read("stage_a.json"), read("stage_b.json")


def annex_labels(stage_a: dict) -> list[str]:
    """Annex III section numbers rendered as the labels the form offers.

    :param stage_a: The Stage A declaration.
    :returns: The labels, in declaration order, for sections the form knows.
    """
    from aaa.ui.wizard.constants import ANNEX_III_LABELS

    return [ANNEX_III_LABELS[str(s)] for s in stage_a.get("declared_annex_iii_sections") or []
            if str(s) in ANNEX_III_LABELS]


def uploadable(field: str, value: str, case_dir: pathlib.Path) -> pathlib.Path | None:
    """The file to attach for *field*, honouring what its uploader accepts.

    :param field: A Stage B URI field.
    :param value: The path the bundle names.
    :param case_dir: The intake bundle, for resolving relative paths.
    :returns: An existing file the uploader will take, or ``None``.
    """
    allowed = spec.accepted_types(field)
    path = pathlib.Path(value)
    if not path.is_file():
        path = case_dir / pathlib.Path(*path.parts[1:]) if len(path.parts) > 1 else path
    if not path.is_file():
        return None
    if path.suffix.lstrip(".").lower() in allowed:
        return path
    for ext in allowed:
        sibling = path.with_suffix(f".{ext}")
        if sibling.is_file():
            print(f"      {field}: uploader takes {allowed}, "
                  f"using {sibling.name} instead of {path.name}")
            return sibling
    return None


__all__ = ["CASE_DIR", "FREE_FORM_DOCS", "HEADINGS", "annex_labels", "load_case", "uploadable"]
