"""P6E34 synthetic tests for pre-parser HTTP upload-envelope limits."""
from __future__ import annotations

import asyncio
from io import BytesIO

from fastapi.testclient import TestClient

from backend.app import upload_guard
from backend.app.main import app


def test_normal_multipart_reaches_existing_report_builder(monkeypatch):
    from backend.app.services import basic_report
    monkeypatch.setattr(basic_report, "build_basic_zip", lambda df: b"fake-test-zip")
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("synthetic.csv", BytesIO(b"x,y\n1,2\n3,4\n"), "text/csv")},
    )
    assert response.status_code == 200
    assert response.content == b"fake-test-zip"


def test_oversized_multipart_content_length_rejected(monkeypatch):
    monkeypatch.setattr(upload_guard, "MAX_MULTIPART_BODY_BYTES", 400)
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("synthetic.csv", BytesIO(b"x,y\n" + b"1,2\n" * 150), "text/csv")},
    )
    assert response.status_code == 413
    assert "synthetic.csv" not in response.text


def test_chunked_body_without_content_length_is_stopped(monkeypatch):
    monkeypatch.setattr(upload_guard, "MAX_MULTIPART_BODY_BYTES", 5)
    messages = [
        {"type": "http.request", "body": b"abcd", "more_body": True},
        {"type": "http.request", "body": b"efgh", "more_body": False},
    ]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    async def reader(scope, receive, send):
        while True:
            item = await receive()
            if not item.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    scope = {
        "type": "http", "method": "POST", "path": "/api/standard-report",
        "headers": [(b"content-type", b"multipart/form-data; boundary=x")],
    }
    asyncio.run(upload_guard.UploadEnvelopeLimit(reader)(scope, receive, send))
    assert sent[0]["status"] == 413
    assert not messages


def test_duplicate_or_malformed_content_length_rejected_early():
    async def should_not_run(*args):
        raise AssertionError("Header rejection must precede upload parsing")

    async def should_not_receive():
        raise AssertionError("Header rejection must precede body receive")

    for headers in [
        [(b"content-length", b"5"), (b"content-length", b"6")],
        [(b"content-length", b"not-a-number")],
    ]:
        sent = []

        async def send(message):
            sent.append(message)

        scope = {"type": "http", "method": "POST", "path": "/api/premium-report",
                 "headers": headers}
        asyncio.run(upload_guard.UploadEnvelopeLimit(should_not_run)(
            scope, should_not_receive, send
        ))
        assert sent[0]["status"] == 400


def test_non_upload_route_unaffected_by_upload_budget(monkeypatch):
    monkeypatch.setattr(upload_guard, "MAX_MULTIPART_BODY_BYTES", 1)
    assert TestClient(app).get("/health").status_code == 200
