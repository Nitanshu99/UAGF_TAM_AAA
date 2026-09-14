"""Unit tests for model-artefact layout inference (fix F6/F7, findings S4/S5/S7)."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from aaa.tools.model_meta import (
    DIRECTORY,
    SINGLE_FILE,
    archive_members,
    infer_artifact_kind,
    suggest_entrypoint,
)

_REAL_BUNDLE = Path("mock/04_legalmindd_ai_ltd/model/lexai_v2_stub.zip")


def _zip(names: list[str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name in names:
            archive.writestr(name, b"x")
    return buffer.getvalue()


def test_model_suffix_is_a_single_file() -> None:
    """A bare weights file is one artefact."""
    assert infer_artifact_kind("creditguard_v2.1.joblib") == SINGLE_FILE
    assert infer_artifact_kind("minio://eng/uploads/harboursense_v1.4.pkl") == SINGLE_FILE


def test_archive_and_extensionless_names_are_directories() -> None:
    """A bundle arrives as a .zip; a snapshot path has no suffix at all."""
    assert infer_artifact_kind("lexai_v2_stub.zip") == DIRECTORY
    assert infer_artifact_kind("file:///models/mistral_snapshot") == DIRECTORY


def test_unknown_suffix_declares_nothing() -> None:
    """No confident answer yields None, so the hand-off warns instead."""
    assert infer_artifact_kind("readme.txt") is None
    assert infer_artifact_kind("") is None
    assert infer_artifact_kind(None) is None


def test_members_exclude_packaging_noise() -> None:
    """``__MACOSX`` and ``.DS_Store`` are not model content."""
    data = _zip(["config.json", "__MACOSX/._config.json", ".DS_Store", "model.safetensors"])
    assert archive_members(data) == ["config.json", "model.safetensors"]


def test_unreadable_archive_returns_empty_not_raises() -> None:
    """A corrupt upload must not break the wizard."""
    assert archive_members(b"not a zip at all") == []


def test_entrypoint_prefers_weights_over_config() -> None:
    """The loadable object wins over the files describing it."""
    members = archive_members(_zip(["config.json", "model.safetensors", "vocab.txt"]))
    assert suggest_entrypoint(members) == "model.safetensors"


def test_entrypoint_follows_the_weight_priority_order() -> None:
    """Real weights beat a pickled wrapper when a bundle holds both."""
    members = archive_members(_zip(["wrapper.joblib", "model.safetensors"]))
    assert suggest_entrypoint(members) == "model.safetensors"


def test_nested_snapshot_resolves_to_its_directory() -> None:
    """A zip wrapping one directory points at the directory, not a file in it."""
    members = archive_members(_zip(["snapshot/config.json", "snapshot/model.bin"]))
    assert suggest_entrypoint(members) == "snapshot"


def test_config_only_bundle_suggests_nothing() -> None:
    """No loadable candidate is answered with None, never with a guess.

    Both bundles in this repo are config-only stubs. Inventing an entrypoint for
    them would put a path in the hand-off that resolves to nothing.
    """
    members = archive_members(_REAL_BUNDLE.read_bytes())
    assert members == ["adapter_config.json", "config.json",
                       "generation_config.json", "tokenizer_config.json"]
    assert suggest_entrypoint(members) is None
    assert suggest_entrypoint([]) is None
