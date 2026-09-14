"""Logger and the flat keyword view of Annex III points 1-4."""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.annex_iii_classify.points import POINTS_1_TO_4, flat_sections

logger = logging.getLogger(__name__)

_SECTIONS_1_TO_4: dict[str, dict[str, Any]] = flat_sections(POINTS_1_TO_4)
