"""Playwright driver that fills the Mariposa wizard form from its intake bundle.

Labels are imported from the modules that render them rather than copied, so a
renamed field stops the driver instead of silently leaving a slot blank.
"""
