"""T-20260913-103: the session sweep's scan over live objects raises no foreign warnings.

``isinstance`` over ``gc.get_objects()`` touched torch's deprecated module proxies,
and "torch.distributed.reduce_op is deprecated" was logged against
``loop_clients.py`` on every phase of every run.
"""
from __future__ import annotations

import asyncio
import warnings

import pytest

from aaa.platform.loop_clients import close_loop_sessions

pytest.importorskip("litellm.llms.custom_httpx.aiohttp_transport")


class _DeprecatedProxy:
    """An object that warns when ``isinstance`` reads its ``__class__``."""

    @property
    def __class__(self):  # type: ignore[override]  # pylint: disable=invalid-overridden-method
        warnings.warn("proxy attribute is deprecated", FutureWarning, stacklevel=2)
        return _DeprecatedProxy


def test_the_scan_swallows_warnings_raised_by_the_objects_it_inspects() -> None:
    """A warning-raising object alive during the sweep produces no warning."""
    proxy = _DeprecatedProxy()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert asyncio.run(close_loop_sessions()) == 0
    assert proxy is not None and not caught
