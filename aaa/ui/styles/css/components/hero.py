"""The hero surface."""
from __future__ import annotations

HERO = """
.aaa-hero { background: linear-gradient(150deg in oklab, var(--ink), oklch(0.30 0.075 278));
  color: var(--on-ink); border-radius: var(--r-xl); padding: 2.2rem 2.3rem;
  position: relative; overflow: clip; isolation: isolate; }
.aaa-hero::after { content: ""; position: absolute; inset-block-start: -40%;
  inset-inline-end: -12%; inline-size: 26rem; aspect-ratio: 1; border-radius: 50%;
  background: radial-gradient(circle, color-mix(in oklab, var(--brand) 60%, transparent), transparent 68%);
  z-index: -1; }
.aaa-hero h1, .aaa-hero .aaa-hero-title { color: #fff; margin: 0.35rem 0 0.6rem;
  font-size: clamp(1.75rem, 1.2rem + 1.7vw, 2.5rem); line-height: 1.1;
  letter-spacing: -0.024em; font-weight: 660; text-wrap: balance; }
.aaa-hero p, .aaa-hero .aaa-hero-sub { color: color-mix(in oklab, var(--on-ink) 78%, transparent);
  max-width: 52ch; margin: 0; font-size: 1rem; line-height: 1.6; }
.aaa-hero .aaa-eyebrow { color: color-mix(in oklab, var(--brand-line) 85%, white); }
.aaa-hero-meta { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-block-start: 1.2rem; }
.aaa-hero-chip { font-size: 0.76rem; font-weight: 560; padding: 0.28rem 0.7rem;
  border-radius: var(--r-pill); background: color-mix(in oklab, white 14%, transparent);
  border: 1px solid color-mix(in oklab, white 18%, transparent); color: var(--on-ink); }
"""

__all__ = ["HERO"]
