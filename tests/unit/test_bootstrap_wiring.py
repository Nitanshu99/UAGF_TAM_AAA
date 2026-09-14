"""Tabs, ports and the dependency fingerprint — the bootstrap's small pure parts."""
from __future__ import annotations

from pathlib import Path

from scripts.bootstrap.browser.tabs import service_tabs
from scripts.bootstrap.environment import child_env, port
from scripts.bootstrap.venv_stage import DEPENDENCY_FILES, dependency_fingerprint


def test_every_listed_service_gets_a_tab_on_its_default_port() -> None:
    urls = {t.name.split(" ·")[0]: t.url for t in service_tabs({})}
    assert urls["Grafana"] == "http://localhost:3002/d/aaa-overview?orgId=1&refresh=30s"
    assert urls["Loki"].startswith("http://localhost:3002/d/aaa-logs")
    assert urls["Prometheus"] == "http://127.0.0.1:9090/targets"
    assert urls["Alloy"] == "http://127.0.0.1:12345/"
    assert urls["Langfuse"] == "http://localhost:3003/auth/sign-in"
    assert urls["Qdrant"] == "http://localhost:6333/dashboard"
    assert urls["Postgres"] == "http://127.0.0.1:8081/"
    assert urls["MinIO"] == "http://localhost:9001/browser"
    assert urls["Valkey"] == "http://127.0.0.1:8082/"
    assert urls["API"] == "http://localhost:8000/docs"


def test_tabs_follow_the_port_overrides() -> None:
    env = {"GRAFANA_PORT": "13002", "QDRANT_URL": "http://localhost:16333/",
           "LANGFUSE_HOST": "http://localhost:13003", "PLATFORM_PORT": "18000"}
    urls = {t.name.split(" ·")[0]: t.url for t in service_tabs(env)}
    assert urls["Grafana"].startswith("http://localhost:13002/")
    assert urls["Qdrant"] == "http://localhost:16333/dashboard"
    assert urls["Langfuse"] == "http://localhost:13003/auth/sign-in"
    assert urls["API"] == "http://localhost:18000/docs"


def test_port_tolerates_blanks_and_junk() -> None:
    assert port({"X": ""}, "X", 7) == 7
    assert port({"X": " 12 "}, "X", 7) == 12
    assert port({}, "X", 7) == 7


def test_child_env_prefers_shell_then_env_file_then_overrides(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("A=file\nB=file\nPOSTGRES_PORT=5\nURL=pg://h:${POSTGRES_PORT}/db\n")
    # The shell now wins inside ${VAR} too (T-20260914-068); a value another test left
    # in os.environ must not stand in for the file's.
    for leaked in ("A", "C", "POSTGRES_PORT", "URL"):
        monkeypatch.delenv(leaked, raising=False)
    monkeypatch.setenv("B", "shell")
    env = child_env(env_file, {"B": "override", "C": "override"})
    assert (env["A"], env["B"], env["C"]) == ("file", "override", "override")
    assert env["URL"] == "pg://h:5/db"
    assert env["PYTHONUNBUFFERED"] == "1"


def test_fingerprint_changes_with_any_dependency_file(tmp_path: Path) -> None:
    for name in DEPENDENCY_FILES:
        (tmp_path / name).write_text("x")
    before = dependency_fingerprint(tmp_path)
    (tmp_path / "constraints.txt").write_text("y")
    assert dependency_fingerprint(tmp_path) != before
