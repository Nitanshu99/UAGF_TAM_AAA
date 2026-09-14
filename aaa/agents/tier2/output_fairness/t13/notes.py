"""What T13 says about the sample — including when there was none.

With no system outputs to sample the log read "Sampled 0 predictions via 'first_n'
strategy" and its Art. 10 §2(f) note said the sample had been "inspected for
discriminatory patterns" — an examination that never ran (live run bb7837, which
the Verifier rated material). Both now state what happened.
"""
from __future__ import annotations

_NO_OUTPUTS = "No system outputs were available to sample."


def sampling_narrative(sampled: int, strategy: str, toxicity_verdict: str,
                       skipped_reason: str | None) -> str:
    """The sampling narrative for *sampled* predictions.

    :param sampled: Predictions actually sampled.
    :param strategy: The declared sampling strategy.
    :param toxicity_verdict: ``toxicity_classifier`` verdict.
    :param skipped_reason: Why Phase 4 had nothing to test, when it had nothing.
    """
    if sampled:
        return (f"Sampled {sampled} predictions via '{strategy}' strategy; toxicity verdict: "
                f"{toxicity_verdict}.")
    return f"No predictions were sampled, so no output was inspected. {skipped_reason or _NO_OUTPUTS}"


def art10_2f_note(sampled: int, toxicity_verdict: str, skipped_reason: str | None,
                  text_outputs: bool = True) -> str:
    """Whether the Art. 10 §2(f) examination of outputs was performed, and on what.

    :param text_outputs: The outputs are language; labels and scores are examined by
        T12's group-fairness analysis, and no language screen applies to them.
    """
    if sampled and not text_outputs:
        return (f"The {sampled} sampled outputs are the model's labels or scores, not "
                "language, so no toxicity or discriminatory-language screen applies; the "
                "Art. 10 §2(f) examination of these outputs is the group-fairness analysis "
                "recorded in T12.")
    if sampled and toxicity_verdict != "NOT_TESTED":
        return (f"Output sample of {sampled} predictions inspected for discriminatory patterns "
                "per Art. 10 §2(f).")
    if sampled:
        return (f"{sampled} predictions were sampled but not scored for discriminatory patterns "
                "(toxicity NOT_TESTED); the Art. 10 §2(f) examination of outputs is incomplete.")
    return ("No output sample was inspected, so the Art. 10 §2(f) examination of the system's "
            f"outputs was not performed. {skipped_reason or _NO_OUTPUTS}")


__all__ = ["art10_2f_note", "sampling_narrative"]
