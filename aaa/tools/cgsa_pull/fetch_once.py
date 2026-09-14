"""Part 2 of the former ``cgsa_pull`` module (auto-split)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from aaa.tools.cgsa_pull.logger import CGSAPullError, logger


def _fetch_once(url: str, headers: dict[str, str], pinned_version: str,
                timeout_seconds: float, assessment_id: str, attempt: int) -> dict[str, Any]:
    """Issue a single HTTP GET and verify the X-Schema-Version header."""
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        body = resp.read().decode("utf-8")
        got_version = resp.headers.get("X-Schema-Version")
        if got_version and got_version != pinned_version:
            raise CGSAPullError(
                "schema_version_drift",
                {"pinned": pinned_version, "got": got_version},
            )
        payload = json.loads(body)
        logger.info("cgsa_pull: %s ok (attempt=%d, bytes=%d)",
                    assessment_id, attempt, len(body))
        return payload
