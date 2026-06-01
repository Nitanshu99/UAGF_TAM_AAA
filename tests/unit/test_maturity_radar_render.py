"""Tests for governance maturity radar chart rendering."""
from __future__ import annotations

import os
import tempfile

from aaa.tools.maturity_radar_render import maturity_radar_render


def test_maturity_radar_render_creates_png():
    out = tempfile.mktemp(suffix=".png")
    result = maturity_radar_render({"D1 Model Algorithm": 2.5, "D2 Data": 3.0}, out)
    assert result == out
    assert os.path.exists(result)
    assert os.path.getsize(result) > 0