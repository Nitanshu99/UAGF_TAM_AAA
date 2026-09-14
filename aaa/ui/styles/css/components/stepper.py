"""The stepper surface."""
from __future__ import annotations

STEPPER = """
.aaa-stepper { list-style: none; margin: 0 0 2.1rem; padding: 0; display: grid;
  grid-auto-flow: column; grid-auto-columns: 1fr; position: relative; }
.aaa-step-rail { position: absolute; inset-inline: 6%; inset-block-start: 0.72rem;
  block-size: 2px; background: var(--line); border-radius: var(--r-pill); }
.aaa-stepper { --steps: 5; }
.aaa-step-rail { inset-inline: calc(50% / var(--steps)); }
.aaa-step-rail-fill { block-size: 100%; background: var(--brand); border-radius: inherit;
  transition: inline-size var(--dur-3) var(--ease); }
.aaa-step-node { display: grid; justify-items: center; gap: 0.5rem; position: relative;
  text-align: center; padding-inline: 0.3rem; }
.aaa-step-dot { inline-size: 1.5rem; block-size: 1.5rem; border-radius: 50%;
  display: grid; place-items: center; font-size: 0.72rem; font-weight: 700;
  background: var(--canvas); border: 2px solid var(--line-strong); color: var(--text-3);
  transition: background var(--dur-2) var(--ease), border-color var(--dur-2) var(--ease); }
.aaa-step-node[data-state="done"] .aaa-step-dot { background: var(--brand);
  border-color: var(--brand); color: #fff; }
.aaa-step-node[data-state="current"] .aaa-step-dot { background: var(--surface);
  border-color: var(--brand); color: var(--brand); }
.aaa-step-label { font-size: 0.78rem; color: var(--text-3); font-weight: 520;
  text-wrap: balance; line-height: 1.25; }
.aaa-step-node[data-state="current"] .aaa-step-label { color: var(--brand); font-weight: 640; }
.aaa-step-node[data-state="done"] .aaa-step-label { color: var(--text-2); }
@media (width < 52rem) { .aaa-step-label { font-size: 0.72rem; } }
@media (width < 34rem) {
  .aaa-step-label { display: none; }
  .aaa-stepper { grid-auto-columns: auto; justify-content: space-between; }
  .aaa-step-rail { inset-inline: 0.75rem; }
}
"""

__all__ = ["STEPPER"]
