"""The Art. 43 §1 decision for an Annex III point-1 system."""
from __future__ import annotations

from aaa.platform.state import Art43Decision


def _point_1_decision(harmonised: bool, elects_third_party: bool) -> Art43Decision:
    """Decide an Annex III point 1 (biometric) system under Art. 43 §1.

    :param harmonised: Whether Art. 40 harmonised standards were applied.
    :param elects_third_party: Whether the provider elected a notified body.
    :returns: The procedure with the sub-paragraph that produced it.
    """
    if not harmonised:
        return Art43Decision(
            procedure="annex_vii_notified_body",
            rationale=(
                "Annex III point 1 (biometrics). Harmonised standards under Art. 40 "
                "are not recorded as applied and no common specifications under "
                "Art. 41 are recorded, so the second subparagraph of Art. 43 §1 "
                "requires the Annex VII procedure with notified-body involvement."
            ),
        )
    if elects_third_party:
        return Art43Decision(
            procedure="annex_vii_notified_body",
            rationale=(
                "Annex III point 1 (biometrics) with harmonised standards applied "
                "under Art. 40. The provider has opted for the Annex VII procedure "
                "under Art. 43 §1(b)."
            ),
        )
    return Art43Decision(
        procedure="annex_vi_internal_control",
        rationale=(
            "Annex III point 1 (biometrics) with harmonised standards applied "
            "under Art. 40. The provider has opted for internal control based on "
            "Annex VI under Art. 43 §1(a)."
        ),
    )


__all__ = ["_point_1_decision"]
