"""P6E27: verify real Japanese glyphs in PDF and PNG, not just CP932 decoding.

Synthetic-only. Actual font files come from preinstalled system/runner packages;
no binaries or private customer strings are committed.
"""
from __future__ import annotations

from io import BytesIO
import json
import warnings
from zipfile import ZipFile

import pandas as pd
import pytest
from pypdf import PdfReader

from backend.app.services.font_coverage import (
    resolve_report_fonts, safe_pdf_markup, _has_glyph,
)
from backend.app.services.basic_report import build_basic_zip


def japanese_frame() -> pd.DataFrame:
    n = 120
    return pd.DataFrame({
        "日付": pd.date_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "地域": ["A", "B", "C"] * (n // 3),
        "訪問数": [20 + i % 17 for i in range(n)],
        "売上": [100 + i % 23 * 2 for i in range(n)],
        "費用": [60 + i % 19 for i in range(n)],
        "購入": [i % 2 for i in range(n)],
    })


def test_missing_nanum_kanji_gets_real_local_fallback_and_markup():
    font, fallback = resolve_report_fonts("売上訪問数")
    assert fallback is not None, "CI must install a Japanese TrueType font"
    assert not _has_glyph(font, "売")
    assert not _has_glyph(font, "数")
    assert _has_glyph(fallback, "売") and _has_glyph(fallback, "数")
    marked = safe_pdf_markup("매출 & 売上", font, fallback)
    assert "&amp;" in marked
    assert '<font name="' in marked
    assert "売" in marked


def test_no_local_fallback_rejects_missing_glyphs_without_tofu(monkeypatch):
    from backend.app.services import font_coverage
    monkeypatch.setattr(font_coverage, "_japanese_path", lambda: None)
    with pytest.raises(ValueError, match="Japanese/Unicode report font"):
        font_coverage.resolve_report_fonts("売上")
    # Ordinary Korean-only reports retain their original font.
    primary, fallback = font_coverage.resolve_report_fonts("데이터 보고서")
    assert primary.startswith("AutoMLKorean")
    assert fallback is None


def test_real_japanese_report_pdf_and_chart_warns_no_missing_glyph():
    df = japanese_frame()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        payload = build_basic_zip(df)
    missing = [str(item.message) for item in caught if "Glyph " in str(item.message)
               and "missing from font" in str(item.message)]
    assert missing == [], missing

    with ZipFile(BytesIO(payload)) as archive:
        assert archive.testzip() is None
        summary = json.loads(archive.read("summary.json"))
        assert {x["column"] for x in summary["quality"]} == set(df.columns)
        pdf = PdfReader(BytesIO(archive.read("report.pdf")))
        extracted = "\n".join(page.extract_text() or "" for page in pdf.pages)
        assert "売上" in extracted
        assert "訪問数" in extracted
        assert "데이터 진단" in extracted
        assert any(x.endswith(".png") for x in archive.namelist())


def test_html_metacharacters_in_customer_header_remain_literal():
    font, fallback = resolve_report_fonts("売")
    marked = safe_pdf_markup("売 & <script>", font, fallback)
    assert "&amp;" in marked and "&lt;" in marked and "&gt;" in marked
    assert "<script>" not in marked
