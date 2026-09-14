"""Lazy third-party imports with a friendly install hint."""
from __future__ import annotations

from typing import Any


def require(modname: str, pip_name: str | None = None) -> Any:
    """Import *modname* with a friendly error if the package is missing.

    :param modname: Dotted module path to import.
    :param pip_name: Pip package name when it differs from the module name.
    :returns: The imported module.
    :raises SystemExit: With install instructions when the import fails.
    """
    try:
        return __import__(modname, fromlist=["*"])
    except ImportError as exc:
        pkg = pip_name or modname.split(".")[0]
        raise SystemExit(
            f"missing optional dependency '{pkg}' required for ingestion.\n"
            f"  install: pip install {pkg}\n  (original error: {exc})"
        ) from exc
