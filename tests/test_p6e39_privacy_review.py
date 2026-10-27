"""P6E39: only column headers are inspected; reports never disclose row values."""
from io import BytesIO
import json
from zipfile import ZipFile
import pandas as pd
from pypdf import PdfReader

from backend.app.services.privacy_review import inspect_header_privacy, privacy_header_notice
from backend.app.services.basic_report import build_basic_zip


def test_header_hint_positive_negative_and_no_automatic_clearance():
    review = inspect_header_privacy(["고객_전화번호", "배송주소", "매출"])
    assert review["suspected_column_count"] == 2
    assert review["hint_categories"] == ["contact", "location"]
    assert review["source_values_inspected"] is False
    assert review["automatic_privacy_clearance"] is False
    assert review["manual_deidentification_review_required"] is True
    assert "배송주소" not in str(review)
    assert "비식별화 검수가 필요" in privacy_header_notice(review)
    missed = inspect_header_privacy(["매출", "방문수"])
    assert missed["suspected_column_count"] == 0
    assert missed["automatic_privacy_clearance"] is False
    assert "검증된 것은 아닙니다" in privacy_header_notice(missed)


def test_synthetic_basic_zip_readme_and_pdf_warning_have_no_source_record():
    df = pd.DataFrame({
        "전화번호": ["SYNTH-PRIVATE-ROW-" + str(i) for i in range(12)],
        "매출": list(range(12)),
    })
    with ZipFile(BytesIO(build_basic_zip(df))) as archive:
        summary = json.loads(archive.read("summary.json"))
        review = summary["privacy_review"]
        assert review["suspected_column_count"] == 1
        assert review["hint_categories"] == ["contact"]
        assert review["source_values_inspected"] is False
        notice = archive.read("README.txt").decode("utf-8")
        assert "의심 열 1개" in notice
        assert "SYNTH-PRIVATE-ROW" not in notice
        assert "SYNTH-PRIVATE-ROW" not in archive.read("summary.json").decode("utf-8")
        pdftext = "\n".join(p.extract_text() or "" for p in
                            PdfReader(BytesIO(archive.read("report.pdf"))).pages)
        assert "개인정보 주의" in pdftext
        assert "SYNTH-PRIVATE-ROW" not in pdftext
