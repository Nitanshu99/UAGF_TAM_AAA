"""The Agent 14 client brief, rendered as a customer-facing PDF.

The brief is the one deliverable written to be read without an auditor beside
you, and it was the only one with no PDF: the results page offered the formal
report as a PDF and the plain-language summary not at all.
"""
from __future__ import annotations

from reportlab.platypus import Paragraph, Table

from aaa.tools.report_render.pdf.brief import build_brief_pdf, markdown_flowables
from aaa.tools.report_render.pdf.markdown_inline import escape, inline

_BRIEF = """# Mariposa — what the audit found

Mariposa-Edu GmbH · engagement `eng-06` · 2026-09-10

> **Result: Not met (FAIL).** Auditor's opinion: adverse.

## In short

The system failed this audit.

## What is holding the result back

- Art. 10 (Data and data governance): you declared no special-category data.
- Art. 15 (Accuracy, robustness): no runnable model was supplied.

| Requirement | What it covers | Result |
|---|---|---|
| Art.10 | Data and data governance | Not met |
| Art.43 | Conformity assessment route | Met |
| Art.15§1 | Accuracy | Could not be checked |

### Art. 10

**What you told us** — nothing to declare.
"""


def test_it_renders_a_pdf():
    pdf = build_brief_pdf(_BRIEF, "eng-06")
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000


def test_every_block_becomes_a_flowable():
    flow = markdown_flowables(_BRIEF)
    assert any(isinstance(f, Table) for f in flow)
    text = " ".join(f.text for f in flow if isinstance(f, Paragraph))
    for expected in ("Mariposa", "In short", "Art. 10", "no runnable model"):
        assert expected in text


def test_the_table_drops_its_rule_row_and_keeps_the_rest():
    table = next(f for f in markdown_flowables(_BRIEF) if isinstance(f, Table))
    rows = table._cellvalues
    assert len(rows) == 4          # header + three articles, no |---| row
    assert len(rows[0]) == 3
    assert "Requirement" in rows[0][0].text


def test_bold_and_code_survive_as_markup():
    assert inline("**hi**") == "<b>hi</b>"
    assert inline("`x`") == '<font face="Courier">x</font>'
    assert inline("a **b** and `c`") == 'a <b>b</b> and <font face="Courier">c</font>'


def test_customer_text_is_escaped_before_markup():
    """The brief quotes customer strings; a stray `<` or `&` would otherwise
    raise inside the PDF build and cost the whole document."""
    assert escape("A & B <tag>") == "A &amp; B &lt;tag&gt;"
    assert build_brief_pdf("# A & B <script>\n\nbody & more\n").startswith(b"%PDF-")


def test_an_unrecognised_line_is_kept_not_dropped():
    """A construct the renderer does not know must still reach the reader."""
    flow = markdown_flowables("1. numbered item\n")
    assert any(isinstance(f, Paragraph) and "numbered item" in f.text for f in flow)


def test_an_empty_brief_still_produces_a_document():
    assert build_brief_pdf("").startswith(b"%PDF-")


def test_headings_map_to_descending_styles():
    flow = markdown_flowables("# One\n\n## Two\n\n### Three\n")
    styles = [f.style.name for f in flow if isinstance(f, Paragraph)]
    assert styles == ["title", "h1", "h2"]
