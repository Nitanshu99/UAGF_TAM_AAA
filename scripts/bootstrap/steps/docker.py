"""Step 6: the Docker stack — core services plus the ``obs`` and ``ui`` profiles."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.setup.console import err, ok, warn
from scripts.setup.shell import run

#: Started together: the core services carry no profile, so they come too.
PROFILES = ("obs", "ui")


def compose(*args: str) -> list[str]:
    """``docker compose`` with every bootstrap profile selected."""
    cmd = ["docker", "compose"]
    for profile in PROFILES:
        cmd += ["--profile", profile]
    return cmd + list(args)


def stack_up(wait_timeout: int) -> None:
    """Start everything and wait until each container reports healthy.

    ``--wait`` blocks on the health checks (Langfuse's takes about a minute on
    first start), so what follows can rely on Postgres, Qdrant and MinIO
    answering rather than probing them itself.

    :param wait_timeout: Seconds before Compose gives up.
    """
    code = run(compose("up", "-d", "--wait", "--wait-timeout", str(wait_timeout)),
               check=False)
    if code != 0:
        subprocess.run(compose("ps"), check=False)
        err("the Docker stack did not come up healthy; see `docker compose ps` above and "
            "`docker compose logs <service>`")
        sys.exit(1)
    ok("stack healthy: postgres, qdrant, minio, valkey, clickhouse, langfuse, openbao, "
       "prometheus, loki, alloy, grafana, pgweb, redis-commander")


def migrate(python: Path) -> None:
    """Apply the Alembic migrations (the checkpointer tables and the app schema)."""
    code = run([str(python), "-m", "alembic", "upgrade", "head"], check=False)
    if code != 0:
        warn("alembic upgrade failed; the API still starts (checkpoints degrade to memory)")
    else:
        ok("database migrations applied")
