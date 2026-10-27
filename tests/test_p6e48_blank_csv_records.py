"""P6E48 — reject blank logical CSV records instead of silently losing rows.

Both the shared API upload and the shipped PREMIUM local CSV predictor preflight
use csv.reader to ensure pandas' default skip_blank_lines cannot remove records.
All synthetic; blank *cells* and quoted multiline CSV remain legal.
"""
from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from backend.app.main import _read_csv_from_bytes, app
from backend.app.services.premium_predict import _load_input


@pytest.mark.parametrize("payload", [
    b"amount,area\n1,A\n\n2,B\n",
    b"amount,area\n\n1,A\n2,B\n",
    b"amount,area\n1,A\n2,B\n\n",
])
def test_shared_upload_rejects_blank_logical_record(payload):
    with pytest.raises(ValueError, match="blank data row"):
        _read_csv_from_bytes(payload, "utf-8")
    client = TestClient(app)
    for tier, extra in (
        ("basic", {}),
        ("standard", {"target_column": "amount", "task_type": "regression"}),
        ("premium", {"target_column": "amount", "task_type": "regression"}),
    ):
        resp = client.post(
            f"/api/{tier}-report",
            data=extra,
            files={"file": ("synthetic.csv", BytesIO(payload), "text/csv")},
        )
        assert resp.status_code == 400, (tier, resp.status_code)
        assert "blank data row" in resp.json()["detail"]


@pytest.mark.parametrize("payload", [
    "amount,area\n1,A\n\n2,B\n",
    "amount,area\n1,A\n2,B\n\n",
])
def test_premium_predict_rejects_blank_record(payload, tmp_path):
    path = tmp_path / "new.csv"
    path.write_text(payload, encoding="utf-8")
    schema = {
        "raw_feature_columns": ["amount", "area"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
    }
    with pytest.raises(ValueError, match="blank data row"):
        _load_input(path, schema, "utf-8")


def test_missing_cells_and_multiline_quoted_value_stay_supported(tmp_path):
    valid = 'amount,area\n1,"A\nB"\n2,\n3\n'
    payload = valid.encode("utf-8")
    uploaded = _read_csv_from_bytes(payload, "utf-8")
    assert len(uploaded) == 3
    assert uploaded["area"].iloc[0] == "A\nB"
    assert uploaded["area"].isna().sum() == 2

    path = tmp_path / "new.csv"
    path.write_bytes(payload)
    schema = {
        "raw_feature_columns": ["amount", "area"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
    }
    predicted_input = _load_input(path, schema, "utf-8")
    assert len(predicted_input) == 3
    assert predicted_input["area"].iloc[0] == "A\nB"
    assert predicted_input["area"].isna().sum() == 2
