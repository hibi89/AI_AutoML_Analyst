"""P6E40: holdout validation CSV export, no untested predictive claim."""
from __future__ import annotations

import csv
from io import StringIO

import pytest

from backend.app.services.ml_delivery_tables import (
    feature_importance_csv, holdout_scores_csv,
)


def rows(value):
    return list(csv.DictReader(StringIO(value.decode("utf-8-sig"))))


def test_classification_no_skill_export_is_explicit():
    analysis = {
        "selected_model": "random_forest_classifier",
        "dummy_model": "dummy_classifier",
        "primary_metric": "f1_weighted",
        "holdout_beats_dummy": False,
        "selected_holdout_metrics": {"accuracy": .45, "f1_weighted": .42},
        "dummy_holdout_metrics": {"accuracy": .50, "f1_weighted": .48},
    }
    result = rows(holdout_scores_csv(analysis))
    assert [r["metric"] for r in result] == ["accuracy", "f1_weighted"]
    assert all(r["direction"] == "higher_is_better" for r in result)
    assert all(r["selected_better_on_metric"] == "no" for r in result)
    assert all(r["primary_holdout_beats_dummy"] == "no" for r in result)
    assert all(r["selection_basis"] == "selected_by_training_cv_only" for r in result)


def test_regression_mae_rmse_lower_is_better():
    analysis = {
        "selected_model": "ridge_regressor",
        "dummy_model": "dummy_regressor",
        "primary_metric": "r2",
        "holdout_beats_dummy": True,
        "selected_holdout_metrics": {"r2": .4, "mae": 2, "rmse": 2.5},
        "dummy_holdout_metrics": {"r2": -.2, "mae": 4, "rmse": 4.5},
    }
    result = {r["metric"]: r for r in rows(holdout_scores_csv(analysis))}
    assert result["mae"]["direction"] == "lower_is_better"
    assert result["mae"]["selected_better_on_metric"] == "yes"
    assert float(result["rmse"]["selected_minus_dummy"]) == -2
    assert result["r2"]["primary_holdout_beats_dummy"] == "yes"


def test_optional_importance_and_formula_safety():
    assert feature_importance_csv({"training_feature_importance": []}) is None
    result = rows(feature_importance_csv({
        "selected_model": "ridge_regressor",
        "training_feature_importance": [{
            "feature": "=HYPERLINK(1)", "importance": .75,
            "method": "absolute_coefficient",
        }],
    }))
    assert result[0]["feature"].startswith("'=")
    assert result[0]["interpretation"] == "model_internal_not_causal"


def test_invalid_holdout_metrics_fail_closed():
    a = {
        "selected_model": "candidate", "dummy_model": "dummy",
        "primary_metric": "accuracy", "holdout_beats_dummy": False,
        "selected_holdout_metrics": {"accuracy": .5},
        "dummy_holdout_metrics": {"accuracy": .5},
    }
    assert len(rows(holdout_scores_csv(a))) == 1
    with pytest.raises(ValueError, match="do not match"):
        holdout_scores_csv({**a, "dummy_holdout_metrics": {}})
    with pytest.raises(ValueError, match="finite"):
        holdout_scores_csv({**a, "selected_holdout_metrics": {"accuracy": float("nan")}})
