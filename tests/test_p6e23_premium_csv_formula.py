"""P6E23: PREMIUM sample_input.csv must never export executable CSV headers.

The delivered prediction schema is intentionally exact; escaping its
headers would break repeat prediction. Synthetic test data only.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import premium_delivery


@pytest.mark.parametrize("unsafe", [
    '=HYPERLINK("https://example.invalid","link")',
    "  =SUM(1,2)",
    "+SUM(1,2)",
    "-1+2",
    "@SUM(1,2)",
])
def test_premium_api_blocks_formula_shaped_feature_header_before_training(
    unsafe, monkeypatch,
):
    def not_reached(*args, **kwargs):
        raise AssertionError("unsafe feature header must fail before ML training")
    monkeypatch.setattr(premium_delivery, "run_standard", not_reached)
    frame = pd.DataFrame({
        unsafe: [10 + i for i in range(40)],
        "label": [i % 2 for i in range(40)],
    })
    response = TestClient(app).post(
        "/api/premium-report",
        data={"target_column": "label", "task_type": "classification"},
        files={"file": ("synthetic.csv", BytesIO(frame.to_csv(index=False).encode()), "text/csv")},
    )
    assert response.status_code == 400
    assert "spreadsheet formula-like feature headers" in response.text
    # Error messages must not expose the customer-supplied formula/header.
    assert unsafe not in response.text


def test_valid_business_feature_names_preserve_exact_schema():
    frame = pd.DataFrame({
        "gross-margin": [10, 20],
        "sales@shop": [3, 4],
        "label": [0, 1],
    })
    premium_delivery._reject_unsafe_sample_headers(frame, "label", None, None)


def test_formula_shaped_target_or_excluded_group_not_in_prediction_template():
    frame = pd.DataFrame({
        "visits": [2, 4],
        "@target": [0, 1],
        "=internal_group": ["A", "B"],
    })
    premium_delivery._reject_unsafe_sample_headers(
        frame, "@target", "=internal_group", None,
    )


def test_safe_premium_remains_unchanged_with_existing_exact_schema():
    frame = pd.DataFrame({"visits": [1, 2], "label": [0, 1]})
    premium_delivery._reject_unsafe_sample_headers(frame, "label", None, None)
