"""Structural checks on docker-compose.yml's optional `obs` profile.

Pure YAML assertions (no Docker required) so this runs in CI: guards against
someone editing docker-compose.yml and accidentally pulling the observability
stack into the default `docker compose up` service set, or breaking a
referenced config-file path.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
_COMPOSE = yaml.safe_load((_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
_SERVICES = _COMPOSE["services"]

_OBS_SERVICES = {"prometheus", "loki", "alloy", "grafana"}
_UI_SERVICES = {"pgweb", "redis-commander"}
_DEFAULT_SERVICES = {"postgres", "qdrant", "minio", "valkey", "langfuse", "openbao"}
_DEFAULT_PORT = re.compile(r"\$\{[A-Z_]+:-(\d+)}")


def _host_ports(service: str) -> list[str]:
    """Host ports as published with no override — ``${X_PORT:-3002}`` → ``3002``."""
    return [_DEFAULT_PORT.sub(lambda m: m.group(1), str(p)).rsplit(":", 1)[0].rsplit(":", 1)[-1]
            for p in _SERVICES[service]["ports"]]


def test_obs_services_are_profile_gated():
    """Every obs service declares profiles: [obs] so it never starts by default."""
    for name in _OBS_SERVICES:
        assert _SERVICES[name].get("profiles") == ["obs"], name


def test_ui_services_are_profile_gated():
    """pgweb and redis-commander only come up with --profile ui (the bootstrap)."""
    for name in _UI_SERVICES:
        assert _SERVICES[name].get("profiles") == ["ui"], name
        assert all(str(p).startswith("127.0.0.1:") for p in _SERVICES[name]["ports"]), name


def test_default_services_have_no_profile():
    """The original six services carry no profile — untouched default startup."""
    for name in _DEFAULT_SERVICES:
        assert "profiles" not in _SERVICES[name], name


def test_referenced_config_files_exist():
    """Every bind-mounted observability config file is present on disk."""
    for path in ("infra/observability/prometheus.yml",
                 "infra/observability/loki-config.yml",
                 "infra/observability/alloy-config.alloy",
                 "infra/observability/grafana/provisioning/datasources/datasources.yml",
                 "infra/observability/grafana/provisioning/dashboards/dashboards.yml",
                 "infra/observability/grafana/dashboards/aaa-overview.json",
                 "infra/observability/grafana/dashboards/aaa-logs.json"):
        assert (_ROOT / path).is_file(), path


def test_grafana_and_prometheus_ports_do_not_collide():
    """Grafana (3002) and Prometheus (127.0.0.1:9090) use distinct host ports by default."""
    assert _host_ports("grafana") == ["3002"]
    assert _host_ports("prometheus") == ["9090"]


def test_every_host_port_is_overridable_and_unique_by_default():
    """Two checkouts can run side by side from their own .env; defaults never collide."""
    seen: dict[str, str] = {}
    for name, service in _SERVICES.items():
        for spec in service.get("ports", []):
            assert _DEFAULT_PORT.search(str(spec)), f"{name}: {spec} has a hardcoded host port"
        for host_port in _host_ports(name) if "ports" in service else []:
            assert host_port not in seen, f"{name} and {seen[host_port]} both publish {host_port}"
            seen[host_port] = name
