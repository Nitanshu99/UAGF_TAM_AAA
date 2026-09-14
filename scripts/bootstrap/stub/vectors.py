"""Deterministic stand-in vectors: same text, same vector, every run."""
from __future__ import annotations

import hashlib
import math
import random

#: Width of ``text-embedding-3-large``, so collections built against the stub
#: have the real shape.
DIM = 3072


def vector(text: str, dim: int = DIM) -> list[float]:
    """A unit vector seeded by the SHA-256 of *text*.

    :param text: The input the vector stands for.
    :param dim: Vector width.
    :returns: ``dim`` floats of unit length.
    """
    rng = random.Random(hashlib.sha256(text.encode("utf-8")).digest())  # noqa: S311 - not security
    raw = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [round(x / norm, 6) for x in raw]
