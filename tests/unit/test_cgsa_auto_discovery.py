"""The client's CGSA is found for them; the wizard never asks for its id.

Guards behaviour, not source text. The M1–M30 register shows why: fixes written
as "this string is not on the page" broke the moment a page was rewritten, while
the ones that asserted what a function returns survived.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.tools.cgsa_pull import discover_assessments, resolve_assessment_id


def _write(root: Path, name: str, org: str, system: str, aid: str | None = None) -> Path:
    """Write a minimal CGSA fixture and return its path."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{name}.json"
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "metadata": {"assessment_id": aid or name, "organisation_name": org,
                     "system_under_audit": system},
    }), encoding="utf-8")
    return path


@pytest.fixture(name="roots")
def _roots(tmp_path: Path) -> list[str]:
    """A case-shaped root plus a flat shared root, as the repo has."""
    _write(tmp_path / "mock" / "06_case" / "cgsa",
           "orbit-learning-001", "Orbit Learning GmbH", "Orbit v1.0.0")
    _write(tmp_path / "shared", "acme-001", "Acme Credit AI Ltd.", "Scorer v1.0.0")
    return [str(tmp_path / "mock"), str(tmp_path / "shared")]


def test_the_customer_never_types_the_assessment_id(roots: list[str]) -> None:
    """The names the wizard already collects are enough to find the CGSA."""
    assert resolve_assessment_id(
        "Orbit Learning GmbH", "Orbit", roots) == "orbit-learning-001"


def test_a_legal_form_is_not_part_of_the_identity(roots: list[str]) -> None:
    """"Orbit Learning" and "Orbit Learning GmbH" are the same client."""
    assert resolve_assessment_id(
        "orbit learning", "Orbit", roots) == "orbit-learning-001"


def test_the_system_version_is_not_part_of_the_identity(roots: list[str]) -> None:
    """The CGSA records "Orbit v1.0.0"; the wizard asks name and version apart."""
    assert resolve_assessment_id(
        "Orbit Learning GmbH", "Orbit v1.0.0", roots) == "orbit-learning-001"


def test_an_unknown_client_gets_no_assessment(roots: list[str]) -> None:
    """A first-time client is not handed somebody else's governance history."""
    assert resolve_assessment_id("Nobody Ltd", "Thing", roots) is None


def test_an_empty_form_resolves_to_nothing(roots: list[str]) -> None:
    """Before anything is typed there is no client to look up."""
    assert resolve_assessment_id("", "", roots) is None


def test_two_systems_at_one_client_are_split_by_system_name(tmp_path: Path) -> None:
    """One organisation, two assessments: the system name decides."""
    root = tmp_path / "mock" / "case" / "cgsa"
    _write(root, "acme-alpha-001", "Acme GmbH", "Alpha v1.0")
    _write(root, "acme-beta-001", "Acme GmbH", "Beta v2.0")
    roots = [str(tmp_path / "mock")]
    assert resolve_assessment_id("Acme GmbH", "Beta", roots) == "acme-beta-001"
    # Ambiguous is silence, never a guess: attaching the wrong self-assessment
    # would put another system's governance findings in this client's report.
    assert resolve_assessment_id("Acme GmbH", "", roots) is None


def test_discovery_prefers_the_copy_the_pull_will_read(tmp_path: Path) -> None:
    """Four assessments exist in two roots and have drifted (M21/A14).

    Discovery must name the first root's copy, because that is the one
    ``_find_fixture`` returns — offering an id resolved from the second would
    describe a payload the run never loads.
    """
    _write(tmp_path / "mock" / "case" / "cgsa", "dup-001", "Dup GmbH", "Sys v1.0")
    _write(tmp_path / "shared", "dup-001", "Dup GmbH", "Sys v1.0")
    roots = [str(tmp_path / "mock"), str(tmp_path / "shared")]
    found = [a for a in discover_assessments(roots) if a["assessment_id"] == "dup-001"]
    assert len(found) == 1
    assert found[0]["path"].startswith(str(tmp_path / "mock"))


def test_the_wizard_form_has_no_assessment_id_field() -> None:
    """No widget asks for it, so nothing can put the jargon back by accident."""
    from aaa.ui.wizard.step3 import defaults
    from aaa.ui.wizard.step3.stage_a import flags
    source = Path(flags.__file__).read_text(encoding="utf-8")
    assert "st.text_input" not in source
    assert "cgsa_assessment_id" not in defaults.EXTRACTED_A


def test_the_real_fixtures_resolve_for_every_mock_case() -> None:
    """Each shipped case's declared id is what its own names resolve to."""
    for stage_a_path in sorted(Path("mock").glob("*/stage_a.json")):
        cgsa_dir = stage_a_path.parent / "cgsa"
        if not cgsa_dir.is_dir():
            continue
        declared = {p.stem for p in cgsa_dir.glob("*.json")}
        stage_a = json.loads(stage_a_path.read_text(encoding="utf-8"))
        resolved = resolve_assessment_id(
            stage_a.get("provider_name", ""), stage_a.get("system_name", ""), ["mock"])
        assert resolved in declared, f"{stage_a_path}: resolved {resolved!r}"
