"""Fetching an image from the evidence store for the report."""
from __future__ import annotations

import io
import logging
from typing import Any

from reportlab.lib.units import cm
from reportlab.platypus import Image

logger = logging.getLogger(__name__)


def fetch_image(uri: str | None, store: Any, width_cm: float, height_cm: float) -> Image | None:
    """Resolve a stored PNG into an :class:`Image` flowable, fail-soft.

    :param uri: ``minio://`` (or file) URI of the figure.
    :type uri: str | None
    :param store: Evidence store for URI resolution; may be ``None``.
    :type store: Any
    :param width_cm: Rendered width in centimetres.
    :type width_cm: float
    :param height_cm: Rendered height in centimetres.
    :type height_cm: float
    :returns: The image flowable, or ``None`` when unresolvable.
    :rtype: Image | None
    """
    if not uri:
        return None
    try:
        from aaa.platform.artifact_loader import load_artifact_from_uri
        data = load_artifact_from_uri(uri, store, "bytes")
        return Image(io.BytesIO(data), width=width_cm * cm, height=height_cm * cm)
    except Exception as exc:  # noqa: BLE001 — figures are strictly best-effort
        logger.warning("report figure %s unavailable: %s", uri, exc)
        return None


__all__ = ["fetch_image"]
