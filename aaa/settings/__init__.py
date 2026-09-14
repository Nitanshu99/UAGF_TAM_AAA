"""aaa.settings — Centralised configuration via pydantic-settings (§14.3).

Import the singleton ``settings`` object wherever you need a config value::

    from aaa.settings import settings

    print(settings.platform_port)
"""
from aaa.settings.model import AAASettings, settings

__all__ = ["AAASettings", "settings"]
