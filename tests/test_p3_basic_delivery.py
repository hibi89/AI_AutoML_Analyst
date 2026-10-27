"""Commercial BASIC PDF/ZIP acceptance tests using synthetic local-only inputs."""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

import pandas as pd
from fastapi.testclient import TestClient
from pypdf import PdfReader
from PIL import Image
import pytest

from backend.app.main import app
from backend.app.services.basic_report import build_basic_zip


def rich_frame() -> pd.DataFrame:
    n = 150
    records = pd.DataFrame({
        "날짜": pd.date_range("2026-01-01", periods=n, freq="D").strftime("%Y-%m-%d"),
        "지역": ["서울", "부산", "대전"] * 50,
        "방문수": [20 + (i % 23) * 3 for i in range(n)],
        "매출": [150 + (i % 23) * 8 + (i % 4) for i in range(n)],
        "원가": [90 + (i % 23) * 4 + (i % 7) for i in range(n)],
    })
    records.loc[10:25, "지역"] = None
    records.loc[4:13, "매출"] = float("nan")
    return records


def test_rich_input_produces_real_korean_pdf_five_charts_and_manifest(tmp_path):
    raw = rich_frame()
    payload = build_basic_zip(raw)
    with ZipFile(BytesIO(payload)) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        assert {"report.pdf", "summary.csv", "summary.json", "README.txt", "manifest.json"} <= set(names)
        charts = sorted(n for n in names if n.startswith("charts/"))
        assert len(charts) == 5, charts
        for name in charts:
            assert z.read(name).startswith(b"\\x89PNG".decode("unicode_escape").encode("latin1"))
        summary = json.loads(z.read("summary.json"))
        assert summary["rows"] == 150
        assert summary["columns"] == 5
        assert summary["chart_count"] == 5
        profiles = summary["numeric_profiles"]
        assert 1 <= len(profiles) <= 4
        assert all(item["observed"] >= 4 for item in profiles)
        for item in profiles:
            expected = pd.to_numeric(raw[item["column"]], errors="coerce").dropna()
            assert item["median"] == round(float(expected.median()), 2)
            assert item["q1"] == round(float(expected.quantile(.25)), 2)
            assert item["q3"] == round(float(expected.quantile(.75)), 2)
        assert 5 <= len(summary["metrics"]) <= 10
        assert 3 <= len(summary["findings"]) <= 5
        assert len(summary["suggestions"]) <= 3
        assert summary["missing_cells"] == int(raw.isna().sum().sum())
        assert summary["duplicate_rows"] == int(raw.duplicated().sum())
        assert "서울" not in z.read("README.txt").decode("utf-8")
        manifest = json.loads(z.read("manifest.json"))
        assert manifest["no_raw_dataset"] is True
        for item in manifest["files"]:
            blob = z.read(item["path"])
            assert len(blob) == item["bytes"]
            assert hashlib.sha256(blob).hexdigest() == item["sha256"]
        assert not any("source" in n.lower() or n.endswith("original.csv") for n in names)

        pdf = z.read("report.pdf")
        assert pdf.startswith(b"%PDF-")
        reader = PdfReader(BytesIO(pdf))
        assert 6 <= len(reader.pages) <= 8, len(reader.pages)
        searchable = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert "BASIC" in (reader.pages[0].extract_text() or "")
        assert "EXPLORATORY DATA REPORT" in (reader.pages[0].extract_text() or "")
        assert "데이터 진단" in searchable
        assert "주요 발견" in searchable
        assert "ML 적용 가능성" in searchable
        assert "목표열 검토 전 확인할 수치형 현황" in (reader.pages[-1].extract_text() or "")
        # Only the final lone-chart page receives real numeric quartile content.
        assert "관측 수치의 사분위 요약" in (reader.pages[-2].extract_text() or "")
        assert "사분위 요약" not in (reader.pages[0].extract_text() or "")
        assert "인과관계" in searchable

        path = tmp_path / "report.pdf"
        path.write_bytes(pdf)
        result = subprocess.run(
            ["pdftoppm", "-f", "1", "-l", "1", "-scale-to", "950", "-singlefile",
             "-png", str(path), str(tmp_path / "cover")],
            check=True, capture_output=True, timeout=25,
        )
        png = tmp_path / "cover.png"
        assert png.stat().st_size > 15_000
        with Image.open(png) as cover:
            assert cover.size[0] > 500
            # Content is not an empty/white raster.
            colors = cover.convert("RGB").getcolors(maxcolors=20_000)
            assert colors is None or len(colors) > 80



def test_outlier_signal_contract_and_no_false_zero_for_flat_iqr():
    from backend.app.services.basic_p3 import _outlier_signals
    data = pd.DataFrame({
        "매출": list(range(1, 12)) + [100],
        "고정값": [2] * 12,
        "라벨": ["A", "B"] * 6,
    })
    flagged = {item["column"]: item for item in _outlier_signals(data)}
    assert flagged["매출"]["iqr_status"] == "observed_signal"
    assert flagged["매출"]["iqr_outliers"] == 1
    assert flagged["고정값"]["iqr_outliers"] is None
    assert flagged["고정값"]["iqr_status"] == "insufficient_data"
    assert "라벨" not in flagged
    plateau = _outlier_signals(pd.DataFrame({"가격": [2] * 20 + [100]}))[0]
    assert plateau["iqr_status"] == "flat_iqr"
    assert plateau["iqr_outliers"] is None


