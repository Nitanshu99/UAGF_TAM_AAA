"""Which EU AI Act articles a fairness result speaks to, as findings and as evidence."""
from __future__ import annotations

#: The articles a fairness finding *bears on*. Art. 10 §2(f) is the obligation to
#: examine datasets for possible biases; Art. 9 is the risk-management system that
#: examination feeds. Art. 15 §1 — which this list used to name — governs accuracy,
#: robustness and cybersecurity, and nothing else. The system's own Verifier caught
#: that (case 05 #017, graded critical/material): *"Art. 15§1 concerns accuracy,
#: robustness and cybersecurity only. Non-discrimination bias examination is
#: mandated by Art. 10§2(f) (and Art. 9 risk management)."*
FINDING_ARTICLES = ["Art.10§2(f)", "Art.9"]
#: The article this phase's artefacts are *contracted to evidence*, and therefore
#: the only one a Phase 4 evidence gap may hold back. The distinction matters:
#: a finding names every article it bears on, but Phase 4 was never contracted to
#: evidence the risk-management system — Phase 5 assesses Art. 9 through the CGSA
#: payload, and a fairness gap must not be able to disclaim an article another
#: phase evidenced.
EVIDENCED_ARTICLES = ["Art.10§2(f)"]


__all__ = ["EVIDENCED_ARTICLES", "FINDING_ARTICLES"]
