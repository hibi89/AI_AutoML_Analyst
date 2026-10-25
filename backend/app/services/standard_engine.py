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
from backend.app.services.ml_workload_policy import check_rows, estimate_training_matrix
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
    max_challengers: int = 3,
) -> dict[str, Any]:
    if max_challengers not in (3, 5) or isinstance(max_challengers, bool):
        raise ValueError("Only STANDARD=3 or PREMIUM=5 challengers are supported.")
    validate_basic_frame(df)
    # P6D: STANDARD/PREMIUM fit caps differ from BASIC report input caps.
    check_rows(len(df), max_challengers)
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
    # A literal duplicate of the target is direct leakage, not predictive skill.
    for col in data.columns:
        if col not in excluded and data[col].equals(data[target_column]):
            raise ValueError(
                f"Direct target leakage: feature '{col}' is identical to the target. "
                "Remove it and retry."
            )
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
    workload_budget = estimate_training_matrix(
        X_train, prep.numeric_features, prep.categorical_features, max_challengers
    )
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
        random_state=random_state, max_models=max_challengers,
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
    tuned_params: dict[str, dict[str, Any]] = {}
    tuning_log: list[dict[str, Any]] = []
    if max_challengers == 5:
        # PREMIUM-only: limited CV search among the top two challengers.
        # The untouched holdout never enters tuning or model selection.
        from sklearn.model_selection import GridSearchCV
        search_spaces = {
            "logistic_regression": {"model__C": [0.4, 1.6]},
            "ridge_classifier": {"model__alpha": [0.5, 2.0]},
            "random_forest_classifier": {"model__max_depth": [6, None]},
            "extra_trees_classifier": {"model__max_depth": [6, None]},
            "gradient_boosting_classifier": {"model__learning_rate": [0.05, 0.12]},
            "hist_gradient_boosting_classifier": {"model__learning_rate": [0.05, 0.12]},
            "linear_regression": {"model__fit_intercept": [True, False]},
            "ridge": {"model__alpha": [0.5, 2.0]},
            "lasso": {"model__alpha": [0.2, 1.0]},
            "random_forest_regressor": {"model__max_depth": [6, None]},
            "extra_trees_regressor": {"model__max_depth": [6, None]},
            "gradient_boosting_regressor": {"model__learning_rate": [0.05, 0.12]},
            "hist_gradient_boosting_regressor": {"model__learning_rate": [0.05, 0.12]},
        }
        for row in sorted(challengers, key=lambda item: item["cv_primary"], reverse=True)[:2]:
            name = row["model"]
            grid = search_spaces.get(name)
            if not grid:
                continue
            runner = Pipeline([
                ("preprocess", clone(prep.preprocessor)),
                ("model", clone(selection.models[name])),
            ])
            try:
                search = GridSearchCV(
                    runner, param_grid=grid, scoring=scoring.scoring,
                    refit=scoring.primary_metric, cv=cv_splits,
                    n_jobs=1, error_score="raise",
                )
                search.fit(X_train, y_train)
                best_idx = search.best_index_
                if not math.isfinite(float(search.best_score_)):
                    raise ValueError("Non-finite tuning CV score.")
                # All tuned metric averages refer to the SAME winning parameter set.
                row["cv_metrics"] = {}
                for metric_name in scoring.scoring:
                    mean = float(search.cv_results_[f"mean_test_{metric_name}"][best_idx])
                    std = float(search.cv_results_[f"std_test_{metric_name}"][best_idx])
                    display = metric_name
                    if metric_name == "neg_mae":
                        display, mean = "mae", -mean
                    elif metric_name == "neg_rmse":
                        display, mean = "rmse", -mean
                    row["cv_metrics"][display] = {"mean": mean, "std": std}
                row["cv_primary"] = float(search.best_score_)
                row["cv_std"] = float(search.cv_results_[
                    f"std_test_{scoring.primary_metric}"][best_idx])
                tuned_params[name] = dict(search.best_params_)
                tuning_log.append({
                    "model": name, "best_params": dict(search.best_params_),
                    "cv_primary": row["cv_primary"],
                    "cv_grid_candidates": len(search.cv_results_["params"]),
                })
            except Exception as exc:
                warnings.append(f"PREMIUM 탐색적 튜닝 실패({name}): {type(exc).__name__}. 기존 CV 평가로 계속합니다.")
        warnings.append(
            "PREMIUM 튜닝·모델 선택에 동일 CV 데이터를 사용했으므로 CV 값은 낙관적일 수 있습니다. "
            "결과 해석에는 별도 holdout 평가를 우선하세요."
        )
    winner = max(challengers, key=lambda r: r["cv_primary"])
    estimator = clone(selection.models[winner["model"]])
    if winner["model"] in tuned_params:
        estimator.set_params(**{
            k.replace("model__", "", 1): v
            for k, v in tuned_params[winner["model"]].items()
        })
    baseline_estimator = selection.models[baseline["model"]]

    def fit_holdout(est):
        fitted = Pipeline([
            ("preprocess", clone(prep.preprocessor)),
            ("model", clone(est)),
        ]).fit(X_train, y_train)
        return _holdout_scores(task, y_test, fitted.predict(X_test)), fitted

    best_holdout, best_pipeline = fit_holdout(estimator)
    dummy_holdout, _ = fit_holdout(baseline_estimator)

    # Training-derived model-specific ranking; never used to select model.
    # These are NOT permutation importance nor causal attributions.
    feature_importance: list[dict[str, Any]] = []
    fitted_model = best_pipeline.named_steps["model"]
    kind = None
    raw_importance = None
    if hasattr(fitted_model, "feature_importances_"):
        raw_importance = np.asarray(fitted_model.feature_importances_, dtype=float)
        kind = "tree_impurity"
    elif hasattr(fitted_model, "coef_"):
        coefs = np.asarray(fitted_model.coef_, dtype=float)
        raw_importance = np.abs(coefs).mean(axis=0) if coefs.ndim > 1 else np.abs(coefs)
        kind = "absolute_coefficient"
    if raw_importance is not None:
        try:
            feature_names = list(
                best_pipeline.named_steps["preprocess"].get_feature_names_out()
            )
            if len(feature_names) == len(raw_importance):
                # OneHotEncoder feature names embed category *values*, which
                # may be personal/confidential. Aggregate category-level scores
                # back to the user-supplied column name before reporting.
                merged: dict[str, float] = {}
                categorical_names = sorted(
                    [str(c) for c in prep.categorical_features], key=len, reverse=True
                )
                for raw_name, raw_score in zip(feature_names, raw_importance):
                    if not math.isfinite(float(raw_score)):
                        continue
                    name = str(raw_name)
                    if name.startswith("categorical__"):
                        encoded = name.removeprefix("categorical__")
                        name = next(
                            (c for c in categorical_names if encoded.startswith(c + "_")),
                            "범주형 변수 (식별값 비공개)",
                        )
                    else:
                        name = name.split("__", 1)[-1]
                    merged[name] = merged.get(name, 0.0) + float(raw_score)
                feature_importance = [
                    {"feature": name, "importance": round(score, 6), "method": kind}
                    for name, score in sorted(
                        merged.items(), key=lambda item: item[1], reverse=True
                    )[:8]
                ]
        except (ValueError, AttributeError, TypeError):
            # Intentionally do not fabricate importance when feature mapping fails.
            pass
    primary = scoring.primary_metric
    better_cv = winner["cv_primary"] > baseline["cv_primary"]
    better_holdout = best_holdout[primary] > dummy_holdout[primary]
    if not better_cv or not better_holdout:
        warnings.append("비교 모델이 Dummy 기준선을 넘지 못했습니다. 유효한 예측 신호가 있다고 주장할 수 없습니다.")
    return {
        "tier": "PREMIUM" if max_challengers == 5 else "STANDARD",
        "challenger_budget": max_challengers, "task_type": task, "target_column": target_column,
        "split_policy": split_policy, "group_column": group_column, "time_column": time_column,
        "selection_basis": "CV only (training partition)", "holdout_used_in_selection": False,
        "train_rows": len(train), "holdout_rows": len(holdout), "cv_splits": len(cv_splits),
        "primary_metric": primary, "model_selection": selection.to_dict(),
        "resource_budget": workload_budget,
        "models": model_rows, "tuning_experiments": tuning_log,
        "selected_hyperparameters": {
            k.replace("model__", "", 1): v
            for k, v in tuned_params.get(winner["model"], {}).items()
        },
        "selected_model": winner["model"],
        "dummy_model": baseline["model"], "selected_cv_score": winner["cv_primary"],
        "dummy_cv_score": baseline["cv_primary"],
        "selected_holdout_metrics": best_holdout, "dummy_holdout_metrics": dummy_holdout,
        "training_feature_importance": feature_importance,
        "cv_beats_dummy": better_cv, "holdout_beats_dummy": better_holdout,
        "warnings": warnings,
        "feature_columns": list(X_train.columns),
        "train_original_indices": [int(i) for i in i_train], "holdout_original_indices": [int(i) for i in i_test],
        "train_group_values": sorted(set(train[group_column].astype(str))) if split_policy == "group" else None,
        "holdout_group_values": sorted(set(holdout[group_column].astype(str))) if split_policy == "group" else None,
    }
