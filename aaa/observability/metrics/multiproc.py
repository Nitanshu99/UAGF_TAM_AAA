"""Prometheus multiprocess mode — one metrics view across every AAA process.

The pipeline runs in whichever process invoked it: uvicorn for API-driven
runs, Streamlit for the wizard, a bare interpreter for ``aaa.cli`` and
``scripts.run_mock_case``. Prometheus scrapes only the API's ``/metrics``, so
a counter incremented anywhere else was never seen by Grafana — after months
of runs the TSDB held no ``aaa_*`` series at all.

prometheus_client's multiprocess mode has every process write its values to
mmap files under ``PROMETHEUS_MULTIPROC_DIR``; the API merges that directory
on each scrape. The variable must be set before ``prometheus_client`` is
imported, which is why :mod:`aaa` sets it at package import and this module
only reads it. Under pytest it stays unset, so tests keep in-process values.
Only counters and histograms are registered, so no gauge mode is involved and
a file left behind by an exited process is exactly the total that should
survive it.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ENV_VAR = "PROMETHEUS_MULTIPROC_DIR"


def multiproc_dir() -> Path | None:
    """Return the shared metrics directory, or ``None`` in single-process mode.

    :returns: Directory named by ``PROMETHEUS_MULTIPROC_DIR``, or ``None``.
    :rtype: Path | None
    """
    configured = os.environ.get(ENV_VAR)
    return Path(configured) if configured else None


def build_registry(path: Path) -> Any:
    """Return a registry that merges every process's files under *path*.

    :param path: Directory holding the per-process ``*.db`` files.
    :type path: Path
    :returns: A fresh ``CollectorRegistry`` wired to a ``MultiProcessCollector``.
    :rtype: Any
    """
    from prometheus_client import CollectorRegistry, multiprocess

    # An explicitly configured directory (containers set the variable in their
    # environment, so the package bootstrap does not create it) must exist
    # before the collector globs it, or the very first scrape is a 500.
    path.mkdir(parents=True, exist_ok=True)
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry, path=str(path))
    return registry


def exposition_registry() -> Any:
    """Return the registry ``/metrics`` should render.

    :returns: The merged multiprocess registry when the shared directory is
        configured, otherwise this process's default registry.
    :rtype: Any
    """
    path = multiproc_dir()
    if path is None:
        from prometheus_client import REGISTRY

        return REGISTRY
    return build_registry(path)
