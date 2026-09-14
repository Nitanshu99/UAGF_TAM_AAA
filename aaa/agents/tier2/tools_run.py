"""What each phase's runtime actually ran, by tool name (finding F10).

The phase agents run a fixed block of deterministic tools *before* the model is
invoked, and hand the results over as ``tool_outputs``. Those output keys are
not tool names — Phase 2 passes ``profile_result`` and ``missingness`` for
``data_profile`` and ``missingness_scan`` — so a model reading its payload could
not tell which of the tools its prompt lists had been run for it. At case 01
call #003 the DataAuditor asked for ``drift_test`` in ``tool_calls``; the tool
had in fact run, and its result reached neither the payload nor the artefact.

``tools_run`` names the tools of *this* dispatch, in run order, so the model is
told rather than left to infer, and so
:func:`aaa.tools.evidence_retrieval.tool_requests.check_tool_requests` has an
authoritative set to test a model-named tool against.
"""
from __future__ import annotations

from collections.abc import Iterable

#: Tools each phase's runtime invokes on every dispatch. They fail soft — a
#: tool that could not compute still runs and reports why in ``tool_outputs``,
#: which is a different thing from not having been run at all.
PHASE_TOOLS: dict[str, tuple[str, ...]] = {
    "P1": ("annex_iii_classify", "declaration_diff", "art43_select"),
    "P2": ("data_profile", "missingness_scan", "class_balance", "pii_scan",
           "drift_test"),
    "P3": ("metric_suite", "robustness_probe"),
    "P4": ("demographic_parity", "equal_opportunity", "disparate_impact",
           "subgroup_metrics", "toxicity_classifier"),
    "P5": ("cgsa_pull", "cgsa_ingest"),
    # T17 is rendered before the synthesis call; the T18 render follows it.
    "P6": ("template_render",),
}

#: Phase 3 records the explainability *technique* it managed to run; the model
#: is offered the tools those techniques belong to (PROMPT.md §7 AGENT_TOOLS).
#: A technique that could not run produced no output and is not listed; why it
#: did not run is answered by ``tool_outputs.explainability_degraded``.
TECHNIQUE_TOOLS: dict[str, str] = {
    "shap": "shap_explain",
    "lime": "lime_explain",
    "gradcam": "gradcam_explain",
    "token_importance": "text_explain",
}


def tools_run(phase_id: str, *, client_docs: bool = False,
              techniques: Iterable[str] = ()) -> list[str]:
    """Return the tool names this dispatch ran, in run order.

    :param phase_id: Phase whose fixed tool block ran (``P1`` … ``P6``).
    :type phase_id: str
    :param client_docs: Whether ``client_doc_search`` ran for this dispatch —
        it is guarded on the engagement having an ingested document collection.
    :type client_docs: bool
    :param techniques: Explainability techniques Phase 3 actually produced;
        mapped onto their tool names and ignored for every other phase.
    :type techniques: Iterable[str]
    :returns: Tool names, without duplicates, in the order they ran.
    :rtype: list[str]
    """
    names = list(PHASE_TOOLS.get(phase_id, ()))
    names += [TECHNIQUE_TOOLS[t] for t in techniques if t in TECHNIQUE_TOOLS]
    if client_docs:
        names.append("client_doc_search")
    return list(dict.fromkeys(names))


__all__ = ["PHASE_TOOLS", "TECHNIQUE_TOOLS", "tools_run"]
