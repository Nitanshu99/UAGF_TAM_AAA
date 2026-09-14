"""The UI must be able to reach a case's CGSA, the way the CLI can.

The CLI takes ``--cgsa-fixture-dir`` per run. The Streamlit UI has no such flag,
so it gets whatever ``CGSA_FIXTURE_DIR`` happens to say — which on 2026-09-11
was ``scripts/fixtures/cgsa``, a directory holding five other cases and not
Mariposa's. Phase 5 dispatched three times, produced empty artefacts each time,
hit its dispatch cap, and the run finished with no ``cgsa_payload``, no T14/T15,
and Art. 9/12/17/72 unevidenced. Coverage read 50 %.

So ``CGSA_FIXTURE_DIR`` now takes several roots and each is searched, which lets
one setting cover every case — the only shape of fix that reaches a UI with
nowhere to put a per-run flag.
"""
from __future__ import annotations

import json
import os
import pathlib

import pytest

from aaa.tools.cgsa_pull import CGSAPullError, _find_fixture, cgsa_pull, fixture_roots


@pytest.fixture(name="roots")
def _roots(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """A shared fixture directory and a case bundle, as the repo has."""
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "other-case-001.json").write_text(
        json.dumps({"schema_version": "1.0.0", "id": "other"}), encoding="utf-8")
    bundle = tmp_path / "mock"
    nested = bundle / "06_case" / "cgsa"
    nested.mkdir(parents=True)
    (nested / "wanted-001.json").write_text(
        json.dumps({"schema_version": "1.0.0", "id": "wanted"}), encoding="utf-8")
    return shared, bundle


def test_several_roots_are_searched(roots, monkeypatch: pytest.MonkeyPatch) -> None:
    shared, bundle = roots
    monkeypatch.setenv("CGSA_FIXTURE_DIR", os.pathsep.join([str(shared), str(bundle)]))
    assert fixture_roots() == [str(shared), str(bundle)]


def test_a_case_bundle_is_found_without_naming_its_directory(roots) -> None:
    """`mock/<case>/cgsa/<id>.json` resolves from the `mock` root alone."""
    shared, bundle = roots
    found = _find_fixture("wanted-001", [str(shared), str(bundle)])
    assert found is not None and found.endswith("06_case/cgsa/wanted-001.json")


def test_a_direct_hit_beats_a_walk(roots) -> None:
    """The historical `{root}/{id}.json` layout keeps working, and wins."""
    shared, bundle = roots
    (shared / "wanted-001.json").write_text(
        json.dumps({"schema_version": "1.0.0", "id": "shared-copy"}), encoding="utf-8")
    found = _find_fixture("wanted-001", [str(shared), str(bundle)])
    assert found == str(shared / "wanted-001.json")


