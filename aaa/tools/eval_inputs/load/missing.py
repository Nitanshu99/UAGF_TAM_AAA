"""The finding recorded when no model artefact is resolvable.

Absence means different things under different access modes. Under
``artifact_upload`` a missing artefact is a genuine gap — the provider said
they would supply weights and did not. Under the reference modes the model is
named rather than uploaded by design, so reporting "no URI supplied" would be
false; what is true is that this pipeline did not recompute the metrics from
weights, because obtaining them is the evaluation service's job.
"""
from __future__ import annotations

from aaa.platform.state.model_vocab import REFERENCE_MODES
from aaa.tools.eval_inputs.types import FindingSink
from aaa.tools.findings import make_finding


def record_absent_model(sink: FindingSink, source_phase: str,
                        access_mode: str | None) -> None:
    """Record the finding appropriate to *access_mode* when no artefact loads.

    :param sink: Finding sink honouring the caller's emit flags.
    :param source_phase: Tag for the emitted finding.
    :param access_mode: Declared ``model_access_mode``, if any.
    """
    if access_mode in REFERENCE_MODES:
        sink.add(make_finding(
            finding_id="P3-MODEL-BY-REFERENCE",
            description=(
                f"Model is supplied by reference (model_access_mode="
                f"'{access_mode}'), not as an uploaded artefact; declared "
                "performance was not recomputed from weights in this pipeline."
            ),
            materiality="possibly_material", articles=["Art.15"],
            source_phase=source_phase,
            recommendation="Verify the referenced model against its pinned revision.",
        ), load=True)
        return
    if access_mode == "not_provided":
        sink.add(make_finding(
            finding_id="P3-MODEL-NOT-PROVIDED",
            description=(
                "Provider declared that no runnable model is supplied; accuracy, "
                "robustness and fairness claims are unverifiable from artefacts."
            ),
            materiality="possibly_material", articles=["Art.15"],
            source_phase=source_phase,
            recommendation="Supply the model as an upload or a pinned reference.",
        ), load=True)
        return
    sink.add(make_finding(
        finding_id="P3-MODEL-MISSING",
        description="No model artefact URI supplied; declared performance could not be "
                    "independently verified.",
        materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
        recommendation="Supply a model_artifact_uri in the Annex IV dossier.",
    ), load=True)
