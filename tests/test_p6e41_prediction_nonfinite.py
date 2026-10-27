"""P6E41: trusted PREMIUM new-data validation is consistent with training."""
from __future__ import annotations

import pytest

from backend.app.services.premium_predict import _load_input


@pytest.mark.parametrize("bad", ["Infinity", "-Infinity"])
def test_repeated_prediction_rejects_positive_or_negative_infinity(tmp_path, bad):
    source = tmp_path / "synthetic.csv"
    source.write_text("amount,area\n1,A\n" + bad + ",B\n3,C\n", encoding="utf-8")
    schema = {
        "raw_feature_columns": ["amount", "area"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
    }
    with pytest.raises(ValueError, match="infinite values"):
        _load_input(source, schema)


def test_repeated_prediction_allows_missing_numeric_for_existing_imputer(tmp_path):
    source = tmp_path / "synthetic.csv"
    source.write_text("amount,area\n1,A\n,B\n3,C\n", encoding="utf-8")
    schema = {
        "raw_feature_columns": ["amount", "area"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
    }
    loaded = _load_input(source, schema)
    assert len(loaded) == 3
    assert loaded["amount"].isna().sum() == 1
