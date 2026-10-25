"""STANDARD ML evaluation: one untouched holdout, 3 CV-selected challengers + Dummy.

Train/CV fitting is separated from holdout evaluation. The held-out set is
never used to choose the winning model. No artifacts or raw inputs persisted.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
)
from sklearn.model_selection import (
    GroupKFold, GroupShuffleSplit, TimeSeriesSplit,
    cross_validate, train_test_split,
)
from sklearn.pipeline import Pipeline

from backend.app.services.basic_report import validate_basic_frame
from backend.app.services.evaluator import get_scoring_config, summarize_cv_scores
from backend.app.services.model_selector import select_model_candidates
from backend.app.services.preprocessor import (
    build_preprocessing_pipeline, _expand_datetime_features,
)
from backend.app.services.task_detector import detect_task
from backend.app.services.trainer import _make_cv


def _holdout_scores(task: str, y_true: pd.Series, y_pred: Any) -> dict[str, float]:
    if task == "classification":
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        }
    rmse = math.sqrt(float(mean_squared_error(y_true, y_pred)))
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse,
    }


def run_standard(
    df: pd.DataFrame,
    target_column: str,
    task_type: str | None = None,
    split_policy: str = "random",
    group_column: str | None = None,
    time_column: str | None = None,
    cv: int = 3,
    random_state: int = 42,
) -> dict[str, Any]:
    validate_basic_frame(df)
    detected = detect_task(df, target_column, task_type)
    task = detected["task_type"]
    if split_policy not in ("random", "group", "time"):
        raise ValueError("split_policy must be one of: random, group, time.")
    if not isinstance(cv, int) or isinstance(cv, bool) or not 2 <= cv <= 5:
        raise ValueError("cv must be between 2 and 5 for STANDARD.")
    if group_column and split_policy != "group":
        raise ValueError("group_column is only permitted with split_policy='group'.")
    if time_column and split_policy != "time":
        raise ValueError("time_column is only permitted with split_policy='time'.")
    if split_policy == "group" and (not group_column or group_column not in df.columns):
        raise ValueError("Choose an existing group_column for group split.")
    if split_policy == "time" and (not time_column or time_column not in df.columns):
        raise ValueError("Choose an existing time_column for chronological split.")
    excluded = {target_column}
    if group_column:
        excluded.add(group_column)
    if time_column:
        excluded.add(time_column)

    data = df.loc[df[target_column].notna()].copy().reset_index(drop=True)
    warnings = [
        "목표를 직접 생성하거나 관측 이후에만 알 수 있는 설명변수가 있으면 누수가 발생합니다. 사용자 검토가 필요합니다.",
        "CV 점수는 학습 데이터 내부 성능, holdout 점수는 분리된 미사용 데이터 성능입니다. 미래 성과를 보장하지 않습니다.",
        "모델은 CV만으로 선정하며 holdout 점수로 모델을 다시 선정하지 않습니다.",
    ]
    if split_policy == "random":
        warnings.append(
            "무작위 분할은 동일 고객/장비/시간의 반복 관측을 보호하지 않습니다. "
            "그런 데이터에는 group 또는 time 분할을 지정하세요."
        )
        hints = [
            str(c) for c in data.columns if c != target_column
            and any(x in str(c).lower() for x in ("date", "time", "날짜", "일자"))
        ]
        if hints:
            warnings.append("시간 정보로 보이는 열이 있습니다. 미래 예측이라면 시간 분할로 재실행하세요.")
        if task == "classification":
            counts = data[target_column].value_counts()
            if counts.min() < 5:
                raise ValueError("Each class needs at least 5 rows for a disjoint stratified holdout and CV.")
        try:
            i_train, i_test = train_test_split(
                np.arange(len(data)), test_size=0.25,
                random_state=random_state,
                stratify=data[target_column] if task == "classification" else None,
            )
        except ValueError as exc:
            raise ValueError("Stratified holdout not feasible; add more rows per class.") from exc
    elif split_policy == "group":
        if data[group_column].isna().any():
            raise ValueError("group_column cannot contain missing group identifiers.")
        groups = data[group_column].astype(str)
        if groups.nunique() < 5:
            raise ValueError("Group split requires at least 5 distinct groups for holdout plus CV.")
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=random_state)
        i_train, i_test = next(splitter.split(data, data[target_column], groups=groups))
        train_groups = set(groups.iloc[i_train])
        test_groups = set(groups.iloc[i_test])
        if train_groups & test_groups:
            raise ValueError("Group split overlap detected.")
        warnings.append("그룹 간 분리 평가입니다. 새로운 그룹·기간의 성능까지 보장하지는 않습니다.")
    else:
        parsed = pd.to_datetime(data[time_column], errors="coerce")
        if parsed.isna().any():
            raise ValueError("time_column must contain only valid dates/timestamps for chronological holdout.")
        if parsed.nunique() < 10:
            raise ValueError("Chronological split requires at least 10 distinct time points.")
        order = np.argsort(parsed.to_numpy(), kind="stable")
        cut = int(len(data) * 0.75)
        i_train, i_test = order[:cut], order[cut:]
        if parsed.iloc[i_train].max() >= parsed.iloc[i_test].min():
            raise ValueError("Same timestamp crosses the time holdout boundary. Aggregate or split by distinct dates.")
        warnings.append("과거→미래 순서로 분리하되 시계열 전용 시차 특징과 시간상 변화는 별도 검증이 필요합니다.")

    if len(i_train) < 12 or len(i_test) < 4:
        raise ValueError("STANDARD requires at least 12 training and 4 untouched holdout rows.")

    train = data.iloc[i_train].reset_index(drop=True)
    holdout = data.iloc[i_test].reset_index(drop=True)
    if task == "classification":
        required = set(data[target_column].unique())
        if set(train[target_column].unique()) != required or set(holdout[target_column].unique()) != required:
            raise ValueError("Each class must occur in train and untouched holdout for valid classification evaluation.")
        if train[target_column].value_counts().min() < 2:
            raise ValueError("At least 2 training examples per class are required for CV.")

    train_features = train.drop(columns=list(excluded))
    prep = build_preprocessing_pipeline(
        train_features.assign(**{target_column: train[target_column]}),
        target_column=target_column, task_type=task,
    )

    # Feature definitions and missingness-based inclusion were learned on TRAIN only.
    raw_test_features = holdout.drop(columns=list(excluded)).copy()
    if prep.datetime_features:
        raw_test_features = _expand_datetime_features(raw_test_features, prep.datetime_features)
    for name in raw_test_features.select_dtypes(include=["bool"]).columns:
        raw_test_features[name] = raw_test_features[name].astype(float)
    X_train = prep.X
    X_test = raw_test_features.reindex(columns=X_train.columns)
    y_train = prep.y
    y_test = holdout[target_column]
    groups_train = None
    if split_policy == "group":
        groups_train = train[group_column].astype(str).reset_index(drop=True)
        n_groups = groups_train.nunique()
        if n_groups < 3:
            raise ValueError("At least 3 distinct training groups required for grouped cross-validation.")
        folds = min(cv, n_groups)
        cv_splits = list(GroupKFold(n_splits=folds).split(X_train, y_train, groups=groups_train))
    elif split_policy == "time":
        # Do not shuffle CV folds or leak later rows into earlier fits.
        folds = min(cv, max(2, (len(y_train) - 4) // 4))
        cv_splits = list(TimeSeriesSplit(n_splits=folds).split(X_train))
    else:
        cv_strategy, folds = _make_cv(y_train, task, cv, random_state)
        cv_splits = list(cv_strategy.split(X_train, y_train))

    for cv_train, cv_val in cv_splits:
        if len(cv_val) < (2 if task == "regression" else 1):
            raise ValueError("CV validation fold is too small for reliable metrics.")
        if task == "classification":
            if set(y_train.iloc[cv_train].unique()) != set(y_train.unique()):
                raise ValueError("Classification CV training fold is missing a class: choose more data/groups or another split policy.")
            if set(y_train.iloc[cv_val].unique()) != set(y_train.unique()):
                raise ValueError("Classification CV validation fold is missing a class: add groups or change split policy.")

    selection = select_model_candidates(
        task_type=task,
        n_rows=len(X_train),
        n_features=X_train.shape[1],
        has_categorical_features=bool(prep.categorical_features),
        random_state=random_state, max_models=3,
    )
    scoring = get_scoring_config(task, y_train)
    model_rows = []
    for model_name, estimator in selection.models.items():
        pipeline = Pipeline([
            ("preprocess", clone(prep.preprocessor)),
            ("model", clone(estimator)),
        ])
        try:
            cv_scores = cross_validate(
                pipeline, X_train, y_train, cv=cv_splits,
                scoring=scoring.scoring, error_score="raise", n_jobs=1,
            )
            metrics = summarize_cv_scores(cv_scores, scoring)
            score = metrics[scoring.primary_metric]["mean"]
            if not math.isfinite(score):
                raise ValueError("Non-finite CV score.")
            row = {
                "model": model_name, "role": "baseline" if model_name.startswith("dummy_") else "challenger",
                "status": "success", "cv_primary": float(score),
                "cv_std": float(metrics[scoring.primary_metric]["std"]),
                "cv_metrics": metrics, "error": None,
            }
        except Exception as exc:
            row = {"model": model_name, "role": "baseline" if model_name.startswith("dummy_") else "challenger",
                   "status": "failed", "cv_primary": None, "cv_std": None,
                   "cv_metrics": {}, "error": f"{type(exc).__name__}: {str(exc)[:240]}"}
        model_rows.append(row)
    challengers = [r for r in model_rows if r["role"] == "challenger" and r["status"] == "success"]
    baseline = next((r for r in model_rows if r["role"] == "baseline"), None)
    if not challengers or baseline is None or baseline["status"] != "success":
        raise ValueError("ML evaluation infeasible: no valid challenger or Dummy baseline completed CV.")
    winner = max(challengers, key=lambda r: r["cv_primary"])
    estimator = selection.models[winner["model"]]
    baseline_estimator = selection.models[baseline["model"]]

    def fit_holdout(est):
        fitted = Pipeline([
            ("preprocess", clone(prep.preprocessor)),
            ("model", clone(est)),
        ]).fit(X_train, y_train)
        return _holdout_scores(task, y_test, fitted.predict(X_test))

    best_holdout = fit_holdout(estimator)
    dummy_holdout = fit_holdout(baseline_estimator)
    primary = scoring.primary_metric
    better_cv = winner["cv_primary"] > baseline["cv_primary"]
    better_holdout = best_holdout[primary] > dummy_holdout[primary]
    if not better_cv or not better_holdout:
        warnings.append("비교 모델이 Dummy 기준선을 넘지 못했습니다. 유효한 예측 신호가 있다고 주장할 수 없습니다.")
    return {
        "tier": "STANDARD", "task_type": task, "target_column": target_column,
        "split_policy": split_policy, "group_column": group_column, "time_column": time_column,
        "selection_basis": "CV only (training partition)", "holdout_used_in_selection": False,
        "train_rows": len(train), "holdout_rows": len(holdout), "cv_splits": len(cv_splits),
        "primary_metric": primary, "model_selection": selection.to_dict(),
        "models": model_rows, "selected_model": winner["model"],
        "dummy_model": baseline["model"], "selected_cv_score": winner["cv_primary"],
        "dummy_cv_score": baseline["cv_primary"],
        "selected_holdout_metrics": best_holdout, "dummy_holdout_metrics": dummy_holdout,
        "cv_beats_dummy": better_cv, "holdout_beats_dummy": better_holdout,
        "warnings": warnings,
        "feature_columns": list(X_train.columns),
        "train_original_indices": [int(i) for i in i_train], "holdout_original_indices": [int(i) for i in i_test],
        "train_group_values": sorted(set(train[group_column].astype(str))) if split_policy == "group" else None,
        "holdout_group_values": sorted(set(holdout[group_column].astype(str))) if split_policy == "group" else None,
    }
