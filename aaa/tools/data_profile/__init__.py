"""data_profile — Dataset profiling wrapper (§4.1).

Returns a structured summary dict compatible with T07_data_quality_report
``dataset_summary`` block.

Production path:  ydata-profiling (``ProfileReport``).
Fallback: pandas describe()-based stats with no external dependency.

Usage
-----
    from src.tools.data_profile import data_profile

    summary = data_profile(df, target_column="class")"""
from aaa.tools.data_profile.core import data_profile  # noqa: F401
from aaa.tools.data_profile.dtype_summary import _dtype_summary  # noqa: F401
from aaa.tools.data_profile.logger import _profile_ydata, logger  # noqa: F401
from aaa.tools.data_profile.profile_pandas import _profile_pandas  # noqa: F401
from aaa.tools.data_profile.unmeasured import not_profiled  # noqa: F401

__all__ = [
    'logger', '_profile_ydata', '_dtype_summary', '_profile_pandas', 'data_profile', 'not_profiled',
]
