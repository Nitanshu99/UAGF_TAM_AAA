"""Unit tests for the restructure import-rewrite codemod.

Uses fictitious ``fake.*`` module paths so repo-wide codemod runs can never
rewrite this test's own fixtures.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "restructure_imports", Path("scripts/restructure_imports.py"))
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)
rewrite_imports = _MOD.rewrite_imports

_MAP = {"fake.render.pdf_theme": "fake.render.pdf.theme",
        "fake.wizard.step3": "fake.wizard.step3.page"}


def test_from_import_rewritten() -> None:
    """`from old import x` becomes `from new import x`."""
    src = "from fake.render.pdf_theme import STYLES\n"
    assert rewrite_imports(src, _MAP) == "from fake.render.pdf.theme import STYLES\n"


def test_plain_and_docstring_occurrences() -> None:
    """Plain imports and dotted references in prose are rewritten too."""
    src = ('import fake.render.pdf_theme\n'
           '"""See :mod:`fake.render.pdf_theme`."""\n')
    out = rewrite_imports(src, _MAP)
    assert out.count("fake.render.pdf.theme") == 2


def test_prefix_module_does_not_swallow_siblings() -> None:
    """Mapping `...step3` must not touch `...step3_model_meta`."""
    src = ("from fake.wizard.step3 import render_step_3\n"
           "from fake.wizard.step3_model_meta import render_model_meta\n")
    out = rewrite_imports(src, _MAP)
    assert "from fake.wizard.step3.page import render_step_3" in out
    assert "from fake.wizard.step3_model_meta import render_model_meta" in out


def test_longest_path_wins_and_no_re_rewrite() -> None:
    """Overlapping keys apply longest-first; dotted outputs are not re-matched."""
    mapping = {"pkg.audit_state": "pkg.audit_state.core",
               "pkg.audit_state_parts": "pkg.audit_state.parts"}
    src = "from pkg.audit_state_parts import X\nfrom pkg.audit_state import Y\n"
    out = rewrite_imports(src, mapping)
    assert "from pkg.audit_state.parts import X" in out
    assert "from pkg.audit_state.core import Y" in out
