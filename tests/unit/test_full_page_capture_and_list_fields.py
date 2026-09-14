"""Result screenshots cover the whole page; comma lists keep bracketed commas."""
from __future__ import annotations

import pathlib
from typing import Any

from aaa.ui.wizard.listing import split_items
from scripts.wizard_fill.session import shoot


class _Page:
    """Records viewport changes and the capture, like a Playwright page would."""

    def __init__(self, content_height: int):
        self.viewport_size: dict[str, int] | None = {"width": 1440, "height": 1000}
        self.content_height = content_height
        self.calls: list[tuple[str, Any]] = []

    def evaluate(self, _script: str) -> int:
        """Return the content height."""
        return self.content_height

    def set_viewport_size(self, size: dict[str, int]) -> None:
        """Record a resize."""
        self.calls.append(("resize", dict(size)))
        self.viewport_size = dict(size)

    def wait_for_timeout(self, _ms: int) -> None:
        """No-op."""

    def screenshot(self, path: str, full_page: bool) -> None:
        """Record the capture at the current height."""
        self.calls.append(("shot", (full_page, self.viewport_size["height"] if self.viewport_size else 0)))
        pathlib.Path(path).write_bytes(b"png")


def test_a_tall_streamlit_page_is_captured_at_its_content_height(tmp_path: pathlib.Path) -> None:
    page = _Page(content_height=5400)
    shoot(page, tmp_path / "results.png")
    assert ("shot", (True, 5400)) in page.calls
    assert page.calls[-1] == ("resize", {"width": 1440, "height": 1000})


def test_a_short_page_is_not_resized_and_a_huge_one_is_capped(tmp_path: pathlib.Path) -> None:
    short = _Page(content_height=800)
    shoot(short, tmp_path / "a.png")
    assert ("shot", (True, 1000)) in short.calls
    huge = _Page(content_height=90000)
    shoot(huge, tmp_path / "b.png")
    assert ("shot", (True, 16000)) in huge.calls


def test_a_bracketed_comma_stays_inside_its_item() -> None:
    raw = ("ISO/IEC 42001:2023 (guidance, uncertified), ISO/IEC 23894:2023 "
           "(guidance, uncertified), Regulation (EU) 2016/679")
    assert split_items(raw) == ["ISO/IEC 42001:2023 (guidance, uncertified)",
                                "ISO/IEC 23894:2023 (guidance, uncertified)",
                                "Regulation (EU) 2016/679"]
    assert split_items(" a, ,b ") == ["a", "b"] and split_items("") == []


def test_the_snapshot_page_renders_the_wizard_dashboard_over_a_saved_state() -> None:
    """The tool renders step 4 itself, so an API run's page is the page a wizard run shows."""
    source = pathlib.Path("scripts/results_snapshot/page.py").read_text(encoding="utf-8")
    assert "render_step_4()" in source and "AAA_SNAPSHOT_STATE" in source
    from scripts.results_snapshot import capture

    assert capture.shoot is shoot
