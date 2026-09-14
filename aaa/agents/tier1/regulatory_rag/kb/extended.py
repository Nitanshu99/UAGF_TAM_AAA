"""Built-in KB passages — conformity, Annex III, and GPAI articles."""
from __future__ import annotations

from typing import Any

_KB_EXTENDED: dict[str, list[dict[str, Any]]] = {
    "Art.43": [
        {
            "text": (
                "Article 43 EU AI Act — Conformity Assessment. For high-risk AI systems "
                "listed in Annex III, point 1, the provider shall follow the conformity "
                "assessment procedure set out in Annex VII (third-party) or conduct "
                "internal control pursuant to Annex VI."
            ),
            "source": "EU AI Act Art. 43 §1",
            "article": "Art.43",
            "score": 1.0,
        }
    ],
    "Annex_III": [
        {
            "text": (
                "Annex III EU AI Act — High-Risk AI Systems. Includes biometric "
                "identification (§1), critical infrastructure (§2), education (§3), "
                "employment (§4), essential services (§5), law enforcement (§6), "
                "migration and border control (§7), administration of justice (§8)."
            ),
            "source": "EU AI Act Annex III",
            "article": "Annex_III",
            "score": 1.0,
        }
    ],
    "GPAI_51": [
        {
            "text": (
                "Article 51 EU AI Act — Classification of GPAI Models with Systemic Risk. "
                "A GPAI model shall be classified as a model with systemic risk if it has "
                "high impact capabilities evaluated on the basis of appropriate technical "
                "tools and methodologies, including indicators and benchmarks."
            ),
            "source": "EU AI Act Art. 51 §1",
            "article": "GPAI_51",
            "score": 1.0,
        }
    ],
}
