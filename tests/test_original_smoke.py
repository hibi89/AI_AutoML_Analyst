"""Synthetic, customer-data-free smoke tests of the original FastAPI/AutoML paths."""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression, Ridge

from backend.app.main import app
from backend.app.services import storage
from backend.app.services.automl_runner import run_automl_experiment


def classification_frame(n: int = 60) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "visits": [1 + (i % 11) for i in range(n)],
            "group": ["A" if i % 3 else "B" for i in range(n)],
            "outcome": [i % 2 for i in range(n)],
        }
    )


def regression_frame(n: int = 60) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "quantity": [float(1 + (i % 17)) for i in range(n)],
            "segment": ["north" if i % 3 else "south" for i in range(n)],
            "revenue": [float(10 + 3 * (i % 17) + (i % 3)) for i in range(n)],
        }
    )


def test_original_classification_pipeline_runs() -> None:
    result = run_automl_experiment(
        classification_frame(),
        target_column="outcome",
        task_type="classification",
        model_candidates={"logistic_regression": LogisticRegression(max_iter=300)},
        cv=3,
    )
    assert result.task_type == "classification"
    assert result.results[0].status == "success", result.results[0].error
    assert result.results[0].cv_splits == 3
    assert result.best_result is not None


def test_original_regression_pipeline_runs() -> None:
    result = run_automl_experiment(
        regression_frame(),
        target_column="revenue",
        task_type="regression",
        model_candidates={"ridge": Ridge()},
        cv=3,
    )
    assert result.task_type == "regression"
    assert result.results[0].status == "success", result.results[0].error
    assert "mae" in result.results[0].metrics
    assert result.best_result is not None


def test_missing_target_rejected() -> None:
    with pytest.raises(ValueError, match="target_column"):
        run_automl_experiment(
            classification_frame(),
            target_column="does_not_exist",
            task_type="classification",
            model_candidates={"logistic_regression": LogisticRegression()},
            cv=3,
        )


def test_constant_target_cannot_produce_successful_logistic_model() -> None:
    data = classification_frame()
    data["outcome"] = 1
    # Baseline audit: the old code may return a failed model rather than
    # reject this invalid target up front. P2 must improve user-facing errors.
    result = run_automl_experiment(
        data,
        target_column="outcome",
        task_type="classification",
        model_candidates={"logistic_regression": LogisticRegression(max_iter=300)},
        cv=3,
    )
    assert result.best_result is None
    assert result.results[0].status == "failed"


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_original_csv_upload_and_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "EXPERIMENTS_DIR", tmp_path)
    client = TestClient(app)
    csv_bytes = classification_frame(36).to_csv(index=False).encode("utf-8")
    response = client.post(
        "/api/analyze",
        data={"target_column": "outcome", "task_type": "classification", "cv": "2"},
        files={"file": ("synthetic.csv", BytesIO(csv_bytes), "text/csv")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["dataset_info"]["rows"] == 36
    assert body["automl_result"]["task_type"] == "classification"
    assert any(item["status"] == "success" for item in body["automl_result"]["results"])
    job_id = body["job"]["job_id"]
    assert client.get(f"/api/results/{job_id}").status_code == 200
    report_response = client.get(f"/api/reports/{job_id}")
    assert report_response.status_code == 200
    assert report_response.text.strip()
