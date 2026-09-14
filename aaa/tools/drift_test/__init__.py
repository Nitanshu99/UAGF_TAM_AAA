"""drift_test — training-vs-evaluation distribution drift (PSI), Art. 10 §2(g)."""
from aaa.tools.drift_test.core import drift_test  # noqa: F401
from aaa.tools.drift_test.psi import MODERATE, STABLE, band  # noqa: F401

__all__ = ["drift_test", "band", "STABLE", "MODERATE"]
