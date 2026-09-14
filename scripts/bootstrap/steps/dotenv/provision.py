"""Secrets a fresh ``.env`` needs generated: Langfuse keys, login and server secrets."""
from __future__ import annotations

import secrets
import uuid


def langfuse_provisioning() -> dict[str, str]:
    """Fresh Langfuse project keys, login and server secrets for a new ``.env``.

    :returns: The six Langfuse values, each generated once per bootstrap.
    """
    return {
        "LANGFUSE_PUBLIC_KEY": f"pk-lf-{uuid.uuid4()}",
        "LANGFUSE_SECRET_KEY": f"sk-lf-{uuid.uuid4()}",
        "LANGFUSE_INIT_USER_PASSWORD": secrets.token_urlsafe(12),
        "LANGFUSE_ENCRYPTION_KEY": secrets.token_hex(32),
        "LANGFUSE_NEXTAUTH_SECRET": secrets.token_hex(24),
        "LANGFUSE_SALT": secrets.token_hex(16),
    }


__all__ = ["langfuse_provisioning"]
