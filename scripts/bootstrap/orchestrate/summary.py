"""The closing summary: where everything is, and the logins the tabs were signed in with."""
from __future__ import annotations

import argparse

from scripts.bootstrap.paths import LOG_DIR


def summary(env: dict[str, str], args: argparse.Namespace, ui_url: str, api_url: str) -> None:
    """Print the URLs, credentials and output locations for this run.

    :param env: The environment the children were started with.
    :param args: The parsed command line (downloads and screenshot directories).
    :param ui_url: Where the wizard is served.
    :param api_url: Where the API is served.
    """
    print(f"\n  wizard        {ui_url}\n  API           {api_url}/docs")
    print(f"  Langfuse      {env.get('LANGFUSE_INIT_USER_EMAIL') or '(no login configured)'}"
          f" / {env.get('LANGFUSE_INIT_USER_PASSWORD') or '(blank)'}   (also in .env)")
    print(f"  MinIO console {env.get('MINIO_ROOT_USER')} / {env.get('MINIO_ROOT_PASSWORD')}")
    print(f"  Grafana       anonymous viewer; admin / {env.get('GF_SECURITY_ADMIN_PASSWORD')}")
    print(f"  downloads     {args.downloads}\n  logs          {LOG_DIR}/")
    if args.screenshots:
        print(f"  screenshots   {args.screenshots}")


__all__ = ["summary"]
