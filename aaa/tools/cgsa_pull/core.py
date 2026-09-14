"""Part 4 of the former ``cgsa_pull`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_pull.fetch_once import _fetch_once  # noqa: F401
from aaa.tools.cgsa_pull.fixture_roots import fixture_roots
from aaa.tools.cgsa_pull.logger import (
    _DEFAULT_BASE_URL,
    _PINNED_SCHEMA_VERSION,
    CGSAPullError,
    _read_fixture,
)
from aaa.tools.cgsa_pull.pull_http import _pull_http  # noqa: F401


def cgsa_pull(
    assessment_id: str,
    base_url: str | None = None,
    bearer_token: str | None = None,
    schema_version: str | None = None,
    fixture_dir: str | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """
    Fetch the S4 CGSA payload for ``assessment_id``.

    Returns the parsed JSON object.  Raises ``CGSAPullError`` on:
      * fixture missing in fixture mode,
      * 404 Not Found,
      * exhausted retries on network / 5xx errors,
      * schema-version drift (``X-Schema-Version`` mismatch).
    """
    if not assessment_id:
        raise CGSAPullError("missing_assessment_id", {"assessment_id": assessment_id})

    pinned = schema_version or _PINNED_SCHEMA_VERSION
    # Resolved now, not at import: the CLI sets CGSA_FIXTURE_DIR while parsing
    # its arguments, which can be after this module was first imported.
    if fixture_dir or fixture_roots():
        return _read_fixture(assessment_id, fixture_dir, pinned)

    return _pull_http(
        assessment_id=assessment_id,
        base_url=base_url or _DEFAULT_BASE_URL,
        bearer_token=bearer_token,
        pinned_version=pinned,
        timeout_seconds=timeout_seconds,
    )
