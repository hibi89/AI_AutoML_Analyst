"""Reject NUL-bearing prediction CSV before model input parsing."""
from __future__ import annotations
import pytest
from backend.app.services.premium_predict import _load_input

@pytest.mark.parametrize("payload", [
    b"amount,area\n1,A\x00B\n",
    b"amount,area\x00\n1,A\n",
])
def test_premium_predict_rejects_nul(payload, tmp_path):
    path = tmp_path / "prediction.csv"
    path.write_bytes(payload)
    schema = {"raw_feature_columns": ["amount", "area"], "numeric_raw_columns": ["amount"], "boolean_raw_columns": []}
    with pytest.raises(ValueError, match="NUL bytes"):
        _load_input(path, schema, "utf-8")
