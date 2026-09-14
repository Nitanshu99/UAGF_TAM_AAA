"""The kpi surface."""
from __future__ import annotations

KPI = """
.aaa-kpi { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
  padding: 1.05rem 1.15rem; box-shadow: var(--shadow-1); block-size: 100%;
  display: grid; gap: 0.3rem; align-content: start;
  transition: box-shadow var(--dur-2) var(--ease), translate var(--dur-2) var(--ease); }
.aaa-kpi:hover { box-shadow: var(--shadow-2); translate: 0 -2px; }
.aaa-kpi .label { font-size: 0.74rem; font-weight: 600; letter-spacing: 0.055em;
  text-transform: uppercase; color: var(--text-3); text-wrap: balance; }
.aaa-kpi .value { font-size: clamp(1.7rem, 1.4rem + 0.8vw, 2.1rem); font-weight: 660;
  color: var(--text); line-height: 1.05; letter-spacing: -0.028em;
  font-variant-numeric: tabular-nums; }
.aaa-kpi .value .unit { font-size: 0.55em; font-weight: 560; color: var(--text-3);
  margin-inline-start: 0.12em; }
.aaa-kpi .foot { font-size: 0.8rem; color: var(--text-2); }
.aaa-meter { block-size: 0.3rem; border-radius: var(--r-pill); background: var(--surface-3);
  overflow: clip; margin-block-start: 0.15rem; }
.aaa-meter > i { display: block; block-size: 100%; border-radius: inherit; background: var(--brand);
  animation: aaa-sweep var(--dur-3) var(--ease) backwards; transform-origin: left center;
  animation-delay: 0.2s; --anim-reduced: none; }
.aaa-meter > i.is-ok { background: var(--ok); }
.aaa-meter > i.is-warn { background: var(--warn); }
.aaa-meter > i.is-bad { background: var(--bad); }
"""

__all__ = ["KPI"]
