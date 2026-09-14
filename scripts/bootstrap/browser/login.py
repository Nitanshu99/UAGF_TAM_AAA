"""Sign the browser into the stack's own services, with the credentials from ``.env``.

Every login here is to a container the bootstrap started, with a password the
bootstrap wrote or ``.env.example`` ships. Two services take a JSON login on
the same cookie jar the tabs use (``context.request`` shares it); Langfuse's
NextAuth form is filled in its own tab instead.
"""
from __future__ import annotations

from typing import Any


def sign_in_minio(context: Any, console_url: str, user: str, password: str) -> bool:
    """MinIO console: ``POST /api/v1/login`` sets the ``token`` cookie."""
    try:
        reply = context.request.post(f"{console_url}/api/v1/login",
                                     data={"accessKey": user, "secretKey": password})
        return bool(reply.ok)
    except Exception:  # noqa: BLE001 - a failed login leaves the login page, nothing worse
        return False


def sign_in_grafana(context: Any, url: str, password: str) -> bool:
    """Grafana: ``POST /login`` as admin sets ``grafana_session`` (Explore needs it)."""
    try:
        reply = context.request.post(f"{url}/login", data={"user": "admin", "password": password})
        return bool(reply.ok)
    except Exception:  # noqa: BLE001
        return False


def sign_in_langfuse(page: Any, env: dict[str, str]) -> str:
    """Fill Langfuse's sign-in form and land on the project's sessions list.

    :param page: The Langfuse tab, already on ``/auth/sign-in``.
    :param env: Environment holding ``LANGFUSE_INIT_USER_EMAIL`` / ``_PASSWORD``.
    :returns: A one-line note for the tab listing.
    """
    email = env.get("LANGFUSE_INIT_USER_EMAIL") or ""
    password = env.get("LANGFUSE_INIT_USER_PASSWORD") or ""
    if not (email and password):
        return "no LANGFUSE_INIT_USER_EMAIL / _PASSWORD in .env — sign in by hand"
    try:
        # By input type, not label: the password label wraps a "forgot password?"
        # link, which makes a label lookup ambiguous under strict mode.
        page.locator('input[type="email"], input[name="email"]').first.fill(email)
        page.locator('input[type="password"]').first.fill(password)
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.wait_for_url(lambda url: "/auth/sign-in" not in url, timeout=20_000)
        project = env.get("LANGFUSE_INIT_PROJECT_ID") or "aaa-audit"
        page.goto(f"{page.url.split('/', 3)[0]}//{page.url.split('/', 3)[2]}"
                  f"/project/{project}/sessions", wait_until="domcontentloaded", timeout=30_000)
        return f"signed in as {email}; one session per engagement"
    except Exception as exc:  # noqa: BLE001 - the sign-in page is still there
        return f"auto sign-in failed ({type(exc).__name__}); sign in as {email} (password in .env)"
