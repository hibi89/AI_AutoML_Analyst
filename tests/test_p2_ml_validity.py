"""P2 AutoML target semantics / model budget / CV invariants; synthetic only."""
from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression, Ridge

from backend.app.main import app
from backend.app.services.automl_runner import run_automl_experiment
from backend.app.services.model_selector import select_model_candidates
from backend.app.services.task_detector import detect_task
from backend.app.services.trainer import _make_cv


def make_frame(target):
    return pd.DataFrame({
        "visits": [float(i % 12) for i in range(len(target))],
        "region": ["east" if i % 2 else "west" for i in range(len(target))],
        "label": target,
    })


@pytest.mark.parametrize("values", [
    [0, 1] * 25,
    [i % 9 for i in range(54)],
])
def test_ambiguous_numeric_auto_requires_semantics(values):
    frame = make_frame(values)
    with pytest.raises(ValueError, match="Ambiguous numeric"):
        run_automl_experiment(frame, "label", cv=3)


def test_explicit_numeric_binary_classification_runs():
    frame = make_frame([0, 1] * 30)
    result = run_automl_experiment(
        frame, "label", task_type="classification",
        model_candidates={"logistic": LogisticRegression(max_iter=300)}, cv=3,
    )
    assert result.task_detection["task_type_source"] == "explicit"
    assert result.results[0].status == "success", result.results[0].error


def test_explicit_numeric_discrete_regression_runs():
    frame = make_frame([float(i % 9) for i in range(54)])
    result = run_automl_experiment(
        frame, "label", task_type="regression",
        model_candidates={"ridge": Ridge()}, cv=3,
    )
    assert result.task_type == "regression"
    assert result.results[0].status == "success", result.results[0].error


def test_non_numeric_multiclass_auto_detection():
    frame = make_frame(["alpha", "beta", "gamma"] * 20)
    result = detect_task(frame, "label")
    assert result["task_type"] == "classification"
    assert result["subtype"] == "multiclass_classification"
    assert result["task_type_source"] == "inferred_unambiguous"


def test_continuous_numeric_auto_detection_regression():
    frame = make_frame([float(i + i / 31) for i in range(60)])
    result = detect_task(frame, "label")
    assert result["task_type"] == "regression"


def test_boolean_target_auto_classification():
    frame = make_frame([i % 2 == 0 for i in range(60)])
    assert detect_task(frame, "label")["task_type"] == "classification"


@pytest.mark.parametrize("target", [
    [1] * 60,
    [0] * 59 + [1],
])
def test_constant_and_rare_target_raise_before_fit(target):
    with pytest.raises(ValueError, match="distinct|rare class"):
        run_automl_experiment(make_frame(target), "label", task_type="classification")


def test_missing_target_rejected():
    with pytest.raises(ValueError, match="target_column"):
        detect_task(make_frame([0, 1] * 20), "missing")


def test_non_numeric_regression_rejected():
    with pytest.raises(ValueError, match="requires a numeric"):
        detect_task(make_frame(["yes", "no"] * 25), "label", "regression")


def test_cv_does_not_fallback_to_kfold_for_rare_classes():
    with pytest.raises(ValueError, match="rare classes"):
        _make_cv(pd.Series([0] * 9 + [1]), "classification", 5, 42)


def test_regression_cv_keeps_two_test_rows_minimum():
    _, n_splits = _make_cv(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), "regression", 5, 42)
    assert n_splits == 2
    with pytest.raises(ValueError, match="at least 4"):
        _make_cv(pd.Series([1.0, 2.0, 3.0]), "regression", 5, 42)


@pytest.mark.parametrize("task", ["classification", "regression"])
@pytest.mark.parametrize("budget", [3, 5])
def test_model_budget_dummy_separate_and_diverse(task, budget):
    sel = select_model_candidates(
        task, n_rows=100, n_features=4, has_categorical_features=False,
        max_models=budget,
    )
    payload = sel.to_dict()
    names = payload["challenger_model_names"]
    assert len(names) == budget
    assert len(sel.models) == budget + 1
    assert len(set(names)) == budget
    assert payload["baseline_model_name"].startswith("dummy_")
    assert not any(n.startswith("dummy_") for n in names)
    assert payload["policy"]["dummy_baseline_in_budget"] is False
    assert any("random_forest" in n for n in names)
    if budget == 3:
        assert any("hist_gradient_boosting" in n for n in names)


@pytest.mark.parametrize("task", ["classification", "regression"])
def test_sparse_categorical_excludes_hist_gradient_boosting(task):
    sel = select_model_candidates(
        task, n_rows=120, n_features=5, has_categorical_features=True,
        max_models=5,
    )
    assert not any("hist_gradient_boosting" in name for name in sel.models)


def test_default_model_challenger_budget_is_three():
    sel = select_model_candidates(
        "classification", n_rows=30, n_features=2,
        has_categorical_features=True,
    )
    assert len(sel.to_dict()["challenger_model_names"]) == 3
    assert len(sel.models) == 4


def test_invalid_budget_rejected():
    with pytest.raises(ValueError, match="between 1 and 5"):
        select_model_candidates(
            "classification", n_rows=30, n_features=2,
            has_categorical_features=False, max_models=7,
        )


def test_dummy_is_not_best_model_and_noskill_flag_is_exposed():
    frame = make_frame(["a", "b"] * 30)
    result = run_automl_experiment(
        frame, "label", task_type="classification",
        model_candidates={
            "dummy_classifier": DummyClassifier(strategy="most_frequent"),
            "logistic_regression": LogisticRegression(max_iter=300),
        },
        cv=3,
    )
    payload = result.to_dict()
    assert payload["baseline_result"]["status"] == "success"
    assert payload["best_result"]["model_name"] != "dummy_classifier"
    assert isinstance(payload["beats_dummy_baseline"], bool)


def test_http_auto_ambiguous_returns_400():
    csv = make_frame([i % 2 for i in range(36)]).to_csv(index=False).encode()
    resp = TestClient(app).post(
        "/api/analyze",
        data={"target_column": "label", "task_type": "auto", "cv": "2"},
        files={"file": ("synthetic.csv", BytesIO(csv), "text/csv")},
    )
    assert resp.status_code == 400
    assert "Ambiguous numeric" in resp.json()["detail"]
