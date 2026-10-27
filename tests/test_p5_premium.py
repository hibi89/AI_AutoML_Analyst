"""P5 local PREMIUM model fit -> serialized bundle -> repeated prediction tests."""
from __future__ import annotations

from io import BytesIO, StringIO
import csv
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.app.main import app
from backend.app.services.premium_predict import predict_csv


def synthetic():
    n = 96
    return pd.DataFrame({
        "visits": [i % 17 + 1 for i in range(n)],
        "revenue": [float(5 + i % 17 * 2) for i in range(n)],
        "region": ["A", "B", "C"] * (n // 3),
        "target": [i % 2 for i in range(n)],
    })


@pytest.fixture(scope="module")
def bundle():
    df = synthetic()
    res = TestClient(app).post(
        "/api/premium-report",
        data={"target_column": "target", "task_type": "classification", "cv": "3"},
        files={"file": ("synthetic.csv", BytesIO(df.to_csv(index=False).encode()), "text/csv")},
    )
    assert res.status_code == 200, res.text
    return res.content


def test_premium_ui_local_guard():
    client = TestClient(app)
    assert client.get("/premium-mvp").status_code == 200
    assert client.get("/premium-mvp", headers={"host": "evil.example"}).status_code == 403


def test_premium_full_zip_and_five_challengers(bundle):
    with ZipFile(BytesIO(bundle)) as z:
        filenames = set(z.namelist())
        assert {"report.pdf", "model_pipeline.skops", "model_schema.json",
                "premium_summary.json", "model_scores.csv", "holdout_scores.csv", "predict.py",
                "predict.cmd", "sample_input.csv", "sample_predictions.csv",
                "requirements-premium.txt", "manifest.json"} <= filenames
        info = json.loads(z.read("premium_summary.json"))
        assert info["tier"] == "PREMIUM"
        assert info["challenger_budget"] == 5
        assert len(info["models"]) == 6
        assert len(info["tuning_experiments"]) >= 1
        assert len(info["tuning_experiments"]) <= 2
        assert "selected_hyperparameters" in info
        assert len([m for m in info["models"] if m["role"] == "baseline"]) == 1
        assert len([m for m in info["models"] if m["role"] == "challenger"]) == 5
        assert info["holdout_used_in_selection"] is False
        # PREMIUM's CV-selected evaluation is train-only; the delivered
        # holdout table must agree with the same ZIP's pre-refit summary.
        holdout_rows = list(csv.DictReader(StringIO(
            z.read("holdout_scores.csv").decode("utf-8-sig"))))
        assert len(holdout_rows) == len(info["selected_holdout_metrics"])
        assert {row["metric"] for row in holdout_rows} == set(info["selected_holdout_metrics"])
        for row in holdout_rows:
            metric = row["metric"]
            assert row["selected_model"] == info["selected_model"]
            assert row["dummy_model"] == info["dummy_model"]
            assert float(row["selected_holdout"]) == pytest.approx(info["selected_holdout_metrics"][metric])
            assert float(row["dummy_holdout"]) == pytest.approx(info["dummy_holdout_metrics"][metric])
            assert float(row["selected_minus_dummy"]) == pytest.approx(
                info["selected_holdout_metrics"][metric] - info["dummy_holdout_metrics"][metric])
            assert row["primary_holdout_beats_dummy"] == ("yes" if info["holdout_beats_dummy"] else "no")
            assert row["selection_basis"] == "selected_by_training_cv_only"
        assert ("feature_importance.csv" in filenames) == bool(
            info["training_feature_importance"])
        pages = PdfReader(BytesIO(z.read("report.pdf"))).pages
        cover = pages[0].extract_text() or ""
        assert "PREMIUM" in cover
        assert "EXPLORATORY DATA SECTION" in cover
        assert "BASIC  /  EXPLORATORY" not in cover
        assert "모델 학습 및 검증 결과는 뒤의 ML 평가 섹션" in cover
        assert 10 <= len(pages) <= 15
        # Shared STANDARD ML pages must be relabeled for the PREMIUM delivery.
        ml_pages = " ".join(page.extract_text() or "" for page in pages[-5:-2])
        assert "PREMIUM — 모델 학습 및 검증" in ml_pages
        assert "AI AutoML Analyst  |  PREMIUM 모델 검증" in ml_pages
        assert "STANDARD 모델 검증" not in ml_pages
        assert "STANDARD — 모델 학습 및 검증" not in ml_pages
        assert "선택 모델 - Dummy 차이:" in ml_pages
        assert "[U+2212]" not in ml_pages
        if not info["holdout_beats_dummy"]:
            assert "예측 성능 우위가 입증되지 않았습니다." in ml_pages
        # P6E handover stays on two substantive pages without overflow/blank spill.
        handover = pages[-2].extract_text() or ""
        schema_guide = pages[-1].extract_text() or ""
        assert "모델 검증 스냅샷" in handover
        assert "독립 검증 점수" in handover
        assert "새 CSV로 예측하기" in handover
        assert "입력 계약 요약" in schema_guide
        assert "필수 열 미리보기" in schema_guide
        assert "model_schema.json" in schema_guide
        schema = json.loads(z.read("model_schema.json"))
        assert schema["raw_feature_columns"] == ["visits", "revenue", "region"]
        assert schema["selected_hyperparameters"] == info["selected_hyperparameters"]
        assert b"\x80\x04" not in z.read("model_pipeline.skops")[:2]
        assert z.read("sample_input.csv").decode("utf-8-sig").strip() == "visits,revenue,region"
        assert z.read("sample_predictions.csv") == b"prediction\r\n"
        import hashlib
        entries = json.loads(z.read("manifest.json"))["files"]
        assert all(hashlib.sha256(z.read(e["path"])).hexdigest() == e["sha256"] for e in entries)


def test_premium_prediction_and_schema_checks(bundle, tmp_path):
    with ZipFile(BytesIO(bundle)) as z:
        for name in ("model_pipeline.skops", "model_schema.json"):
            (tmp_path / name).write_bytes(z.read(name))
    raw = synthetic().drop(columns=["target"]).iloc[:6]
    incoming = tmp_path / "new_data.csv"
    outgoing = tmp_path / "predictions.csv"
    raw.to_csv(incoming, index=False)
    count = predict_csv(tmp_path, incoming, outgoing)
    assert count == 6
    pred = pd.read_csv(outgoing)
    assert len(pred) == count
    assert list(pred.columns) == ["prediction"]
    with pytest.raises(ValueError, match="Output path exists"):
        predict_csv(tmp_path, incoming, outgoing)

    wrong = tmp_path / "wrong.csv"
    raw[["region", "revenue", "visits"]].to_csv(wrong, index=False)
    with pytest.raises(ValueError, match="header mismatch"):
        predict_csv(tmp_path, wrong, tmp_path / "wrong_out.csv")

    model_path = tmp_path / "model_pipeline.skops"
    model_path.write_bytes(model_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        predict_csv(tmp_path, incoming, tmp_path / "after_tampering.csv")


def test_premium_input_requires_target_semantics():
    df = synthetic()
    res = TestClient(app).post(
        "/api/premium-report",
        data={"target_column": "target", "task_type": "auto"},
        files={"file": ("synthetic.csv", BytesIO(df.to_csv(index=False).encode()), "text/csv")},
    )
    assert res.status_code == 400
    assert "Ambiguous numeric" in res.text
