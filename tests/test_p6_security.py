"""P6 host/origin/legacy safety and schema-quality regression checks."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app


def test_docker_compose_is_local_only_and_uses_verified_dependencies():
    repo_root = Path(__file__).resolve().parents[1]
    compose = (repo_root / "docker-compose.yml").read_text(encoding="utf-8")
    dockerfile = (repo_root / "Dockerfile").read_text(encoding="utf-8")

    assert '"127.0.0.1:8000:8000"' in compose
    assert "C:/Users/" not in compose
    assert "C:\\Users\\" not in compose
    assert "target: /data" not in compose
    assert 'AUTOML_LOCAL_DOCKER_COMPOSE: "1"' in compose
    assert "./local-fonts:/run/automl-fonts:ro" in compose
    assert "AUTOML_KOREAN_FONT_PATH: /run/automl-fonts/NanumGothic.ttf" in compose
    assert "COPY requirements-verified-py311.txt" in dockerfile
    assert "python -m pip install --no-cache-dir -r requirements-verified-py311.txt" in dockerfile


def test_docker_gateway_peer_is_trusted_only_in_explicit_compose_mode(monkeypatch):
    from backend.app import main

    monkeypatch.setattr(main, "_docker_default_gateway_ipv4", lambda: "172.20.0.1")
    monkeypatch.delenv("AUTOML_LOCAL_DOCKER_COMPOSE", raising=False)
    assert not main._is_local_service_peer("172.20.0.1")

    monkeypatch.setenv("AUTOML_LOCAL_DOCKER_COMPOSE", "1")
    assert main._is_local_service_peer("172.20.0.1")
    assert not main._is_local_service_peer("172.20.0.2")
    assert not main._is_local_service_peer("203.0.113.10")


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
