"""P6 host/origin/legacy safety and schema-quality regression checks."""
from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app


def test_legacy_filesystem_routes_are_closed():
    client = TestClient(app)
    assert client.get("/api/folders/browse").status_code == 403
    assert client.post("/api/folder/scan", data={"root_path": "/tmp"}).status_code == 403
    assert client.post("/api/analyze-path", data={"file_path": "/etc/passwd", "target_column": "a"}).status_code == 403


def test_legacy_job_and_upload_routes_block_foreign_hosts_and_origins():
    client = TestClient(app)
    assert client.get("/api/results", headers={"host": "untrusted.example"}).status_code == 403
    assert client.get("/api/results", headers={"origin": "https://untrusted.example"}).status_code == 403
    assert client.get("/health", headers={"host": "untrusted.example"}).status_code == 403
    assert client.get("/health", headers={"origin": "null"}).status_code == 403
    assert client.get("/health", headers={"origin": "http://testserver"}).status_code == 200


def test_legacy_upload_bounded(monkeypatch):
    from backend.app.services import basic_report
    monkeypatch.setattr(basic_report, "MAX_UPLOAD_BYTES", 10)
    response = TestClient(app).post(
        "/api/analyze",
        data={"target_column": "y", "task_type": "classification"},
        files={"file": ("tiny.csv", BytesIO(b"x,y\n1,0\n2,1\n3,0\n"), "text/csv")},
    )
    assert response.status_code == 413


def test_report_routes_same_machine_boundary():
    client = TestClient(app)
    for route in ["/basic-mvp", "/standard-mvp", "/premium-mvp"]:
        assert client.get(route, headers={"origin": "http://127.0.0.1:9999"}).status_code == 403
    assert client.get("/health").status_code == 200


def test_legacy_csv_upload_rejects_excess_columns(monkeypatch):
    from backend.app.services import basic_report
    monkeypatch.setattr(basic_report, "MAX_COLUMNS", 2)
    data = pd.DataFrame({"x":[1,2,3,4], "y":[2,3,4,5], "label":[0,1,0,1]})
    r = TestClient(app).post(
        "/api/analyze", data={"target_column": "label", "task_type": "classification"},
        files={"file": ("x.csv", BytesIO(data.to_csv(index=False).encode()), "text/csv")},
    )
    assert r.status_code == 400
    assert "Limit exceeded" in r.text
