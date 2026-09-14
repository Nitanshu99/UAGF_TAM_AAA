"""What a loaded model states about itself, for the model card.

T09's architecture and training fields were hard-coded to null although Phase 3
had loaded the model (case 03, 2026-09-13: an IsolationForest exposing
``n_features_in_ = 13`` and its full ``get_params()``), and the Verifier refused
the card for it. Only facts the model object itself carries are read; anything
it does not carry stays ``None``.
"""
from aaa.tools.model_meta.introspect.facts import model_facts
from aaa.tools.model_meta.introspect.params import hyperparameters, parameter_count

__all__ = ["hyperparameters", "model_facts", "parameter_count"]
