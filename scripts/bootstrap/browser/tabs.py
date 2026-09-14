"""The dashboards, one tab each, addressed from the ports in ``.env``."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from scripts.bootstrap.browser.login import sign_in_langfuse
from scripts.bootstrap.environment import port


@dataclass(frozen=True)
class Tab:
    """One dashboard tab: what it is, where it is, what the operator must know.

    ``after`` runs in the tab once it has loaded (Langfuse's form sign-in) and
    returns the note to print instead of ``note``.
    """

    name: str
    url: str
    note: str = ""
    after: Callable[[Any, dict[str, str]], str] | None = None


def service_tabs(env: dict[str, str]) -> list[Tab]:
    """Every service view, in the order the tabs are opened.

    Loki has no UI of its own, so its tab is the provisioned Grafana logs
    dashboard; Postgres and Valkey get pgweb and redis-commander from the
    ``ui`` compose profile. Grafana and MinIO are signed in before the tabs
    open (:func:`scripts.bootstrap.browser.pre_sign_in`), Langfuse in its tab.

    :param env: Environment mapping holding the ``*_PORT`` overrides.
    :returns: Tabs left to right.
    """
    grafana = f"http://localhost:{port(env, 'GRAFANA_PORT', 3002)}"
    langfuse = (env.get("LANGFUSE_HOST") or f"http://localhost:{port(env, 'LANGFUSE_PORT', 3003)}")
    qdrant = env.get("QDRANT_URL") or f"http://localhost:{port(env, 'QDRANT_PORT', 6333)}"
    return [
        Tab("Grafana · pipeline overview", f"{grafana}/d/aaa-overview?orgId=1&refresh=30s"),
        Tab("Loki · logs (Grafana dashboard)", f"{grafana}/d/aaa-logs?orgId=1&refresh=30s"),
        Tab("Prometheus · targets", f"http://127.0.0.1:{port(env, 'PROMETHEUS_PORT', 9090)}/targets"),
        Tab("Alloy · log pipeline", f"http://127.0.0.1:{port(env, 'ALLOY_PORT', 12345)}/"),
        Tab("Langfuse · LLM traces", f"{langfuse.rstrip('/')}/auth/sign-in",
            note="sign in with LANGFUSE_INIT_USER_EMAIL / LANGFUSE_INIT_USER_PASSWORD from .env",
            after=sign_in_langfuse),
        Tab("Qdrant · collections", f"{qdrant.rstrip('/')}/dashboard"),
        Tab("Postgres · pgweb", f"http://127.0.0.1:{port(env, 'PGWEB_PORT', 8081)}/"),
        Tab("MinIO · console", f"http://localhost:{port(env, 'MINIO_CONSOLE_PORT', 9001)}/browser",
            note="signed in as MINIO_ROOT_USER from .env"),
        Tab("Valkey · redis-commander",
            f"http://127.0.0.1:{port(env, 'REDIS_COMMANDER_PORT', 8082)}/"),
        Tab("API · Swagger", f"http://localhost:{port(env, 'PLATFORM_PORT', 8000)}/docs"),
    ]