def test_the_environment_is_read_at_call_time(roots, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI assigns CGSA_FIXTURE_DIR while parsing args — after import."""
    shared, bundle = roots
    monkeypatch.delenv("CGSA_FIXTURE_DIR", raising=False)
    assert fixture_roots() == []
    monkeypatch.setenv("CGSA_FIXTURE_DIR", str(bundle))
    assert fixture_roots() == [str(bundle)]


def test_a_missing_fixture_says_where_it_looked(roots, monkeypatch: pytest.MonkeyPatch) -> None:
    """"Wrong directory" and "missing file" are different problems."""
    shared, bundle = roots
    monkeypatch.setenv("CGSA_FIXTURE_DIR", os.pathsep.join([str(shared), str(bundle)]))
    with pytest.raises(CGSAPullError) as caught:
        cgsa_pull("nope-001")
    assert caught.value.details["searched"] == [str(shared), str(bundle)]


def test_a_nonexistent_root_is_ignored_not_fatal(roots, monkeypatch: pytest.MonkeyPatch) -> None:
    shared, _ = roots
    monkeypatch.setenv("CGSA_FIXTURE_DIR", os.pathsep.join(["/no/such/dir", str(shared)]))
    assert fixture_roots() == [str(shared)]


# --- against the repo's own configuration -----------------------------------

_CASES = sorted(p.stem for p in pathlib.Path().glob("mock/*/cgsa/*.json"))


def _configured_roots() -> list[str]:
    """The roots ``.env`` configures.

    Read from the file rather than from ``os.environ``: ``aaa/__init__`` skips
    its dotenv bootstrap under pytest to keep the suite hermetic, so the ambient
    environment says nothing about how a real run is configured — and it is that
    configuration this test exists to check.
    """
    env = pathlib.Path(".env")
    if not env.is_file():
        return []
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("CGSA_FIXTURE_DIR="):
            raw = line.split("=", 1)[1].split("#", 1)[0].strip()
            return [part for part in raw.split(os.pathsep) if part]
    return []


@pytest.mark.skipif(not _CASES or not _configured_roots(),
                    reason="needs the mock bundles and a configured .env")
@pytest.mark.parametrize("assessment_id", _CASES)
def test_every_mock_case_resolves_from_the_configured_roots(assessment_id: str) -> None:
    """What the UI needs: one setting, every case reachable.

    This is the assertion that would have caught the 2026-09-11 run — case 06's
    assessment was unreachable from the configured root, Phase 5 produced
    nothing three times over, and the only symptom was a coverage number.
    """
    roots = [r for r in _configured_roots() if os.path.isdir(r)]
    assert _find_fixture(assessment_id, roots) is not None, (
        f"{assessment_id} is not reachable from CGSA_FIXTURE_DIR={roots}")


# --- the conventions A14 set when it closed M21 -----------------------------

def test_the_explicit_override_wins(roots, monkeypatch: pytest.MonkeyPatch) -> None:
    """``AAA_CGSA_FIXTURE_DIR`` is how a case runs against a real S5 export.

    A14 made it the override for ``scripts/run_mock_case``; it has to mean the
    same thing here, or the two entry points disagree about which assessment a
    case was audited against.
    """
    shared, bundle = roots
    monkeypatch.setenv("CGSA_FIXTURE_DIR", str(shared))
    monkeypatch.setenv("AAA_CGSA_FIXTURE_DIR", str(bundle))
    assert fixture_roots() == [str(bundle)]


def test_a_case_bundle_is_searched_before_the_shared_directory() -> None:
    """A14's rule: the case's own fixture is the more specific answer.

    Load-bearing, not cosmetic: four assessments exist in both places and have
    drifted — ``finclear-creditguard-001`` reads 38 controls in the shared copy
    and 10 in its bundle, so the order decides which audit a case gets.
    """
    configured = _configured_roots()
    if "mock" not in configured or "scripts/fixtures/cgsa" not in configured:
        pytest.skip("repo .env does not configure both roots")
    assert configured.index("mock") < configured.index("scripts/fixtures/cgsa")


# --- the duplicates must not drift further ----------------------------------

#: Assessments that already differ between their bundle and the shared copy, as
#: measured 2026-09-11. `finclear-creditguard-001` reads `controls_assessed: 38`
#: in the shared copy and `10` in its bundle — two different governance
#: assessments under one id. Recorded rather than repaired: the delivered runs
#: for these cases were audited against the bundle copy, so deciding which one
#: is authoritative is an engagement-owner call, not a test's.
_KNOWN_DRIFTED = frozenset({
    "finclear-creditguard-001",
    "harbourlogistik-harboursense-001",
    "legalmindd-lexai-001",
    "retailiq-demandpulse-001",
})


def _duplicated() -> dict[str, tuple[pathlib.Path, pathlib.Path]]:
    """Assessments that exist both in a mock bundle and in the shared folder."""
    shared_dir = pathlib.Path("scripts/fixtures/cgsa")
    pairs: dict[str, tuple[pathlib.Path, pathlib.Path]] = {}
    for bundled in pathlib.Path().glob("mock/*/cgsa/*.json"):
        shared = shared_dir / bundled.name
        if shared.is_file():
            pairs[bundled.stem] = (bundled, shared)
    return pairs


@pytest.mark.skipif(not _duplicated(), reason="no duplicated fixtures")
def test_no_new_fixture_duplicate_drifts() -> None:
    """A copy is only safe while the two copies agree.

    Two files under one assessment id is a trap: which audit a case gets then
    depends on how it was launched. The four in ``_KNOWN_DRIFTED`` are already
    in that state; this fails the moment a fifth joins them.
    """
    drifted = {
        name for name, (bundled, shared) in _duplicated().items()
        if bundled.read_bytes() != shared.read_bytes()
    }
    new = drifted - _KNOWN_DRIFTED
    assert not new, (
        f"{sorted(new)} now differ between mock/<case>/cgsa/ and "
        "scripts/fixtures/cgsa/ — one assessment id, two answers")
