"""The motion layer: entry animations, the stepper's travelling fill, and the
score arc drawing itself in.

Streamlit replaces the DOM subtree on every rerun, so a CSS ``animation`` on a
rendered element plays once per render for free — no ``@starting-style``, no
JavaScript. That is what makes each step of the wizard *arrive* instead of
appearing.

Reduced motion is handled the way the guidance asks: not by zeroing every
duration globally (which makes some animations more jarring, not less), but by
a ``--anim-reduced`` custom property each animated rule sets to its own calm
alternative.
"""
from __future__ import annotations

MOTION = """
@property --anim-reduced {
  syntax: "*";
  inherits: false;
  initial-value: none;
}

@keyframes aaa-rise { from { opacity: 0; translate: 0 14px; } }
@keyframes aaa-fade { from { opacity: 0; } }
@keyframes aaa-pop { from { opacity: 0; scale: 0.94; } }
@keyframes aaa-sweep { from { transform: scaleX(0); } }
@keyframes aaa-draw { from { stroke-dashoffset: var(--arc-len); } }
@keyframes aaa-pulse {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in oklab, var(--brand) 40%, transparent); }
  50% { box-shadow: 0 0 0 6px color-mix(in oklab, var(--brand) 0%, transparent); }
}

/* Every authored surface rises into place, staggered by its --i index. */
:where(.aaa-rise, .aaa-card, .aaa-kpi, .aaa-finding, .aaa-article-row) {
  animation: aaa-rise var(--dur-3) var(--ease) backwards;
  animation-delay: calc(var(--i, 0) * 55ms);
  --anim-reduced: aaa-fade var(--dur-2) var(--ease) backwards;
}
.aaa-pop { animation: aaa-pop var(--dur-2) var(--ease) backwards; --anim-reduced: aaa-fade var(--dur-2); }

/* The stepper's completed rail grows from the start edge. */
.aaa-step-rail-fill {
  transform-origin: left center;
  animation: aaa-sweep var(--dur-3) var(--ease);
  --anim-reduced: none;
}
.aaa-step-node[data-state="current"] .aaa-step-dot {
  animation: aaa-pulse 2.4s var(--ease) infinite;
  --anim-reduced: none;
}

/* The conformity arc draws from zero to its value. */
.aaa-arc {
  animation: aaa-draw 1.1s var(--ease) backwards;
  animation-delay: 0.15s;
  --anim-reduced: none;
}

@media (prefers-reduced-motion: reduce) {
  * { animation: var(--anim-reduced) !important; }
  .stApp *, .stApp *::before, .stApp *::after { transition-duration: 0.01s !important; }
}
"""
