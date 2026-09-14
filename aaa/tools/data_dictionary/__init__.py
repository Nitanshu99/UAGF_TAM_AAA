"""aaa.tools.data_dictionary — Resolve how to split a client dataset for analysis.

To independently re-run metrics, fairness, and robustness, the phase agents must
know (a) which column is the prediction target, (b) which label counts as the
favourable/positive outcome, and (c) which columns are protected attributes for
fairness testing.

A real auditor expects this in the technical documentation. When the client
supplied it (Stage B ``data_dictionary`` or top-level keys) we use it verbatim;
otherwise we derive it defensively from the column names and **record every
assumption** so the calling agent can raise it as a finding rather than proceeding
silently on a guess."""
from aaa.tools.data_dictionary.resolve.data_dictionary import resolve_data_dictionary  # noqa: F401
from aaa.tools.data_dictionary.resolve.target import (  # noqa: F401
    _resolve_sensitive,
    _resolve_target,
)
from aaa.tools.data_dictionary.sensitive_patterns import (  # noqa: F401
    _SENSITIVE_PATTERNS,
    DataDictionary,
    _explicit_block,
    explicit_data_dictionary,
)

__all__ = [
    '_SENSITIVE_PATTERNS', 'DataDictionary', '_explicit_block', '_resolve_target', '_resolve_sensitive',
    'resolve_data_dictionary', 'explicit_data_dictionary', '__all__',
]
