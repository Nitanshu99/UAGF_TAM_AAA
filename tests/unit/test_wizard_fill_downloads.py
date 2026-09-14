"""The dashboard's downloads must land under their real names.

Playwright puts a download in a temporary artifacts directory, names it with a
GUID and no extension, and deletes it when the browser context closes. Driving
the wizard without listening for the ``download`` event therefore produced
exactly what a user reported: the audit report, the conformity report and the
HITL packet all arrived as unopenable hash-named files that were nowhere in
Downloads, and were gone once the browser exited.

The app's own ``st.download_button(file_name=...)`` was correct throughout —
``<eid>_audit_report.pdf``, ``<eid>_hitl_review.json``. Nothing was listening.
"""
from __future__ import annotations

from pathlib import Path

from scripts.wizard_fill.__main__ import _capture_downloads


class _Download:
    """Playwright download stub."""

    def __init__(self, name: str, fail: bool = False) -> None:
        self.suggested_filename = name
        self.saved_to: Path | None = None
        self._fail = fail

    def save_as(self, target: str | Path) -> None:
        """Record where the driver asked for the file to go."""
        if self._fail:
            raise OSError("disk full")
        self.saved_to = Path(target)
        Path(target).write_bytes(b"x")


class _Page:
    """Page stub capturing the registered handler."""

    def __init__(self) -> None:
        self.handlers: dict = {}

    def on(self, event: str, handler) -> None:
        """Register *handler* for *event*."""
        self.handlers[event] = handler


def test_a_download_is_saved_under_its_suggested_name(tmp_path: Path) -> None:
    """The exact regression: real name, real extension, real directory."""
    page = _Page()
    _capture_downloads(page, tmp_path / "downloads")
    download = _Download("eng-mariposa-edu-gmbh-d59885_audit_report.pdf")
    page.handlers["download"](download)
    assert download.saved_to is not None
    assert download.saved_to.name == "eng-mariposa-edu-gmbh-d59885_audit_report.pdf"
    assert download.saved_to.suffix == ".pdf"
    assert download.saved_to.is_file()


def test_the_handler_is_registered_for_the_download_event() -> None:
    """Without this listener Playwright discards the file on exit."""
    page = _Page()
    _capture_downloads(page, Path("downloads"))
    assert "download" in page.handlers


def test_the_folder_is_created_on_first_download(tmp_path: Path) -> None:
    """A directory that does not exist yet must not lose the file."""
    folder = tmp_path / "not" / "there" / "yet"
    page = _Page()
    _capture_downloads(page, folder)
    page.handlers["download"](_Download("eng-x_hitl_review.json"))
    assert (folder / "eng-x_hitl_review.json").is_file()


def test_a_failed_save_does_not_break_the_page(tmp_path: Path) -> None:
    """One unwritable file must not take the dashboard down with it."""
    page = _Page()
    _capture_downloads(page, tmp_path)
    page.handlers["download"](_Download("eng-x_T18.json", fail=True))  # must not raise


def test_every_app_download_button_names_a_file_with_an_extension() -> None:
    """Guards the other half: the app must keep supplying a real filename."""
    import re

    for source in ("aaa/ui/wizard/step4/deliverables.py",
                   "aaa/ui/admin/artefacts.py", "aaa/ui/admin/hitl.py"):
        text = Path(source).read_text("utf-8")
        for name in re.findall(r'file_name=f?"([^"]+)"', text):
            assert "." in name.rsplit("/", 1)[-1], f"{source}: {name!r} has no extension"
