"""aaa — Autonomous AI Auditor package.

Loads the repo-root ``.env`` into ``os.environ`` at import time so flags that are
read directly via ``os.environ`` (rather than pydantic-settings) —
``AAA_DISABLE_FLEX``, ``CGSA_FIXTURE_DIR``, the LiteLLM provider keys, … — can be
configured from ``.env`` for *every* entrypoint (CLI, API, Streamlit, scripts),
not only the ones that call ``load_dotenv`` themselves.

Uses the shared :func:`aaa.platform.env_bootstrap.load_repo_dotenv`, which keeps
existing env values winning (``override=False``) and is a no-op under pytest, so the
test environment stays hermetic.
"""
from __future__ import annotations


def _bootstrap_dotenv() -> None:
    from pathlib import Path

    try:
        from aaa.platform.env_bootstrap import load_repo_dotenv
        load_repo_dotenv(Path(__file__).resolve().parent.parent)
    except Exception:  # noqa: BLE001 - env bootstrap must never break imports
        pass


def _bootstrap_metrics_dir() -> None:
    """Choose the shared Prometheus directory before ``prometheus_client`` loads.

    prometheus_client decides between in-process and multiprocess values when it
    is first imported, from ``PROMETHEUS_MULTIPROC_DIR``. Setting it here, ahead
    of every other import in the package, is what lets the API's ``/metrics``
    show counters incremented by the Streamlit wizard, ``aaa.cli`` and the
    mock-case runner. Left unset under pytest so tests keep private values.
    """
    import os
    import sys
    from pathlib import Path

    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        return
    if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST"):
        return
    try:
        log_dir = os.environ.get("AAA_LOG_DIR") or Path(__file__).resolve().parent.parent / "logs"
        path = Path(log_dir) / "metrics"
        path.mkdir(parents=True, exist_ok=True)
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(path)
    except OSError:  # an unwritable log dir must never break imports
        pass


_bootstrap_dotenv()
_bootstrap_metrics_dir()
