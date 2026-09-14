"""Extracting a bundle into the place the code expects it, without redoing what is there."""
from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.bootstrap.steps.bundles.archive import find_prefix, regular_files
from scripts.bootstrap.steps.bundles.spec import Bundle, BundleError


def unpack(zip_path: Path, bundle: Bundle) -> tuple[int, int]:
    """Extract *zip_path* into ``bundle.target``.

    Existing files of the same size are left alone, so a re-run is a no-op and
    a corrected bundle still replaces what it changes.

    :param zip_path: The archive on disk.
    :param bundle: What it should contain and where it goes.
    :returns: ``(written, unchanged)`` file counts.
    :raises BundleError: On a wrong archive or an entry escaping the target.
    """
    root = bundle.target.resolve()
    written = kept = 0
    with zipfile.ZipFile(zip_path) as archive:
        members = regular_files(archive)
        prefix = find_prefix([m.filename for m in members], bundle)
        for info in members:
            dest = (root / info.filename[len(prefix):]).resolve()
            if root not in dest.parents:
                raise BundleError(f"{bundle.name}: entry {info.filename!r} escapes {root}")
            if dest.is_file() and dest.stat().st_size == info.file_size:
                kept += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.read(info))
            written += 1
    return written, kept


__all__ = ["unpack"]
