"""Built-in KB passages — core high-risk articles (Art. 9/10/13)."""
from __future__ import annotations

from typing import Any

_KB_CORE: dict[str, list[dict[str, Any]]] = {
    "Art.9": [
        {
            "text": (
                "Article 9 EU AI Act — Risk Management System. Providers of high-risk "
                "AI systems shall establish, implement, document and maintain a risk "
                "management system that runs throughout the entire lifecycle."
            ),
            "source": "EU AI Act Art. 9 §1",
            "article": "Art.9",
            "score": 1.0,
        }
    ],
    "Art.10": [
        {
            "text": (
                "Article 10 EU AI Act — Data and Data Governance. Training, validation "
                "and testing data sets shall be subject to appropriate data governance "
                "and management practices. Data sets shall be relevant, sufficiently "
                "representative and, to the best extent possible, free of errors."
            ),
            "source": "EU AI Act Art. 10 §2",
            "article": "Art.10",
            "score": 1.0,
        }
    ],
    "Art.13": [
        {
            "text": (
                "Article 13 EU AI Act — Transparency and Provision of Information. "
                "High-risk AI systems shall be designed and developed in such a way "
                "to ensure that their operation is sufficiently transparent to enable "
                "deployers to interpret the system's output and use it appropriately."
            ),
            "source": "EU AI Act Art. 13 §1",
            "article": "Art.13",
            "score": 1.0,
        }
    ],
}
