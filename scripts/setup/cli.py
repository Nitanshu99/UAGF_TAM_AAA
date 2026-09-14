"""Argument parsing and the next-steps epilogue."""
from __future__ import annotations

import argparse
import os


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the bootstrap CLI arguments."""
    p = argparse.ArgumentParser(
        prog="python -m scripts.setup",
        description="One-shot environment bootstrap for the AAA repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--no-venv", action="store_true",
                   help="Reuse the current interpreter; do not create .venv/.")
    p.add_argument("--no-docker", action="store_true",
                   help="Skip 'docker compose up -d'.")
    p.add_argument("--no-migrate", action="store_true",
                   help="Skip 'alembic upgrade head'.")
    p.add_argument("--no-tests", action="store_true",
                   help="Skip the pytest smoke run.")
    p.add_argument("--with-prod-deps", action="store_true",
                   help="Install requirements.txt (runtime only) instead of "
                        "requirements-dev.txt (runtime + dev tooling).")
    return p.parse_args(argv)


def print_next_steps() -> None:
    """Print the post-setup quickstart commands."""
    activate = ". .venv/bin/activate" if os.name != "nt" else ".venv\\Scripts\\activate"
    print(
        "\n\033[1;32m✓ Setup complete.\033[0m\n\n"
        "Next steps:\n"
        f"  1. Activate the venv:   {activate}\n"
        "  2. Edit .env with real LLM API keys.\n"
        "  3. Start everything:     python -m aaa   (or: make start)\n"
        "  4. Run the fixture demo: make intake-demo\n"
        "  5. Read USER_MANUAL.md for the full guide.\n"
    )
