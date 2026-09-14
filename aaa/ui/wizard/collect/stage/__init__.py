"""Collectors that read the wizard's session state into Stage A / Stage B payloads.

``a`` builds the Stage A declaration, ``b`` the Stage B dossier, and ``b_meta``
resolves the model-provenance and data-dictionary blocks ``b`` embeds.
"""
from __future__ import annotations

from aaa.ui.wizard.collect.stage.a import collect_stage_a
from aaa.ui.wizard.collect.stage.b import collect_stage_b
from aaa.ui.wizard.collect.stage.b_meta import data_dictionary_block, model_meta_fields

__all__ = ["collect_stage_a", "collect_stage_b", "data_dictionary_block", "model_meta_fields"]
