"""T-20260914-067/068: the bootstrap refuses a taken host port and lets a shell port reach its URLs."""
from __future__ import annotations

import socket
from pathlib import Path

import pytest

from scripts.bootstrap import environment
from scripts.bootstrap.steps import ports


def test_a_port_held_by_another_process_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """5432 held by a host Postgres is reported by its variable; the others pass."""
    monkeypatch.setattr(ports, "published_ports", set)
    monkeypatch.setattr(ports, "listening", lambda n: n == 5432)
    assert ports.busy_ports({}) == {"POSTGRES_PORT": 5432}
    assert ports.busy_ports({"POSTGRES_PORT": "15432"}) == {}


def test_a_port_this_project_publishes_is_its_own(monkeypatch: pytest.MonkeyPatch) -> None:
    """A re-run finds its own Postgres on the port and carries on."""
    monkeypatch.setattr(ports, "published_ports", lambda: {5432})
    monkeypatch.setattr(ports, "listening", lambda n: n == 5432)
    assert ports.busy_ports({}) == {}


def test_check_ports_exits_on_a_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ports, "busy_ports", lambda env: {"GRAFANA_PORT": 3002})
    with pytest.raises(SystemExit):
        ports.check_ports({})


def test_listening_sees_a_bound_socket() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        assert ports.listening(server.getsockname()[1]) is True


def test_an_exported_port_reaches_the_url_built_from_it(tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL follows POSTGRES_PORT from the shell, as docker compose does."""
    env_file = tmp_path / ".env"
    env_file.write_text("POSTGRES_PORT=5432\nDATABASE_URL=postgresql://a:b@localhost:${POSTGRES_PORT}/aaa\n"
                        "PLAIN=${MISSING:-fallback}\n", encoding="utf-8")
    # `import aaa` loads a real .env into os.environ; only the shell values this test sets count.
    for leaked in ("DATABASE_URL", "PLAIN", "MISSING"):
        monkeypatch.delenv(leaked, raising=False)
    monkeypatch.setenv("POSTGRES_PORT", "15433")
    env = environment.child_env(env_file)
    assert env["DATABASE_URL"] == "postgresql://a:b@localhost:15433/aaa"
    assert env["PLAIN"] == "fallback"
    monkeypatch.delenv("POSTGRES_PORT")
    assert environment.child_env(env_file)["DATABASE_URL"].endswith(":5432/aaa")
