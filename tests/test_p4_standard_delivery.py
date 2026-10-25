"""STANDARD P4 controlled synthetic evaluation tests."""
from __future__ import annotations

import json
from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.app.main import app
from backend.app.services.standard_engine import run_standard


def frame(n=120, regression=False):
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "group_id": [f"G{i//6:02d}" for i in range(n)],
        "visits": [i % 17 + 1 for i in range(n)],
        "amount": [float(15 + 3 * (i % 17) + (i % 3)) for i in range(n)],
        "segment": ["A", "B", "C"] * (n // 3),
        "target": [i % 2 for i in range(n)],
    })
    if regression:
        df["target"] = [float(10 + 4 * (i % 17) + (i % 3)) for i in range(n)]
    return df


def test_local_standard_html():
    client = TestClient(app)
    assert "STANDARD" in client.get("/standard-mvp").text
    assert client.get("/standard-mvp", headers={"host":"remote.test"}).status_code == 403


def test_standard_real_http_pdf_zip():
    df = frame()
    resp = TestClient(app).post(
        "/api/standard-report",
        data={"target_column":"target","task_type":"classification","cv":"3"},
        files={"file":("synthetic.csv", BytesIO(df.to_csv(index=False).encode()), "text/csv")},
    )
    assert resp.status_code == 200, resp.text
    with ZipFile(BytesIO(resp.content)) as z:
        assert {"report.pdf", "model_scores.csv", "standard_summary.json",
                "summary.csv", "manifest.json", "charts/06_ml_comparison.png"} <= set(z.namelist())
        x = json.loads(z.read("standard_summary.json"))
        assert x["train_rows"] + x["holdout_rows"] == 120
        assert x["holdout_used_in_selection"] is False
        assert len(x["models"]) == 4
        assert sum(v["role"] == "baseline" for v in x["models"]) == 1
        assert sum(v["role"] == "challenger" for v in x["models"]) == 3
        assert "f1_weighted" in x["selected_holdout_metrics"]
        assert "train_original_indices" not in x
        reader = PdfReader(BytesIO(z.read("report.pdf")))
        assert 8 <= len(reader.pages) <= 12
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        assert "독립 검증 및 해석" in text
        assert "모델 비교 결과" in text


def test_standard_regression_direct():
    x = run_standard(frame(regression=True), "target", "regression")
    assert x["primary_metric"] == "r2"
    assert x["dummy_model"] == "dummy_regressor"
    assert "rmse" in x["selected_holdout_metrics"]


def test_group_cv_disjoint():
    x = run_standard(frame(), "target", "classification",
                     split_policy="group", group_column="group_id")
    assert set(x["train_group_values"]).isdisjoint(set(x["holdout_group_values"]))
    assert x["cv_splits"] == 3


def test_time_cv_chronological():
    x = run_standard(frame(), "target", "classification",
                     split_policy="time", time_column="date")
    assert max(x["train_original_indices"]) < min(x["holdout_original_indices"])
    assert x["cv_splits"] == 3


@pytest.mark.parametrize("kwargs", [
    {"task_type":None},
    {"task_type":"classification","split_policy":"group"},
    {"task_type":"classification","split_policy":"time"},
    {"task_type":"classification","split_policy":"bad"},
])
def test_invalid_split_or_ambiguous_target(kwargs):
    with pytest.raises(ValueError):
        run_standard(frame(), "target", **kwargs)


def test_constant_target_rejected():
    df = frame()
    df["target"] = 1
    with pytest.raises(ValueError, match="distinct"):
        run_standard(df, "target", "classification")


def test_too_few_groups_rejected():
    df = frame()
    df["group_id"] = ["A"] * 60 + ["B"] * 60
    with pytest.raises(ValueError, match="5 distinct"):
        run_standard(df, "target", "classification", "group", group_column="group_id")
