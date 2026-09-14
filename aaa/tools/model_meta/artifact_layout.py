"""Whether a model artefact is one file or a bundle — fix F6/F7 (findings S4, S5, S7).

S6 needs two facts the wizard could not previously supply: is the artefact a
single file or a directory (``model_artifact_kind``), and if a directory, what
inside it is the thing to load (``model_entrypoint``). Neither field existed
anywhere in this codebase, and neither had a control that could have produced
it — ``OPTIONAL_UPLOAD_FIELDS["model_artifact_uri"]`` is one ``st.file_uploader``,
so a Chronos wrapper or a Hugging Face snapshot had no way in at all.

The repo had already answered the transport question without writing it down:
``mock/02_retailiq_ag/model/`` and ``mock/04_legalmindd_ai_ltd/model/`` each ship
a ``.zip`` beside the extracted directory, and ``zip`` was already in the
uploader's accepted types. So a directory artefact arrives as an archive, and
this module reads it: the members are listed from the uploaded bytes, and the
entrypoint is suggested from what they contain.

**The suggestion is a default, never a decision.** ``suggest_entrypoint`` returns
``None`` rather than guessing when the bundle holds no loadable candidate — the
two bundles in this repo are config-only stubs, and inventing an entrypoint for
them would put a path in the hand-off that resolves to nothing, which is the
class of defect this whole backlog is removing.

.. note::
   ``kind`` here is *layout* — one file or a bundle. It is unrelated to
   :func:`aaa.platform.artifact_loader.infer_kind`, which resolves a
   *deserialisation* target (``joblib``, ``csv``, ``docx``). The two words
   collide in the domain; the concepts do not.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath
from typing import Final

#: Layout values, matching the S6 hand-off vocabulary exactly.
SINGLE_FILE: Final = "single_file"
DIRECTORY: Final = "directory"

#: Upload suffixes that carry a directory of files rather than one model.
ARCHIVE_SUFFIXES: Final[tuple[str, ...]] = (".zip",)

#: Suffixes that are one loadable model, most-preferred first. Order is the
#: entrypoint priority: real weights beat a wrapper, a wrapper beats a config.
WEIGHT_SUFFIXES: Final[tuple[str, ...]] = (
    ".safetensors", ".bin", ".pt", ".pth", ".onnx", ".joblib", ".pkl", ".pickle",
)

#: Archive members that are packaging noise, not model content.
_JUNK_PREFIXES: Final[tuple[str, ...]] = ("__MACOSX/", ".git/")
_JUNK_NAMES: Final[frozenset[str]] = frozenset({".DS_Store", "Thumbs.db"})


def infer_artifact_kind(name: str | None) -> str | None:
    """Infer ``model_artifact_kind`` from an artefact filename or URI.

    :param name: Uploaded filename or stored URI; ``None``/empty allowed.
    :returns: :data:`DIRECTORY` for an archive or an extension-less name (a
        snapshot directory), :data:`SINGLE_FILE` for a known model suffix, and
        ``None`` when there is no confident answer — the caller shows the user
        a control rather than declaring something it cannot support.
    """
    if not name:
        return None
    leaf = PurePosixPath(name.rsplit("/", 1)[-1])
    suffix = leaf.suffix.lower()
    if suffix in ARCHIVE_SUFFIXES:
        return DIRECTORY
    if suffix in WEIGHT_SUFFIXES:
        return SINGLE_FILE
    return DIRECTORY if not suffix else None


def archive_members(data: bytes) -> list[str]:
    """List the model-bearing files inside an uploaded archive.

    :param data: Raw archive bytes.
    :returns: Sorted member paths, packaging noise and directory entries
        removed; empty when *data* is not a readable zip.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = [i.filename for i in archive.infolist() if not i.is_dir()]
    except (zipfile.BadZipFile, OSError, ValueError):
        return []
    return sorted(
        n for n in names
        if not n.startswith(_JUNK_PREFIXES)
        and PurePosixPath(n).name not in _JUNK_NAMES
    )


def _common_top_level_dir(members: list[str]) -> str | None:
    """The single directory every member sits under, if there is exactly one."""
    tops = {m.split("/", 1)[0] for m in members if "/" in m}
    return tops.pop() if len(tops) == 1 and all("/" in m for m in members) else None


def suggest_entrypoint(members: list[str]) -> str | None:
    """Suggest ``model_entrypoint`` for a bundle's *members*.

    :param members: Output of :func:`archive_members`.
    :returns: The member path most likely to be the loadable model, or ``None``
        when the bundle holds no loadable candidate. ``None`` is a real answer:
        the user is then asked, rather than handed a path that resolves to
        nothing.
    """
    if not members:
        return None
    nested = _common_top_level_dir(members)
    if nested:
        return nested
    for suffix in WEIGHT_SUFFIXES:
        matches = sorted(m for m in members if m.lower().endswith(suffix))
        if matches:
            return matches[0]
    return None


__all__ = ["SINGLE_FILE", "DIRECTORY", "ARCHIVE_SUFFIXES", "WEIGHT_SUFFIXES",
           "infer_artifact_kind", "archive_members", "suggest_entrypoint"]
