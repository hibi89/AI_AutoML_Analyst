"""P6E45: date-derived features must never silently replace raw customer columns.

All input is synthetic. Both STANDARD and PREMIUM share this preprocessor.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.preprocessor import (
    _expand_datetime_features, build_preprocessing_pipeline,
)
from backend.app.services.standard_engine import run_standard


@pytest.mark.parametrize("suffix", ["year", "month", "day", "dayofweek", "hour"])
def test_preexisting_source_field_must_not_be_overwritten(suffix):
    original = pd.DataFrame({
        "sale_date": ["2026-01-01", "2026-01-02"],
        f"sale_date__{suffix}": [901, 902],
    })
    with pytest.raises(ValueError, match="Datetime-derived feature name conflicts"):
        _expand_datetime_features(original, ["sale_date"])
    assert original[f"sale_date__{suffix}"].tolist() == [901, 902]


def test_normal_datetime_expansion_remains_supported():
    df = pd.DataFrame({
        "sale_date": ["2026-01-01", "2026-02-02"],
        "income": [900, 901],
    })
    actual = _expand_datetime_features(df, ["sale_date"])
    assert actual["sale_date__year"].tolist() == [2026, 2026]
    assert actual["sale_date__month"].tolist() == [1, 2]
    assert actual["income"].tolist() == [900, 901]
    assert "sale_date" not in actual.columns


def _colliding_frame():
    return pd.DataFrame({
        "sale_date": pd.date_range("2026-01-01", periods=48).strftime("%Y-%m-%d"),
        "sale_date__year": list(range(900, 948)),
        "amount": [float(i % 11) for i in range(48)],
        "label": [i % 2 for i in range(48)],
    })


def test_training_preprocessor_rejects_collision_before_model_fit():
    frame = _colliding_frame()
    with pytest.raises(ValueError, match="Datetime-derived feature name conflicts"):
        build_preprocessing_pipeline(frame, target_column="label", task_type="classification")
    with pytest.raises(ValueError, match="Datetime-derived feature name conflicts"):
        run_standard(frame, "label", task_type="classification")


@pytest.mark.parametrize("route", ["/api/standard-report", "/api/premium-report"])
def test_real_http_report_returns_controlled_error_without_corrupting_raw_columns(route):
    frame = _colliding_frame()
    response = TestClient(app).post(
        route,
        data={"target_column": "label", "task_type": "classification"},
        files={"file": ("synthetic.csv", BytesIO(frame.to_csv(index=False).encode("utf-8-sig")), "text/csv")},
    )
    assert response.status_code == 400, (route, response.status_code, response.text)
    assert "Datetime-derived feature name conflicts" in response.json()["detail"]
    assert "900" not in response.text
