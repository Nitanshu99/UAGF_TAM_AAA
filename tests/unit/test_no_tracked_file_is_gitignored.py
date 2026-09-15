"""No tracked file may match .gitignore (T-20260915-002).

A tracked file that an ignore rule matches survives only while nobody rebuilds the
index: ``git add -A`` over a fresh tree skips it without a word. The golden reference
in ``out/`` was such a file, and the single-commit rebuild of the repository dropped
it, failing every golden test on GitHub while local runs, which still had the file on
disk, passed. Either the file is data the repository needs and moves out of the
ignored path, or the rule is narrowed.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

_ROOT = pathlib.Path(__file__).parents[2]


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git")
    if git is None or not (_ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    return subprocess.run([git, "-C", str(_ROOT), *args], capture_output=True, text=True,
                          check=False)


def test_no_tracked_file_matches_an_ignore_rule() -> None:
    """``git ls-files -ci --exclude-standard`` lists tracked files that .gitignore matches."""
    listed = _git("ls-files", "-ci", "--exclude-standard")
    assert listed.returncode == 0, listed.stderr
    assert listed.stdout.split() == [], (
        "tracked but gitignored — a rebuild of the index would drop them:\n" + listed.stdout)


def test_the_golden_reference_is_not_ignored() -> None:
    """The fixture the golden tests read is outside every ignore rule."""
    probe = _git("check-ignore", "-q", "tests/golden/fixtures/eng-uci-german-credit-001.json")
    assert probe.returncode == 1
