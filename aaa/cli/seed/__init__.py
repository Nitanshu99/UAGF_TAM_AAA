"""Seeding a headless CLI run: client documents into the evidence store, then the intake itself."""
from __future__ import annotations

from aaa.cli.seed.documents import seed_client_documents

__all__ = ["seed_client_documents"]
