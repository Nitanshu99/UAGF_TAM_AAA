"""The two bundles unpack to the right places, with or without a wrapping folder."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from scripts.bootstrap.steps.bundles import Bundle, BundleError, find_prefix, unpack


def _zip(path: Path, entries: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return path


def _bundle(tmp_path: Path) -> Bundle:
    return Bundle("mariposa.zip", tmp_path / "case", ("stage_a.json", "stage_b.json", "docs"))


def test_a_flat_archive_unpacks_to_the_target(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    archive = _zip(tmp_path / "mariposa.zip", {
        "stage_a.json": b"{}", "stage_b.json": b"{}", "docs/model_card.md": b"# card",
        "__MACOSX/._stage_a.json": b"junk", "docs/.DS_Store": b"junk"})
    assert unpack(archive, bundle) == (3, 0)
    assert (bundle.target / "docs" / "model_card.md").read_text() == "# card"
    assert not (bundle.target / "__MACOSX").exists()
    assert unpack(archive, bundle) == (0, 3)  # a re-run touches nothing


def test_a_wrapped_archive_has_its_folder_stripped(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    archive = _zip(tmp_path / "mariposa.zip", {
        "06_mariposa_edu_gmbh/stage_a.json": b"{}", "06_mariposa_edu_gmbh/stage_b.json": b"{}",
        "06_mariposa_edu_gmbh/docs/evidence.txt": b"e"})
    assert find_prefix([n for n in zipfile.ZipFile(archive).namelist()], bundle) == \
        "06_mariposa_edu_gmbh/"
    unpack(archive, bundle)
    assert (bundle.target / "stage_a.json").is_file()
    assert not (bundle.target / "06_mariposa_edu_gmbh").exists()


def test_the_wrong_archive_is_refused_by_name(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    archive = _zip(tmp_path / "mariposa.zip", {"regulatory_corpus/GDPR.html": b"<html>"})
    with pytest.raises(BundleError, match="stage_a.json"):
        unpack(archive, bundle)


def test_an_entry_escaping_the_target_is_refused(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    archive = _zip(tmp_path / "mariposa.zip", {
        "stage_a.json": b"{}", "stage_b.json": b"{}", "docs/x": b"", "../escape.txt": b"no"})
    with pytest.raises(BundleError, match="escapes"):
        unpack(archive, bundle)
    assert not (tmp_path / "escape.txt").exists()


def test_a_changed_file_is_rewritten_an_unchanged_one_kept(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    first = _zip(tmp_path / "v1.zip", {"stage_a.json": b"{}", "stage_b.json": b"{}", "docs/a": b"1"})
    unpack(first, bundle)
    second = _zip(tmp_path / "v2.zip", {"stage_a.json": b"{}", "stage_b.json": b"{}",
                                        "docs/a": b"22"})
    assert unpack(second, bundle) == (1, 2)
    assert (bundle.target / "docs" / "a").read_bytes() == b"22"
