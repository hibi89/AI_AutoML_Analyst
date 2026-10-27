"""P6E43: preserve CSV field-to-header alignment in upload and local prediction.

All examples are synthetic. Pandas otherwise implicitly promotes an extra
first record field to the index and silently shifts data columns.
"""
from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from backend.app.main import _read_csv_from_bytes, app
from backend.app.services.premium_predict import _load_input


@pytest.mark.parametrize("payload", [
    b"amount,area\n1,A,secret\n2,B,secret\n",
    b"amount,area\n1,A,secret\n2,B\n",
])
def test_upload_csv_rejects_surplus_fields(payload):
    with pytest.raises(ValueError, match="more fields than header"):
        _read_csv_from_bytes(payload)

    client = TestClient(app)
    for route, data in (
        ("/api/basic-report", {}),
        ("/api/standard-report", {"target_column": "amount", "task_type": "regression"}),
        ("/api/premium-report", {"target_column": "amount", "task_type": "regression"}),
    ):
        response = client.post(
            route,
            data=data,
            files={"file": ("synthetic.csv", BytesIO(payload), "text/csv")},
        )
        assert response.status_code == 400, (route, response.status_code, response.text)
        assert "more fields than header" in response.json()["detail"]
        assert "secret" not in response.text


@pytest.mark.parametrize("payload", [
    "amount,area\n1,A,private\n2,B,private\n",
])
def test_premium_prediction_rejects_shift_before_model_load(tmp_path, payload):
    path = tmp_path / "new.csv"
    path.write_text(payload, encoding="utf-8")
    schema = {
        "raw_feature_columns": ["amount", "area"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
    }
    with pytest.raises(ValueError, match="field count"):
        _load_input(path, schema, "utf-8")


def test_short_row_is_preserved_as_missing_trailing_cell(tmp_path):
    payload = b"amount,area\\n1,A\\n2\\n"
    frame = _read_csv_from_bytes(payload, "utf-8")
    assert frame["amount"].tolist() == [1, 2]
    assert frame["area"].isna().sum() == 1

    path = tmp_path / "short-but-imputable.csv"
    path.write_bytes(payload)
    schema = {
        "raw_feature_columns": ["amount", "area"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
    }
    result = _load_input(path, schema, "utf-8")
    assert len(result) == 2
    assert result["area"].isna().sum() == 1


def test_csv_quoted_commas_and_multiline_values_keep_logical_width(tmp_path):
    payload = b'amount,area\n1,"A,B"\n2,"C\nD"\n'
    uploaded = _read_csv_from_bytes(payload, "utf-8")
    assert uploaded["amount"].tolist() == [1, 2]
    assert uploaded["area"].tolist() == ["A,B", "C\nD"]

    path = tmp_path / "legitimate.csv"
    path.write_bytes(payload)
    schema = {
        "raw_feature_columns": ["amount", "area"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
    }
    predicted_input = _load_input(path, schema, "utf-8")
    assert predicted_input["amount"].tolist() == [1, 2]
    assert predicted_input["area"].tolist() == ["A,B", "C\nD"]


def test_cp949_csv_still_parses_with_width_guard(tmp_path):
    payload = "금액,지역\n1,부산\n2,서울\n".encode("cp949")
    frame = _read_csv_from_bytes(payload, "cp949")
    assert frame["지역"].tolist() == ["부산", "서울"]
    path = tmp_path / "korean.csv"
    path.write_bytes(payload)
    schema = {
        "raw_feature_columns": ["금액", "지역"],
        "numeric_raw_columns": ["금액"],
        "boolean_raw_columns": [],
    }
    assert _load_input(path, schema, "cp949")["금액"].tolist() == [1, 2]
