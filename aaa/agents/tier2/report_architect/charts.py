"""Risk-heatmap / maturity-radar rendering and PNG persistence."""
from __future__ import annotations

import logging
import os
import tempfile
from typing import Any

from aaa.tools.maturity_radar_render import maturity_radar_render
from aaa.tools.risk_heatmap_render import risk_heatmap_render

logger = logging.getLogger(__name__)


def persist_png(agent: Any, engagement_id: str, local_path: str | None,
                kind: str) -> str | None:
    """Persist a rendered PNG to the evidence store; return a stable URI.

    The renderers write to a temp path that vanishes on reboot.  The bytes
    are stored so the report stays durable and reviewable, falling back to
    the local path only if persistence fails.

    :param agent: The calling :class:`ReportArchitect` instance.
    :param engagement_id: Engagement identifier.
    :param local_path: Renderer output path (may be missing).
    :param kind: Artefact type, e.g. ``risk_heatmap``.
    :returns: Evidence-store URI, the local path on failure, or ``None``.
    """
    if not local_path or not os.path.exists(local_path):
        return local_path
    try:
        with open(local_path, "rb") as handle:
            data = handle.read()
        return agent.store.store_file(
            engagement_id=engagement_id, phase="phase_6", artefact_type=kind,
            filename=f"{kind}.png", content_type="image/png", data=data,
            agent_name=agent.name)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to persist %s PNG (%s); using local path.", kind, exc)
        return local_path


def attach_charts(agent: Any, engagement_id: str, decl: dict[str, Any],
                  t18: dict[str, Any]) -> None:
    """Render the risk heatmap and maturity radar into *t18* (best effort).

    :param agent: The calling :class:`ReportArchitect` instance.
    :param engagement_id: Engagement identifier.
    :param decl: Declaration summary (for CGSA domain scores).
    :param t18: T18 payload mutated in place with the chart URIs.
    """
    heatmap_tmp = os.path.join(tempfile.gettempdir(), f"heatmap_{engagement_id}.png")
    try:
        local = risk_heatmap_render(findings=t18.get("blocking_findings", []),
                                    output_path=heatmap_tmp)
        t18["risk_heatmap_uri"] = persist_png(agent, engagement_id, local, "risk_heatmap")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("risk_heatmap_render failed (%s); continuing without heatmap.", exc)
        t18["risk_heatmap_uri"] = None
    radar_tmp = os.path.join(tempfile.gettempdir(), f"radar_{engagement_id}.png")
    domain_scores = decl.get("cgsa_domain_scores", {}) or {}
    try:
        local_radar = maturity_radar_render(domain_scores, radar_tmp) if domain_scores else None
        t18["maturity_radar_uri"] = (
            persist_png(agent, engagement_id, local_radar, "maturity_radar")
            if local_radar else None)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("maturity_radar_render failed (%s); continuing without radar.", exc)
        t18["maturity_radar_uri"] = None
