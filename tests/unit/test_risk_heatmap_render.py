"""Tests for risk heatmap PNG rendering."""
from __future__ import annotations

import os
import tempfile

from aaa.tools.risk_heatmap_render import risk_heatmap_render


def test_risk_heatmap_render_creates_png():
    out = tempfile.mktemp(suffix=".png")
    result = risk_heatmap_render(
        [{"finding_id": "F-001", "severity": "critical", "materiality": "material"}],
        out,
    )
    assert result == out
    assert os.path.exists(result)
    assert os.path.getsize(result) > 0