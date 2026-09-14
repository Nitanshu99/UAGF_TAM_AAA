"""Bootstrap orchestration."""
from __future__ import annotations

from scripts.setup.cli import parse_args, print_next_steps
from scripts.setup.console import step
from scripts.setup.steps.env import check_python, copy_env, create_venv, install_requirements
from scripts.setup.steps.infra import alembic_migrate, docker_up, smoke_test


def main(argv: list[str] | None = None) -> int:
    """Run all bootstrap steps in order.

    :param argv: Optional argument list (defaults to ``sys.argv[1:]``).
    :returns: Process exit code.
    """
    args = parse_args(argv)
    total = 7

    step(1, total, "Verify Python version")
    check_python()

    step(2, total, "Create virtualenv")
    py = create_venv(skip=args.no_venv)

    step(3, total, "Install Python dependencies")
    install_requirements(py, with_prod=args.with_prod_deps)

    step(4, total, "Copy .env.example -> .env")
    copy_env()

    step(5, total, "Start docker compose stack")
    docker_up(skip=args.no_docker)

    step(6, total, "Apply alembic migrations")
    alembic_migrate(py, skip=args.no_migrate)

    step(7, total, "Run smoke test")
    smoke_test(py, skip=args.no_tests)

    print_next_steps()
    return 0
