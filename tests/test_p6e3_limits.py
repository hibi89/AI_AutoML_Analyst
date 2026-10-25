"""P6E3 bounded CSV/XLSX operational tests, strictly synthetic."""
from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from fastapi.testclient import TestClient
import pytest

from backend.app.main import _read_csv_from_bytes, app
from backend.app.services.basic_report import MAX_ROWS, validate_basic_frame
from backend.app.services.tabular_input import read_xlsx_bounded


def _xlsx(headers, rows):
    book = Workbook()
    sheet = book.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    result = BytesIO()
    book.save(result)
    book.close()
    return result.getvalue()


def test_csv_near_row_limit_and_no_silent_sampling():
    # Input of exactly MAX_ROWS rows is accepted; one over must be detected.
    csv_bytes = b"n,label\n" + b"1,0\n" * MAX_ROWS
    accepted = _read_csv_from_bytes(csv_bytes)
    assert len(accepted) == MAX_ROWS
    validate_basic_frame(accepted)
    larger = _read_csv_from_bytes(csv_bytes + b"2,1\n")
    assert len(larger) == MAX_ROWS + 1
    with pytest.raises(ValueError, match="Limit exceeded"):
        validate_basic_frame(larger)


def test_xlsx_50_columns_with_ragged_records_is_not_silently_dropped():
    headers = [f"data_{i:02d}" for i in range(50)]
    rows = [[i for i in range(50)], [8, 9, 10], [None] * 49 + [4]]
    frame = read_xlsx_bounded(_xlsx(headers, rows))
    assert frame.shape == (3, 50)
    assert frame.iloc[1, 0] == 8
    assert frame.iloc[1, 3] != frame.iloc[1, 3]  # missing cell preserved
    assert frame.iloc[2, 49] == 4


def test_xlsx_preflight_blocks_row_overflow_before_parser():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["n", "value"])
    for i in range(MAX_ROWS + 1):
        sheet.append([i, i % 2])
    memory = BytesIO()
    workbook.save(memory)
    workbook.close()
    with pytest.raises(ValueError, match="XLSX limit exceeded"):
        read_xlsx_bounded(memory.getvalue())


def test_upload_oversize_rejected_before_report_generation(monkeypatch):
    from backend.app.services import basic_report
    monkeypatch.setattr(basic_report, "MAX_UPLOAD_BYTES", 64)
    payload = b"n,value\n" + b"1,2\n" * 20
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("test.csv", BytesIO(payload), "text/csv")},
    )
    assert response.status_code == 413
    assert "test.csv" not in response.text


def test_xlsx_rejects_overlong_header_without_echo():
    unique_header = "고객" * 81
    payload = _xlsx([unique_header, "target"], [[4, 1], [5, 0]])
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("data.xlsx", BytesIO(payload), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert unique_header not in response.text
