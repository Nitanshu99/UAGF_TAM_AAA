"""MinIO credentials: a scoped service account wins over the server root key."""
from __future__ import annotations

from aaa.settings.model import AAASettings


def _settings(monkeypatch, **env):
    """Build settings from *env* only (no .env file, no inherited MinIO vars)."""
    for name in ("MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return AAASettings(_env_file=None)  # pyright: ignore[reportCallIssue]


def test_service_account_takes_precedence(monkeypatch):
    """Both sets present → the scoped account is what the client uses."""
    cfg = _settings(monkeypatch, MINIO_ACCESS_KEY="aaa-evidence-rw", MINIO_SECRET_KEY="svc",
                    MINIO_ROOT_USER="root", MINIO_ROOT_PASSWORD="rootpw")
    assert (cfg.minio_access_key, cfg.minio_secret_key) == ("aaa-evidence-rw", "svc")


def test_root_credentials_remain_the_fallback(monkeypatch):
    """Only the root key configured (local dev) → still works unchanged."""
    cfg = _settings(monkeypatch, MINIO_ROOT_USER="root", MINIO_ROOT_PASSWORD="rootpw")
    assert (cfg.minio_access_key, cfg.minio_secret_key) == ("root", "rootpw")
