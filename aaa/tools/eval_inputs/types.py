"""Result container and finding sink for the evaluation loader."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aaa.tools.data_dictionary import DataDictionary


@dataclass
class ScoredEvaluation:
    """Result of loading + independently scoring an evaluation set."""

    model: Any = None
    X_eval: Any = None
    # The matrix the model is actually scored on: ``X_eval`` selected down to the
    # bundle's ``feature_cols`` and label-encoded with its fitted encoders. The raw
    # frame keeps its categorical strings, which SHAP / LIME / the robustness probe
    # cannot consume — they need the model's own input space, not the client's.
    X_model: Any = None
    #: Columns the model bundle label-encodes, i.e. the categorical features.
    categorical_features: list[str] = field(default_factory=list)
    y_true: list[Any] | None = None
    y_pred: list[Any] | None = None
    y_proba: list[float] | None = None
    data_dict: DataDictionary | None = None
    sensitive_features: dict[str, list[Any]] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    # classification | regression | anomaly | unknown — drives whether group-fairness
    # semantics apply (they do not for a forecaster or an anomaly detector).
    task_type: str = "unknown"
    #: ``predict`` in the evaluation set's label space (outlier detectors mapped); every
    #: consumer that runs the model — metrics and both robustness probes — uses it.
    predict_fn: Any = None

    @property
    def scored(self) -> bool:
        """True when an aligned (y_true, y_pred) pair is available."""
        return (
            self.y_true is not None and self.y_pred is not None
            and len(self.y_true) > 0 and len(self.y_pred) == len(self.y_true)
        )


@dataclass
class FindingSink:
    """Routes findings into a result honouring the caller's emit flags."""

    result: ScoredEvaluation
    emit_load: bool = True
    emit_datadict: bool = True

    def add(self, finding: dict[str, Any], *, load: bool = False,
            datadict: bool = False) -> None:
        """Append *finding* unless its category is suppressed.

        :param finding: The finding dict to record.
        :param load: Marks a loading/validity finding (Phase 3 owns these).
        :param datadict: Marks a data-dictionary assumption finding.
        """
        if load and not self.emit_load:
            return
        if datadict and not self.emit_datadict:
            return
        self.result.findings.append(finding)
