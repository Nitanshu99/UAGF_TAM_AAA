"""Reading a bundle archive: its real files, and the folder its markers sit under."""
from __future__ import annotations

import zipfile

from scripts.bootstrap.steps.bundles.spec import Bundle, BundleError

_SKIPPED = ("__MACOSX/", ".DS_Store")


def regular_files(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """The archive's regular files, minus macOS resource-fork noise.

    :param archive: An open zip archive.
    :returns: Its file entries, directories and ``__MACOSX`` noise excluded.
    """
    return [i for i in archive.infolist()
            if not i.is_dir() and not any(s in i.filename for s in _SKIPPED)]


def _has(names: list[str], marker: str) -> bool:
    """Whether *marker* is a file or directory among *names*."""
    return any(n == marker or n.startswith(marker + "/") for n in names)


def find_prefix(names: list[str], bundle: Bundle) -> str:
    """The wrapping folder (``"x/"``) the markers sit under, or ``""``.

    :param names: Every file name in the archive.
    :param bundle: The bundle whose markers must be present.
    :returns: The single wrapping folder with its trailing slash, or ``""``.
    :raises BundleError: When the markers are found under no single folder.
    """
    if all(_has(names, m) for m in bundle.markers):
        return ""
    tops = sorted({n.split("/", 1)[0] for n in names if "/" in n})
    for top in tops:
        inner = [n[len(top) + 1:] for n in names if n.startswith(top + "/")]
        if all(_has(inner, m) for m in bundle.markers):
            return top + "/"
    raise BundleError(f"{bundle.name} does not contain {list(bundle.markers)} "
                      "at its top level or under one folder")


__all__ = ["find_prefix", "regular_files"]
