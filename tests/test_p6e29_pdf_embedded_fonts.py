"""P6E29: verify README claims against actual PDF /FontDescriptor streams.

Actual PDF generation, no fake font file or customer data. An installed/selected
font is not necessarily *embedded*, and PDF Helvetica is not an embedded font.
"""
from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import pytest
from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate

from backend.app.services.font_coverage import (
    _font_embedded, embedded_pdf_font_names, font_usage_notice,
    resolve_report_fonts, safe_pdf_markup,
)
from backend.app.services.basic_report import build_basic_zip
from backend.app.services.standard_delivery import build_standard_zip
from backend.app.services.premium_delivery import build_premium_zip
import pandas as pd
from reportlab.pdfbase import pdfmetrics


def korean_frame() -> pd.DataFrame:
    n = 80
    return pd.DataFrame({
        "매출": [float(120 + i % 13 * 7) for i in range(n)],
        "방문": [i % 9 + 1 for i in range(n)],
        "고객유형": ["A", "B"] * (n // 2),
        "목표": [i % 2 for i in range(n)],
    })


def japanese_frame() -> pd.DataFrame:
    return korean_frame().rename(columns={"매출": "売上", "방문": "訪問数", "고객유형": "地域", "목표": "購入"})


def _tiny_report(text: str, font: str) -> bytes:
    out = BytesIO()
    doc = SimpleDocTemplate(out)
    doc.build([Paragraph(text, ParagraphStyle("probe", fontName=font))])
    return out.getvalue()


def test_selected_japanese_font_not_embedded_when_unused():
    primary, fallback = resolve_report_fonts("売上")
    assert fallback is not None
    pdf = _tiny_report("안녕하세요", primary)  # only Nanum; no Japanese markup
    names = embedded_pdf_font_names(pdf)
    assert _font_embedded(pdfmetrics.getFont(primary).face.name, names)
    assert "Helvetica" not in names  # PDF standard /Helvetica does not embed a font stream
    assert not _font_embedded(pdfmetrics.getFont(fallback).face.name, names)
    notice = font_usage_notice("売上", pdf_bytes=pdf)
    assert "보조 글꼴:" in notice
    assert "PDF 내장 없음" in notice
    assert notice.count("PDF 내장 서브셋 확인") == 1


def test_real_japanese_glyph_run_is_pdf_embedded_and_audited():
    primary, fallback = resolve_report_fonts("売上")
    assert fallback is not None
    pdf = _tiny_report(safe_pdf_markup("매출 売上", primary, fallback), primary)
    names = embedded_pdf_font_names(pdf)
    assert _font_embedded(pdfmetrics.getFont(primary).face.name, names)
    assert _font_embedded(pdfmetrics.getFont(fallback).face.name, names)
    assert font_usage_notice("売上", pdf_bytes=pdf).count("PDF 내장 서브셋 확인") == 2


def test_pdf_without_embedded_font_is_rejected():
    payload = _tiny_report("Hello", "Helvetica")  # standard Type1, no FontFile stream
    assert embedded_pdf_font_names(payload) == set()
    with pytest.raises(ValueError, match="no inspectable embedded"):
        font_usage_notice("매출", pdf_bytes=payload)


@pytest.mark.parametrize("tier", ["BASIC", "STANDARD", "PREMIUM"])
@pytest.mark.parametrize("japanese", [False, True])
def test_real_tier_pdf_embedded_streams_match_customer_readme(tier, japanese):
    frame = japanese_frame() if japanese else korean_frame()
    target = "購入" if japanese else "목표"
    if tier == "BASIC":
        packed = build_basic_zip(frame)
    elif tier == "STANDARD":
        packed = build_standard_zip(frame, target, "classification")
    else:
        packed = build_premium_zip(frame, target, "classification")
    with ZipFile(BytesIO(packed)) as archive:
        text = archive.read("README.txt").decode("utf-8")
        pdf = archive.read("report.pdf")
        names = embedded_pdf_font_names(pdf)
        assert names
        if tier == "PREMIUM":
            report_text = "\n".join(
                page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages
            )
            assert "1) 원본 발신자 확인" in report_text
            assert "[U+246" not in report_text
        assert text.count("PDF 내장 서브셋 확인") >= 1
        if japanese:
            assert text.count("PDF 내장 서브셋 확인") == 2, (tier, names, text)
            primary, fallback = resolve_report_fonts("売上")
            assert fallback is not None
            assert _font_embedded(pdfmetrics.getFont(primary).face.name, names)
            assert _font_embedded(pdfmetrics.getFont(fallback).face.name, names)
            # The environment may use AR PL UMing, MS Gothic, Meiryo, or
            # another supported local font. Check that the customer ZIP
            # reports the actual selected family and its matching caveat.
            for expected_line in font_usage_notice("売上").splitlines():
                if expected_line.startswith(("기본 글꼴:", "보조 글꼴:")):
                    family, license_notice = expected_line.split(" — ", 1)
                    assert family in text
                    assert license_notice in text
        else:
            assert text.count("PDF 내장 서브셋 확인") == 1
            assert "Arphic Public License" not in text
        assert "PDF 내장 없음" not in text
        assert "C:/Windows/Fonts" not in text
        assert "/usr/share/fonts/" not in text
        assert PdfReader(BytesIO(pdf)).pages
