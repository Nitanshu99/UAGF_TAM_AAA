"""Host ports the stack and the app bind, checked before Docker is asked to bind them.

On a machine that already ran a Postgres on 5432, ``docker compose up`` published the
stack's Postgres anyway and the app reached the host server instead — migrations failed
on ``role "aaa" does not exist`` with nothing pointing at the port (fresh-clone rehearsal,
2026-09-14, T-20260914-067). A port this project already publishes is its own and passes,
so a re-run is unaffected.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
from typing import Mapping

from scripts.bootstrap.environment import port
from scripts.bootstrap.steps.docker import compose
from scripts.setup.console import err, ok

#: Variable → default, as docker-compose.yml and the bootstrap's API/UI read them.
HOST_PORTS = {"POSTGRES_PORT": 5432, "QDRANT_PORT": 6333, "QDRANT_GRPC_PORT": 6334,
              "MINIO_PORT": 9000, "MINIO_CONSOLE_PORT": 9001, "VALKEY_PORT": 6379,
              "LANGFUSE_PORT": 3003, "OPENBAO_PORT": 8200, "PROMETHEUS_PORT": 9090,
              "ALLOY_PORT": 12345, "GRAFANA_PORT": 3002, "PGWEB_PORT": 8081,
              "REDIS_COMMANDER_PORT": 8082, "PLATFORM_PORT": 8000,
              "STREAMLIT_SERVER_PORT": 8501}


def published_ports() -> set[int]:
    """Host ports this compose project's containers already publish."""
    out = subprocess.run(compose("ps", "--format", "json"), capture_output=True,
                         text=True, check=False).stdout
    rows = [json.loads(line) for line in out.splitlines() if line.strip().startswith("{")]
    return {int(p["PublishedPort"]) for row in rows for p in (row.get("Publishers") or [])
            if p.get("PublishedPort")}


def listening(number: int) -> bool:
    """Whether anything accepts connections on *number* at localhost (IPv4 or IPv6)."""
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            if sock.connect_ex((host, number)) == 0:
                return True
    return False


def busy_ports(env: Mapping[str, str]) -> dict[str, int]:
    """Variable → port for every port another process holds.

    :param env: The environment the stack is started with.
    """
    own = published_ports()
    return {key: number for key, default in HOST_PORTS.items()
            if (number := port(dict(env), key, default)) not in own and listening(number)}


def check_ports(env: Mapping[str, str]) -> None:
    """Exit naming each port variable to change, or confirm every port is free."""
    busy = busy_ports(env)
    if not busy:
        ok(f"host ports free: {len(HOST_PORTS)} checked")
        return
    for key, number in busy.items():
        err(f"port {number} ({key}) is already in use by another process — set {key} to a "
            "free port in .env and re-run")
    sys.exit(1)


__all__ = ["HOST_PORTS", "busy_ports", "check_ports", "listening", "published_ports"]
