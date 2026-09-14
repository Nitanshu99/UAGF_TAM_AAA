"""Sphinx configuration for the AAA — Autonomous AI Auditor documentation.

Build locally with::

    make -C docs html

The API reference is generated straight from the package docstrings via
``sphinx.ext.autodoc``; both reStructuredText field lists and NumPy-style
sections are supported through ``sphinx.ext.napoleon``.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "AAA — Autonomous AI Auditor"
author = "Nitanshu Idnani"
copyright = "2026, Nitanshu Idnani"  # pylint: disable=redefined-builtin
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "furo" if not os.environ.get("AAA_DOCS_BASIC") else "alabaster"
html_title = project
