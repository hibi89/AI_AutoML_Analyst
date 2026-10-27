"""P6E44: reject deceptive Unicode control marks in customer column headers.

Preserve ordinary Korean/Japanese/Latin characters while preventing hidden
directional controls or DEL/C1 from spoofing PDF and CSV labels. Synthetic only.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from backend.app.main import app
from backend.app.services.basic_report import validate_basic_frame


@pytest.mark.parametrize("control", [
    "\u202e",  # right-to-left override
    "\u2066",  # left-to-right isolate
    "\u200f",  # right-to-left mark
    "\u061c",  # Arabic letter mark
    "\u007f",  # DEL, outside the former <32 ASCII filter
    "\u0085",  # C1 next-line control
])
def test_deceptive_control_header_rejected(control):
    df = pd.DataFrame({"매출" + control + "액": [100, 120], "label": [0, 1]})
    with pytest.raises(ValueError, match="control or bidirectional"):
        validate_basic_frame(df)


def test_legitimate_korean_japanese_and_punctuation_still_accepted():
    df = pd.DataFrame({
        "매출액(원)": [100, 110],
        "売上金額": [90, 80],
        "region _ 2026": ["부산", "서울"],
    })
    validate_basic_frame(df)


@pytest.mark.parametrize("route,form", [
    ("/api/basic-report", {}),
    ("/api/standard-report", {"target_column": "label", "task_type": "classification"}),
    ("/api/premium-report", {"target_column": "label", "task_type": "classification"}),
])
@pytest.mark.parametrize("format", ["csv", "xlsx"])
def test_three_skus_reject_bidi_control_before_analysis(route, form, format):
    columns = ["매출" + chr(0x202E) + "액", "label"]
    df = pd.DataFrame({columns[0]: [1, 2, 3, 4, 5, 6], "label": [0, 1, 0, 1, 0, 1]})
    if format == "csv":
        payload = df.to_csv(index=False).encode("utf-8-sig")
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(columns)
        for row in df.itertuples(index=False, name=None):
            ws.append(row)
        stream = BytesIO()
        wb.save(stream)
        payload = stream.getvalue()
    response = TestClient(app).post(
        route, data=form, files={"file": ("synthetic." + format, BytesIO(payload),
        "text/csv" if format == "csv" else
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 400, (route, format, response.status_code, response.text)
    assert "control or bidirectional" in response.json()["detail"]
    assert columns[0] not in response.text
