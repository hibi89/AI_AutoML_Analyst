"""BASIC MVP integration tests: synthetic CSV upload -> diagnostics ZIP."""
from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile
import json

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import basic_report


def demo_data() -> bytes:
    df = pd.DataFrame(
        {
            "units": [i % 11 for i in range(45)],
            "region": ["north" if i % 2 else "south" for i in range(45)],
            "returned": [i % 5 == 0 for i in range(45)],
        }
    )
    df.loc[0, "region"] = None
    return df.to_csv(index=False).encode("utf-8")


def test_basic_web_page_responds() -> None:
    response = TestClient(app).get("/basic-mvp")
    assert response.status_code == 200
    assert "표형 데이터 진단" in response.text


def test_csv_to_zip_contains_factual_diagnostics() -> None:
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("sample.csv", BytesIO(demo_data()), "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/zip")
    with ZipFile(BytesIO(response.content)) as archive:
        filenames = set(archive.namelist())
        assert {"report.pdf", "summary.csv", "summary.json", "README.txt", "manifest.json", "charts/01_distribution.png"} <= filenames
        values = json.loads(archive.read("summary.json"))
        assert values["rows"] == 45
        assert values["columns"] == 3
        assert values["missing_cells"] == 1
        assert len(values["findings"]) >= 3
        assert archive.read("report.pdf").startswith(b"%PDF-")
        assert values["chart_count"] >= 1
        assert archive.read("charts/01_distribution.png").startswith(b"\\x89PNG\\r\\n\\x1a\\n".decode("unicode_escape").encode("latin1"))
        assert "sample.csv" not in filenames


def test_rejects_invalid_extension() -> None:
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("sample.txt", b"units\\n1", "text/plain")},
    )
    assert response.status_code == 400


def test_rejects_oversized_upload(monkeypatch) -> None:
    monkeypatch.setattr(basic_report, "MAX_UPLOAD_BYTES", 20)
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("sample.csv", b"units\\n" + b"1\\n" * 12, "text/csv")},
    )
    assert response.status_code == 413


def test_rejects_foreign_browser_origin() -> None:
    response = TestClient(app).post(
        "/api/basic-report",
        headers={"origin": "https://example.org"},
        files={"file": ("sample.csv", BytesIO(demo_data()), "text/csv")},
    )
    assert response.status_code == 403


def test_rejects_too_many_columns(monkeypatch) -> None:
    monkeypatch.setattr(basic_report, "MAX_COLUMNS", 2)
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("sample.csv", BytesIO(demo_data()), "text/csv")},
    )
    assert response.status_code == 400


def test_export_csv_guards_formula_prefixes() -> None:
    assert basic_report._csv_safe("=1+1") == "'=1+1"
    assert basic_report._csv_safe("@SUM(A1)") == "'@SUM(A1)"
