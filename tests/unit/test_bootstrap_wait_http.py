"""The bootstrap health check opens web URLs only.

``urllib.request.urlopen`` also follows ``file://`` and custom schemes. The
bootstrap only ever polls a local service, so anything else is refused before it
reaches the opener rather than trusted to the caller.
"""
from __future__ import annotations

import pytest

from scripts.bootstrap.steps.app import wait_http


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://localhost/", "localhost:8000"])
def test_a_non_web_url_is_refused(url: str) -> None:
    """Refused up front, and without waiting out the timeout."""
    with pytest.raises(ValueError, match="not an http"):
        wait_http(url, timeout=1)


def test_an_unanswered_web_url_still_times_out() -> None:
    """The guard does not change what happens to a real URL that never answers."""
    with pytest.raises(RuntimeError, match="did not answer"):
        wait_http("http://127.0.0.1:9/", timeout=1)
