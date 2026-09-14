"""shap_explain — SHAP-based global feature importance (§4.2).

Returns a structured dict compatible with the T10_explainability_report
``global_explanation`` block.

Production path:  ``shap.Explainer`` (TreeExplainer / KernelExplainer /
                  PermutationExplainer auto-detected by SHAP) for tabular
                  or NLP feature inputs.
No fallback: when SHAP cannot run, no importances are reported and the
                  reason is returned as ``degraded_reason``.

Usage
-----
    from src.tools.shap_explain import shap_explain

    result = shap_explain(model=clf, X=X_test, feature_names=cols)"""
from aaa.tools.shap_explain.infer_feature_names import (  # noqa: F401
    _empty_result,
    _infer_feature_names,
    shap_explain,
)
from aaa.tools.shap_explain.is_numeric import _is_numeric  # noqa: F401
from aaa.tools.shap_explain.logger import (  # noqa: F401
    _DEFAULT_SAMPLE,
    _DEFAULT_TOP_K,
    _columns_of,
    _explain_shap,
    _row_count,
    logger,
)

__all__ = [
    'logger',
    '_DEFAULT_SAMPLE',
    '_DEFAULT_TOP_K',
    '_row_count',
    '_explain_shap',
    '_columns_of',
    '_is_numeric',
    '_infer_feature_names',
    '_empty_result',
    'shap_explain',
]
