"""Shared golden-reference and fixture loaders for the golden-output tests.

The golden reference used to sit in ``out/``, a gitignored output directory that
``make report-german`` writes to. It was tracked only because it predated the ignore
rule, so the single-commit rebuild of the repository (``git add -A``) left it out and
every golden test failed on GitHub (T-20260915-002). It lives with the tests now.
"""
from __future__ import annotations

import json
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).parents[3]
_GOLDEN = _REPO_ROOT / "tests" / "golden" / "fixtures" / "eng-uci-german-credit-001.json"
_STAGE_B = _REPO_ROOT / "scripts" / "fixtures" / "uci_german_credit" / "stage_b.json"
_CGSA_FIXTURE = _REPO_ROOT / "scripts" / "fixtures" / "cgsa" / "uci-german-credit-001.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    """The committed golden reference audit-state."""
    return json.loads(_GOLDEN.read_text())


@pytest.fixture(scope="module")
def stage_b() -> dict:
    """The UCI German Credit Stage B dossier."""
    return json.loads(_STAGE_B.read_text())


@pytest.fixture(scope="module")
def cgsa_payload() -> dict:
    """The UCI German Credit CGSA handoff payload."""
    return json.loads(_CGSA_FIXTURE.read_text())
