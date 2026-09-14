"""The API calls a mock-case run makes, in the order the wizard would make them."""
from __future__ import annotations

import logging
import sys
from typing import Any


def configure_logging() -> None:
    """Surface phase-level progress logs (start/complete + timing).

    It is then obvious which phase the ``/run`` endpoint is waiting on. The
    TestClient does not run the app lifespan, so stdout logging is set up here.
    """
    logging.getLogger().setLevel(logging.INFO)
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s %(name)s: %(message)s")


def create_engagement(client: Any, eid: str, stage_a: dict) -> None:
    """Register the engagement from the case's Stage A declaration.

    :param client: A FastAPI ``TestClient`` bound to the app.
    :param eid: Engagement identifier.
    :param stage_a: The Stage A declaration.
    """
    client.post("/api/v1/engagements", json={
        "engagement_id": eid,
        "provider_name": stage_a.get("provider_name", "Unknown"),
        "system_name": stage_a.get("system_name", "Unknown"),
        "declared_risk_tier": stage_a.get("declared_risk_tier", "high"),
    })


def submit_intake(client: Any, case: str, eid: str, stage_a: dict, stage_b: dict) -> bool:
    """Submit Stage A and Stage B; report a rejected intake on stderr.

    :returns: ``True`` when the intake was accepted.
    """
    intake = client.post(f"/api/v1/engagements/{eid}/intake",
                         json={"stage_a": stage_a, "stage_b": stage_b, "stage_c": None})
    if intake.status_code != 200:
        print(f"{case}: INTAKE FAILED — {intake.json()}", file=sys.stderr)
        return False
    return True


def dispatch_run(client: Any, case: str, eid: str) -> bool:
    """Run the audit pipeline synchronously through ``/run``.

    :returns: ``True`` when the run endpoint answered 200.
    """
    print("\nrunning audit pipeline — watch the per-phase progress logs below…")
    run = client.post(f"/api/v1/engagements/{eid}/run")
    if run.status_code != 200:
        print(f"{case}: RUN FAILED — {run.text[:300]}", file=sys.stderr)
        return False
    return True


__all__ = ["configure_logging", "create_engagement", "dispatch_run", "submit_intake"]
