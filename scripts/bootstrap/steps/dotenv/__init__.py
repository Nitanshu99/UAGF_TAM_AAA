"""Step 4: a ``.env`` that runs the whole stack on one OpenRouter key.

``defaults`` holds what the bootstrap decides and the placeholder test,
``provision`` generates the Langfuse secrets a fresh file needs, ``key`` finds the
OpenRouter key, and ``configure`` writes the file.
"""
from scripts.bootstrap.steps.dotenv.configure import configure_env
from scripts.bootstrap.steps.dotenv.defaults import FIXED, REFERENCE, VENDOR_KEYS, is_placeholder
from scripts.bootstrap.steps.dotenv.key import prompt_for_key, resolve_key
from scripts.bootstrap.steps.dotenv.provision import langfuse_provisioning

__all__ = ["FIXED", "REFERENCE", "VENDOR_KEYS", "configure_env", "is_placeholder",
           "langfuse_provisioning", "prompt_for_key", "resolve_key"]
