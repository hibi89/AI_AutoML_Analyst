"""P6E13: reject original duplicate/blank CSV headers before pandas mangles them.

Data here are synthetic. The test does not generate a customer report.
"""
from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from backend.app.main import _read_csv_from_bytes, app


@pytest.mark.parametrize(
    "payload",
    [
        b"amount,amount,target\n100,200,0\n200,300,1\n",
        b'"sales,total","sales,total",target\n100,200,0\n',
        "매출,매출,결과\n100,200,0\n".encode("cp949"),
    ],
)
def test_duplicate_headers_do_not_get_renamed(payload: bytes):
    with pytest.raises(ValueError, match="Duplicate column names"):
        _read_csv_from_bytes(payload)
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("example.csv", BytesIO(payload), "text/csv")},
    )
    assert response.status_code == 400
    assert "Duplicate column names" in response.text


@pytest.mark.parametrize(
    "payload",
    [
        b"amount,,target\n100,200,0\n",
        b"amount,   ,target\n100,200,0\n",
    ],
)
def test_blank_original_header_rejected(payload: bytes):
    with pytest.raises(ValueError, match="nonempty"):
        _read_csv_from_bytes(payload)


def test_legitimate_dotted_name_not_false_positive():
    frame = _read_csv_from_bytes(b"sales,sales.1\n10,20\n30,40\n")
    assert list(frame.columns) == ["sales", "sales.1"]
    assert frame.shape == (2, 2)


def test_valid_utf8_korean_headers_remain_unchanged():
    original = "매출,구매\n100,1\n200,0\n".encode("utf-8-sig")
    frame = _read_csv_from_bytes(original)
    assert list(frame.columns) == ["매출", "구매"]
