"""lime_explain — LIME local instance explanations (§4.2).

Returns a list of per-instance explanations compatible with the T10
``local_explanations`` block.

Production path:  ``lime.lime_tabular.LimeTabularExplainer``.
No fallback: raw feature values are not contributions, so when LIME cannot
                  run nothing is returned and the reason goes to ``reasons``.

Usage
-----
    from src.tools.lime_explain import lime_explain

    explanations = lime_explain(
        model=clf,
        X=X_test,
        feature_names=cols,
        num_instances=5,
        num_features=10,
    )"""
from aaa.tools.lime_explain.explain.lime import _explain_lime  # noqa: F401
from aaa.tools.lime_explain.infer_feature_names import (  # noqa: F401
    _infer_feature_names,
    lime_explain,
)
from aaa.tools.lime_explain.logger import (  # noqa: F401
    _DEFAULT_NUM_FEATURES,
    _DEFAULT_NUM_INSTANCES,
    logger,
)
from aaa.tools.lime_explain.row_count import _is_numeric, _row_count  # noqa: F401

__all__ = [
    'logger',
    '_DEFAULT_NUM_INSTANCES',
    '_DEFAULT_NUM_FEATURES',
    '_explain_lime',
    '_row_count',
    '_is_numeric',
    '_infer_feature_names',
    'lime_explain',
]