def test_zip_json_csv_and_pdf_expose_qualified_outlier_diagnostics():
    source = pd.DataFrame({
        "수치": list(range(1, 12)) + [100],
        "라벨": ["A", "B"] * 6,
    })
    with ZipFile(BytesIO(build_basic_zip(source))) as archive:
        summary = json.loads(archive.read("summary.json"))
        assert summary["outlier_signals"][0]["column"] == "수치"
        assert summary["outlier_signals"][0]["iqr_outliers"] == 1
        assert summary["numeric_profiles"][0]["iqr_outliers"] == 1
        csv_data = archive.read("summary.csv").decode("utf-8-sig")
        assert "iqr_outliers" in csv_data
        assert "observed_signal" in csv_data
        pages = PdfReader(BytesIO(archive.read("report.pdf"))).pages
        searchable = "\n".join(page.extract_text() or "" for page in pages)
        assert "IQR 밖" in searchable
        assert "오류 판정" in searchable


def test_long_numeric_headers_remain_exact_in_json_and_pdf_quality_lookup():
    # Headers >48 characters were previously truncated by _numeric_profiles
    # while PDF quality lookup relied on that truncation. Preserve one exact
    # key for both machine-readable statistics and human-readable reports.
    long_name = "월별매출_" + "데이터" * 15
    source = pd.DataFrame({
        long_name: list(range(1, 12)) + [100],
        "구분": ["A", "B"] * 6,
    })
    with ZipFile(BytesIO(build_basic_zip(source))) as archive:
        summary = json.loads(archive.read("summary.json"))
        assert summary["numeric_profiles"][0]["column"] == long_name
        assert summary["outlier_signals"][0]["column"] == long_name
        assert summary["quality"][0]["column"] == long_name
        text = "\n".join(page.extract_text() or "" for page in
                         PdfReader(BytesIO(archive.read("report.pdf"))).pages)
        assert "고유값" in text


def test_sparse_dataset_avoids_filler_charts_and_nonexistent_claims():
    df = pd.DataFrame({"식별자": ["A", "B", "C"], "상태": ["완료", "완료", "완료"]})
    with ZipFile(BytesIO(build_basic_zip(df))) as z:
        summary = json.loads(z.read("summary.json"))
        assert summary["chart_count"] == 0
        assert not any(n.startswith("charts/") for n in z.namelist())
        assert len(PdfReader(BytesIO(z.read("report.pdf"))).pages) < 6
        assert summary["missing_cells"] == 0
        assert summary["duplicate_rows"] == 0


def test_blank_csv_and_empty_columns_rejected():
    from backend.app.services.basic_report import validate_basic_frame
    with pytest.raises(ValueError, match="no usable"):
        validate_basic_frame(pd.DataFrame(columns=["x"]))
    with pytest.raises(ValueError, match="Duplicate"):
        validate_basic_frame(pd.DataFrame([[1, 2]], columns=["x", "x"]))



@pytest.mark.parametrize("infinite_value", [float("inf"), float("-inf")])
def test_infinite_numeric_csv_is_rejected_consistently_before_all_sku_reports(infinite_value):
    """A single +/-Infinity currently makes the numeric histogram fail.

    The shared validation boundary must produce a controlled HTTP 400 rather
    than an unhandled chart/ML error for any of the three customer SKUs.
    """
    from backend.app.services.basic_report import validate_basic_frame

    raw = rich_frame().head(24).copy()
    raw.loc[0, "방문수"] = infinite_value

    with pytest.raises(ValueError, match="infinite numeric values"):
        validate_basic_frame(raw)

    csv_bytes = raw.to_csv(index=False).encode("utf-8-sig")
    client = TestClient(app)
    for endpoint, form in (
        ("/api/basic-report", {}),
        ("/api/standard-report", {"target_column": "매출", "task_type": "regression"}),
        ("/api/premium-report", {"target_column": "매출", "task_type": "regression"}),
    ):
        response = client.post(
            endpoint, data=form,
            files={"file": ("synthetic.csv", BytesIO(csv_bytes), "text/csv")},
        )
        assert response.status_code == 400, (endpoint, response.status_code, response.text)
        assert "infinite numeric values" in response.json()["detail"]


def test_missing_numeric_cells_are_still_allowed_by_infinity_guard():
    """Missing values are handled by diagnostics and must not be rejected."""
    from backend.app.services.basic_report import validate_basic_frame

    raw = rich_frame().head(24).copy()
    raw.loc[0, "방문수"] = float("nan")
    validate_basic_frame(raw)

def test_csv_formula_escape_and_header_preservation():
    df = pd.DataFrame({"=HYPERLINK(1)": [1,2,3,4,5,6,7,8,9],
                       "매출": [1,2,3,4,5,6,7,8,9]})
    with ZipFile(BytesIO(build_basic_zip(df))) as z:
        assert "'=HYPERLINK(1)" in z.read("summary.csv").decode("utf-8-sig")


def test_http_korean_utf8_csv_delivery():
    df = rich_frame().head(80)
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("sample.csv", BytesIO(df.to_csv(index=False).encode("utf-8-sig")), "text/csv")},
    )
    assert response.status_code == 200, response.text
    with ZipFile(BytesIO(response.content)) as z:
        assert "report.pdf" in z.namelist()
        summary = json.loads(z.read("summary.json"))
        assert summary["rows"] == 80


def test_http_korean_cp949_csv_delivery():
    df = rich_frame().head(40)
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("sample.csv", BytesIO(df.to_csv(index=False).encode("cp949")), "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert ZipFile(BytesIO(response.content)).testzip() is None
