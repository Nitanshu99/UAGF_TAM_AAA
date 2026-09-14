"""Reading the prompt-injection probe's result, and the rate it reports."""
from __future__ import annotations


def _injection_result(injection: dict) -> str:
    """What the injection suite measured, or that it measured nothing."""
    rate = injection.get("vulnerability_rate")
    if rate is None:
        return ("no adversarial probing was performed"
                f" ({injection.get('not_tested_reason') or injection.get('method')})")
    return f"vulnerability_rate={rate}"
def _rate(golden_set: dict) -> str:
    """The pass rate as a sentence fragment, or why there is none."""
    rate = golden_set.get("pass_rate")
    return (f"{rate:.2f}" if rate is not None
            else "not scored (no system answers supplied)")


__all__ = ["_injection_result", "_rate"]
