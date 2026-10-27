"""P6E19: deterministic CSV encoding selection for commercial tier imports.

All rows synthetic. No customer data, models, network or font binaries.
"""
from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from backend.app.main import _read_csv_from_bytes, app
from backend.app.services.tabular_input import read_uploaded_table


def test_explicit_cp932_preserves_real_japanese_columns_and_values():
    payload = "日付,売上,購入\n2026-01-01,120,1\n2026-01-02,95,0\n".encode("cp932")
    parsed = read_uploaded_table(payload, "shop.csv", csv_encoding="cp932")
    assert list(parsed.columns) == ["日付", "売上", "購入"]
    assert list(parsed["購入"]) == [1, 0]
    assert list(parsed["売上"]) == [120, 95]


def test_cp949_and_utf8_legacy_inputs_unchanged():
    for codec in ("cp949", "utf-8-sig"):
        payload = "날짜,매출,구매\n2026-01-01,20,1\n2026-01-02,10,0\n".encode(codec)
        auto = _read_csv_from_bytes(payload)
        selected = _read_csv_from_bytes(payload, encoding=codec)
        assert list(auto.columns) == ["날짜", "매출", "구매"]
        assert auto.equals(selected)


def test_unsupported_explicit_encoding_fails_closed():
    with pytest.raises(ValueError, match="Unsupported CSV encoding selection"):
        _read_csv_from_bytes(b"x,y\n1,2\n", encoding="unicode_escape")


def test_raw_duplicate_japanese_headers_rejected_in_explicit_cp932():
    payload = "売上,売上\n1,2\n".encode("cp932")
    with pytest.raises(ValueError, match="Duplicate column names"):
        read_uploaded_table(payload, "dup.csv", csv_encoding="cp932")


@pytest.mark.parametrize("route,extra", [
    ("/api/basic-report", {}),
    ("/api/standard-report", {"target_column": "購入", "task_type": "classification"}),
    ("/api/premium-report", {"target_column": "購入", "task_type": "classification"}),
])
def test_each_local_tier_receives_explicit_cp932_without_mojibake(route, extra, monkeypatch):
    """Check POST form passes encoding through shared ingestion to each tier."""
    import backend.app.services.basic_report as basic
    import backend.app.services.standard_delivery as standard
    import backend.app.services.premium_delivery as premium

    checks = []

    def sample_builder(frame, *args, **kwargs):
        checks.append(list(frame.columns))
        return b"synthetic-zip-placeholder"

    monkeypatch.setattr(basic, "build_basic_zip", sample_builder)
    monkeypatch.setattr(standard, "build_standard_zip", sample_builder)
    monkeypatch.setattr(premium, "build_premium_zip", sample_builder)
    payload = ("日付,売上,購入\n" +
               "\n".join(f"2026-01-{i:02d},{100 + i},{i % 2}" for i in range(1, 21))
               ).encode("cp932")
    response = TestClient(app).post(
        route,
        data={**extra, "csv_encoding": "cp932"},
        files={"file": ("synthetic.csv", BytesIO(payload), "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert checks == [["日付", "売上", "購入"]]


@pytest.mark.parametrize("route,extra", [
    ("/api/basic-report", {}),
    ("/api/standard-report", {"target_column": "target"}),
    ("/api/premium-report", {"target_column": "target"}),
])
def test_invalid_encoding_form_returns_400(route, extra):
    response = TestClient(app).post(
        route,
        data={**extra, "csv_encoding": "utf-7"},
        files={"file": ("synthetic.csv", BytesIO(b"a,target\n1,0\n"), "text/csv")},
    )
    assert response.status_code == 400
    assert "Unsupported CSV encoding selection" in response.text


@pytest.mark.parametrize("page", ["/basic-mvp", "/standard-mvp", "/premium-mvp"])
def test_local_web_pages_offer_explicit_cp932_with_safe_default(page):
    response = TestClient(app).get(page)
    assert response.status_code == 200
    assert 'name="csv_encoding"' in response.text
    assert 'value="auto"' in response.text
    assert 'value="cp932"' in response.text
