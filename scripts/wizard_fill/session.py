"""What happens around the form: downloads, the wait for results, holding open.

Shared by the ``wizard_fill`` command and the bootstrap's browser session, so
the two drivers cannot drift on how a download is saved or when a run is
judged finished.
"""
from __future__ import annotations

import pathlib
import time
from typing import Any

# The results wait lives in its own module; re-exported for the two drivers.
from scripts.wizard_fill.watch import RESULT_MARKERS, watch  # noqa: F401


def capture_downloads(page: Any, folder: pathlib.Path) -> None:
    """Save what the dashboard's download buttons produce, under real names.

    Playwright puts a download in a temporary artifacts directory, names it with
    a GUID and no extension, and deletes it when the browser context closes. So
    the report, the conformity PDF and the HITL packet all downloaded as
    unopenable hash-named files that were nowhere in Downloads — and vanished
    on exit. The app's own ``file_name=`` was right all along; nothing was
    listening for the download.

    :param page: The page to watch.
    :param folder: Directory to save into; created on first download.
    """
    def _save(download: Any) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / download.suggested_filename
        try:
            download.save_as(target)
            print(f"  downloaded -> {target}", flush=True)
        except Exception as exc:  # noqa: BLE001 — a failed save must not stop the page
            print(f"  download of {download.suggested_filename!r} failed: {exc}",
                  flush=True)

    page.on("download", _save)


#: The tallest scrolling element's content height. Streamlit scrolls inside its own
#: container, not the document, so the page itself is never taller than the window.
_CONTENT_HEIGHT_JS = """() => Math.max(document.documentElement.scrollHeight,
  ...Array.from(document.querySelectorAll('*'), el => el.scrollHeight))"""
#: Chromium refuses a capture much taller than this.
_MAX_HEIGHT = 16000


def shoot(page: Any, target: pathlib.Path) -> None:
    """Save a screenshot of the whole page, reporting rather than raising on failure.

    ``full_page=True`` alone captured only the 1000-pixel window: a Streamlit page
    scrolls inside its app container, so the document never grows. The window is
    stretched to the content's height for the capture and restored afterwards.

    :param page: The page to capture.
    :param target: Where to write the PNG.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    size = page.viewport_size or {"width": 1440, "height": 1000}
    try:
        height = min(int(page.evaluate(_CONTENT_HEIGHT_JS)), _MAX_HEIGHT)
        if height > size["height"]:
            page.set_viewport_size({"width": size["width"], "height": height})
            page.wait_for_timeout(1500)  # let the app re-lay out at the new height
        page.screenshot(path=str(target), full_page=True)
        print(f"  screenshot -> {target} ({size['width']}x{max(height, size['height'])})", flush=True)
    except Exception as exc:  # noqa: BLE001 — a missed screenshot is not a failed run
        print(f"  screenshot failed ({type(exc).__name__}: {exc})", flush=True)
    finally:
        try:
            page.set_viewport_size(size)
        except Exception:  # noqa: BLE001 — the window may already be gone
            pass


def hold_open(page: Any, stop_hint: str = "pkill -f scripts.wizard_fill") -> bool:
    """Keep the browser and its session alive so the dashboard can be used.

    Playwright tears the browser down when this process exits, and the wizard's
    results live in that tab's Streamlit session — closing it ends the session
    and the dashboard with it. So the process parks here instead, and the
    dashboard stays interactive until it is killed or the window is closed.

    The wait is a plain ``time.sleep``, not ``page.wait_for_timeout``: an
    interrupt that lands inside a Playwright call leaves the driver's event loop
    unusable, and every later call — ``browser.close()`` included — blocks for
    good. The short ``page.title()`` between sleeps is what notices a window
    closed by hand and what drains queued events such as downloads.

    :param page: The page showing the dashboard.
    :param stop_hint: The command the operator can use to end the session.
    :returns: ``True`` when stopped by Ctrl-C or SIGTERM — the caller must then
        make no further Playwright call and simply exit, which closes the
        driver and the browser with it; ``False`` when the window was closed.
    """
    print("\n  Browser left open — the dashboard is live and interactive.", flush=True)
    print("  Downloads are saved with their real names under ./downloads/", flush=True)
    print(f"  Stop it with Ctrl-C, or:  {stop_hint}", flush=True)
    try:
        while True:
            time.sleep(2)
            page.title()  # raises once the browser is gone
    except KeyboardInterrupt:
        print("  interrupted; closing.", flush=True)
        return True
    except Exception as exc:  # noqa: BLE001 — the window was closed by hand
        print(f"  browser closed ({type(exc).__name__}); exiting.", flush=True)
        return False
