"""BASIC frozen-spec gap: explain ML feasibility without fitting or exposing row values."""
from __future__ import annotations

from io import BytesIO
import json
from zipfile import ZipFile

import pandas as pd
from pypdf import PdfReader

from backend.app.services.ml_feasibility import inspect_ml_feasibility
from backend.app.services.basic_report import build_basic_zip


def synthetic_business_frame() -> pd.DataFrame:
    n = 96
    return pd.DataFrame({
        "고객번호": [f"private-person-{i:03d}" for i in range(n)],
        "날짜": pd.date_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "매출": [100 + i * 3.12 for i in range(n)],
        "이탈": [i % 2 for i in range(n)],
        "방문횟수": [1 + (i % 9) for i in range(n)],
        "메모": [f"SECRET_RAW_NOTE_{i:03d}" for i in range(n)],
    })


def test_no_model_fit_no_raw_values_and_ambiguous_numeric_target():
    frame = synthetic_business_frame()
    report = inspect_ml_feasibility(frame)
    assert report["model_fitted"] is False
    assert report["target_confirmed"] is False
    assert report["excluded_column_counts"]["identifier_or_date"] == 2
    assert [item["column"] for item in report["candidates"]][:2] == ["매출", "이탈"]
    by_name = {item["column"]: item for item in report["candidates"]}
    assert by_name["이탈"]["inspection_type"] == "모호한 수치형"
    assert by_name["매출"]["inspection_type"] == "수치형"
    assert any("분류/회귀" in caution for caution in report["constraints"])
    assert not any("private-person" in json.dumps(report) or
                   "SECRET_RAW_NOTE_" in json.dumps(report) for _ in [1])
    assert len(report["requested_information"]) == 3


def test_non_predictive_sparse_dataset_has_no_guaranteed_target():
    frame = pd.DataFrame({
        "식별자": ["A", "B", "C"],
        "상태": ["완료", "완료", "완료"],
    })
    result = inspect_ml_feasibility(frame)
    assert result["candidates"] == []
    assert result["model_fitted"] is False
    assert any("추가" in msg for msg in result["constraints"])


def test_boolean_and_text_category_are_only_review_prompts():
    frame = pd.DataFrame({
        "refund": [i % 2 == 0 for i in range(40)],
        "region": ["N", "S"] * 20,
    })
    hints = inspect_ml_feasibility(frame)
    kinds = {r["column"]: r["inspection_type"] for r in hints["candidates"]}
    assert kinds["refund"] == "이진형"
    assert kinds["region"] == "범주형"
    assert not hints["target_confirmed"]


def test_actual_basic_zip_contains_candidate_caveats_not_model_results():
    frame = synthetic_business_frame()
    with ZipFile(BytesIO(build_basic_zip(frame))) as archive:
        summary = json.loads(archive.read("summary.json"))
        hints = summary["ml_feasibility"]
        assert hints["model_fitted"] is False
        assert "매출" in [x["column"] for x in hints["candidates"]]
        assert "이탈" in [x["column"] for x in hints["candidates"]]
        assert "model_pipeline.skops" not in archive.namelist()
        pdf = PdfReader(BytesIO(archive.read("report.pdf")))
        content = "\n".join(page.extract_text() or "" for page in pdf.pages)
        assert "업무 목표 확인용 열 후보" in content
        assert "매출" in content and "이탈" in content
        assert "SECRET_RAW_NOTE_" not in content
        assert not any("SECRET_RAW_NOTE_" in archive.read(name).decode("utf-8", "ignore")
                       for name in ["summary.json", "README.txt", "summary.csv"])
