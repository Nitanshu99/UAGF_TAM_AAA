"""Steps 9–10: the app, then the browser that watches it."""
from __future__ import annotations

import argparse
import os

from scripts.bootstrap.environment import port
from scripts.bootstrap.orchestrate.common import PYTHON, TOTAL, Children
from scripts.bootstrap.orchestrate.summary import summary
from scripts.bootstrap.paths import CASE_DIR
from scripts.bootstrap.steps.app import start_api, start_ui, wait_http
from scripts.setup.console import ok, step


def serve_and_browse(args: argparse.Namespace, children: Children) -> None:
    """Start the API and the UI, print the summary, then hand over to the browser.

    :param args: The parsed command line.
    :param children: Where the API and UI processes are recorded.
    """
    from scripts.bootstrap.browser import browse

    env = dict(os.environ)
    api_port = port(env, "PLATFORM_PORT", 8000)
    ui_port = port(env, "STREAMLIT_SERVER_PORT", 8501)
    api_url, ui_url = f"http://localhost:{api_port}", f"http://localhost:{ui_port}"
    step(9, TOTAL, "FastAPI backend and Streamlit wizard")
    children["api"] = start_api(PYTHON, api_port)
    wait_http(f"{api_url}/healthz", children["api"])
    ok(f"API up at {api_url}")
    children["ui"] = start_ui(PYTHON, ui_port)
    wait_http(f"{ui_url}/_stcore/health", children["ui"])
    ok(f"UI up at {ui_url}")
    step(10, TOTAL, "Browser: every service dashboard in a tab, the wizard in front")
    summary(env, args, ui_url, api_url)
    browse(args, env, ui_url, CASE_DIR)


__all__ = ["serve_and_browse"]
