"""P6E26: CV feature inclusion must not look at CV validation rows.

Old STANDARD/PREMIUM performed high-cardinality/constant/date detection on the
entire outer TRAIN partition before inner CV, leaking validation distribution.
All inputs in this module are synthetic and generated in memory.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.model_selection import cross_validate, KFold
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge

from backend.app.services import standard_engine
from backend.app.services.preprocessor import (
    FoldLocalPreprocessor, build_preprocessing_pipeline,
)
from backend.app.services.standard_engine import run_standard


def _synthetic_high_cardinality_frame():
    return pd.DataFrame({
        "region": ["A", "B"] * 6 + [f"private-category-{i:02d}" for i in range(12)],
        "amount": [float(100 + i) for i in range(24)],
    })


def test_validation_unique_categories_cannot_make_training_feature_disappear():
    raw = _synthetic_high_cardinality_frame()
    # Reproduces old inclusion: whole train 14 distinct /24 > 0.5, thus dropped;
    # the first fold's 12 training rows have only 2 distinct categories.
    old = build_preprocessing_pipeline(
        raw.assign(label=0), "label", high_cardinality_threshold=5,
    )
    assert "region" in old.dropped_features
    selector = FoldLocalPreprocessor(high_cardinality_threshold=5)
    selector.fit(raw.iloc[:12])
    assert "region" in selector.categorical_features_
    assert "region" not in selector.dropped_features_
    new_category_only_in_validation = selector.transform(raw.iloc[12:])
    assert new_category_only_in_validation.shape[0] == 12
    # Numeric feature plus categories A and B; unknown categories have all-zero
    # OHE encodings, never folded into a fit.
    assert new_category_only_in_validation.shape[1] == 3
    assert np.allclose(new_category_only_in_validation[:, 1:].toarray(), 0)


def test_datetime_rule_only_uses_training_fold_parsing_success():
    raw = pd.DataFrame({
        "event_date": (
            pd.date_range("2026-01-01", periods=12).strftime("%Y-%m-%d").tolist()
            + ["not-a-date"] * 12
        ),
        "sales": list(range(24)),
    })
    old = build_preprocessing_pipeline(raw.assign(label=0), "label")
    assert "event_date" not in old.datetime_features  # 50% date parse
    selector = FoldLocalPreprocessor().fit(raw.iloc[:12])
    assert selector.datetime_features_ == ["event_date"]
    predicted_inputs = selector.transform(raw.iloc[12:])
    assert predicted_inputs.shape[0] == 12
    assert np.isfinite(predicted_inputs).all()


def test_fold_preprocessor_is_sklearn_cloneable_and_survives_cv():
    raw = _synthetic_high_cardinality_frame()
    estimator = Pipeline([
        ("preprocess", FoldLocalPreprocessor(high_cardinality_threshold=5)),
        ("model", Ridge()),
    ])
    assert isinstance(clone(estimator).named_steps["preprocess"], FoldLocalPreprocessor)
    result = cross_validate(
        estimator, raw, pd.Series(np.arange(len(raw)) * 1.1),
        cv=KFold(n_splits=3, shuffle=True, random_state=4),
        scoring="neg_mean_absolute_error", error_score="raise",
    )
    assert len(result["test_score"]) == 3
    assert np.isfinite(result["test_score"]).all()


@pytest.mark.parametrize("split_policy", ["random", "time"])
def test_actual_standard_cv_gets_raw_columns_and_fold_local_selector(
    monkeypatch, split_policy,
):
    n = 120
    synthetic = pd.DataFrame({
        "event_date": pd.date_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "signal": [float(i % 13 + 1) for i in range(n)],
        "segment": ["east", "west", "north"] * (n // 3),
        "label": [float(20 + (i % 13) * 1.7 + i * 0.1) for i in range(n)],
    })
    observed = []
    original = standard_engine.cross_validate

    def check_eval(estimator, X, *args, **kwargs):
        observed.append((estimator.named_steps["preprocess"], tuple(X.columns)))
        return original(estimator, X, *args, **kwargs)

    monkeypatch.setattr(standard_engine, "cross_validate", check_eval)
    args = {"split_policy": split_policy}
    if split_policy == "time":
        args["time_column"] = "event_date"
    result = run_standard(synthetic, "label", "regression", cv=3, **args)
    assert result["cv_splits"] == 3
    assert len(observed) == 4  # 3 challengers + separately scored Dummy
    assert all(isinstance(obj, FoldLocalPreprocessor) for obj, _ in observed)
    assert all("signal" in names and "segment" in names for _, names in observed)
    assert all("label" not in names for _, names in observed)
    if split_policy == "time":
        assert all("event_date" not in names for _, names in observed)
    else:
        assert all("event_date" in names for _, names in observed)
