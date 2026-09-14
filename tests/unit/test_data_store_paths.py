"""Tests for aaa.data.paths helpers."""
from __future__ import annotations

from tests.unit.support.data_store_fixtures import isolated_data_dir  # noqa: F401


class TestPaths:
    def test_inputs_dir(self, isolated_data_dir):  # noqa: F811
        from aaa.data.paths import inputs_dir
        assert inputs_dir("eng-001") == isolated_data_dir / "inputs" / "eng-001"

    def test_results_dir(self, isolated_data_dir):  # noqa: F811
        from aaa.data.paths import results_dir
        assert results_dir("eng-001") == isolated_data_dir / "results" / "eng-001"

    def test_index_path(self, isolated_data_dir):  # noqa: F811
        from aaa.data.paths import index_path
        assert index_path() == isolated_data_dir / "index.json"
