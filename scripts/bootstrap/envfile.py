"""Read and edit ``.env`` in place, keeping its comments and order.

The file is the operator's: every comment in ``.env.example`` explains a knob,
and a rewrite that dropped them would leave the next reader with bare keys.
So known keys are replaced on their own line, and new ones are appended under
a dated header.
"""
from __future__ import annotations

import re
from pathlib import Path

_ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def read_values(path: Path) -> dict[str, str]:
    """Parse *path* the way the application will (quotes and ``${VAR}`` resolved).

    :param path: The ``.env`` file.
    :returns: Key → value; empty when the file does not exist.
    """
    if not path.is_file():
        return {}
    from dotenv import dotenv_values

    return {k: v for k, v in dotenv_values(path).items() if v is not None}


def raw_values(path: Path) -> dict[str, str]:
    """Parse *path* with quotes resolved but ``${VAR}`` references left in place.

    :param path: The ``.env`` file.
    :returns: Key → value; empty when the file does not exist.
    """
    if not path.is_file():
        return {}
    from dotenv import dotenv_values

    return {k: v for k, v in dotenv_values(path, interpolate=False).items() if v is not None}


def _render(value: str) -> str:
    """Quote *value* only when the dotenv grammar needs it."""
    if not value or not any(ch in value for ch in " #\"'"):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def set_values(path: Path, updates: dict[str, str],
               header: str = "Set by python bootstrap.py") -> None:
    """Assign every key in *updates*, in place where the key exists.

    :param path: The ``.env`` file (created when absent).
    :param updates: Key → value to write.
    :param header: Comment above keys the file did not have yet.
    """
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    pending = dict(updates)
    out: list[str] = []
    for line in lines:
        match = _ASSIGNMENT.match(line)
        key = match.group(1) if match else None
        if key in updates:
            out.append(f"{key}={_render(updates[key])}")
            pending.pop(key, None)
        else:
            out.append(line)
    if pending:
        out += ["", f"# --- {header} ---"] + [f"{k}={_render(v)}" for k, v in pending.items()]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
