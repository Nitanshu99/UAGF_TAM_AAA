"""Model-metadata vocabularies for the S6 hand-off (task type, format, framework).

Single source for the Literal types used in :mod:`aaa.platform.state.dossier`
and the runtime tuples the wizard select-boxes and validators consume.

Provenance (2026-08) extends this with :data:`ModelAccessMode` and
:class:`ModelReference`. The pre-existing vocabulary could only describe a
model as *a file we hold* — every field assumed uploaded bytes — so a customer
running a vendor-hosted model had nowhere truthful to put that fact and ended
up declaring a ``model_format`` promising weights that never arrived. The
access mode is the discriminator: it answers the only question a loader needs
answered, namely how to obtain something runnable.

Fix F9 (2026-09-06, findings S9–S11) widened three of these vocabularies, because
being narrower than reality does not prevent a false declaration — it *compels*
one. ``ModelFramework`` held three members while the S6 contract lists eight, so
RetailIQ's Chronos transformer behind a random-forest wrapper had to declare
plain ``sklearn`` and LegalMind's LoRA adapter had to declare plain
``transformers``: a consumer following either would load the wrong object and be
told nothing. ``TaskType`` had no ``anomaly_detection``, and
:mod:`aaa.tools.model_meta.backfill` recorded the consequence in its own
docstring — *"harbourlogistik's anomaly detector maps to binary_classification
pending an enum extension on the S6 side"* — while the S6 sheet had accepted
``anomaly_detection`` all along. The enum extension was owed here.
"""
from __future__ import annotations

from typing import NotRequired, TypedDict

from aaa.platform.state.model_vocab import ModelProvider


class ModelReference(TypedDict):
    """Vendor-side identity of a model the auditor does not host.

    ``revision`` is required rather than optional because it is what turns a
    reference into evidence: ``gpt-4o`` and a ``main`` branch both re-point
    over time, so an audit pinned to either cannot name the weights it
    actually assessed.
    """
    provider: ModelProvider
    model_id: str
    revision: str
    endpoint_url: NotRequired[str | None]
    auth_type: NotRequired[str | None]
    gated: NotRequired[bool | None]
    license: NotRequired[str | None]
    base_model_id: NotRequired[str | None]
    base_model_revision: NotRequired[str | None]
    adapter_uri: NotRequired[str | None]
    adapter_reference: NotRequired[str | None]
    peft_type: NotRequired[str | None]
    runtime_versions: NotRequired[dict[str, str] | None]
    quantization: NotRequired[str | None]
    decoding_params: NotRequired[dict[str, float | int | str] | None]
    upstream_provider: NotRequired[str | None]
