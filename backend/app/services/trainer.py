from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import KFold, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from backend.app.services.evaluator import (
    get_scoring_config,
    summarize_cv_scores,
)


@dataclass
class ExperimentResult:
    model_name: str
    task_type: str
    primary_metric: str
    primary_score_mean: float | None
    primary_score_std: float | None
    metrics: dict[str, dict[str, float]]
    fit_time_mean: float | None
    score_time_mean: float | None
    cv_splits: int | None
    status: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "task_type": self.task_type,
            "primary_metric": self.primary_metric,
            "primary_score_mean": self.primary_score_mean,
            "primary_score_std": self.primary_score_std,
            "metrics": self.metrics,
            "fit_time_mean": self.fit_time_mean,
            "score_time_mean": self.score_time_mean,
            "cv_splits": self.cv_splits,
            "status": self.status,
            "error": self.error,
        }


def _normalize_model_candidates(
    model_candidates: Any,
) -> list[tuple[str, Any]]:
    """
    여러 형태의 모델 후보 입력을 통일한다.

    허용 형태:
    1. dict
        {
            "random_forest": RandomForestClassifier(),
            "logistic_regression": LogisticRegression()
        }

    2. list of tuple
        [
            ("random_forest", RandomForestClassifier()),
            ("logistic_regression", LogisticRegression())
        ]

    3. list of dict
        [
            {"name": "random_forest", "estimator": RandomForestClassifier()}
        ]

    4. 객체
        item.name
        item.estimator
    """

    normalized: list[tuple[str, Any]] = []

    if isinstance(model_candidates, dict):
        for name, estimator in model_candidates.items():
            normalized.append((str(name), estimator))
        return normalized

    if not isinstance(model_candidates, Iterable):
        raise TypeError("model_candidates must be dict or iterable.")

    for item in model_candidates:
        if isinstance(item, tuple) and len(item) == 2:
            name, estimator = item
            normalized.append((str(name), estimator))
            continue

        if isinstance(item, dict):
            name = item.get("name") or item.get("model_name")
            estimator = item.get("estimator") or item.get("model")

            if name is None or estimator is None:
                raise ValueError(
                    "model candidate dict must have name/model_name and estimator/model."
                )

            normalized.append((str(name), estimator))
            continue

        name = getattr(item, "name", None) or getattr(item, "model_name", None)
        estimator = getattr(item, "estimator", None) or getattr(item, "model", None)

        if name is None or estimator is None:
            raise ValueError(f"Unsupported model candidate format: {item}")

        normalized.append((str(name), estimator))

    return normalized


def _make_cv(
    y: pd.Series,
    task_type: str,
    requested_splits: int,
    random_state: int,
):
    """
    데이터 크기와 클래스 개수에 맞춰 안전한 CV 객체 생성.

    classification에서는 StratifiedKFold를 쓰되,
    특정 클래스 샘플 수가 너무 적으면 split 수를 자동으로 줄인다.
    """

    n_samples = len(y)

    if n_samples < 2:
        raise ValueError("At least 2 samples are required for cross validation.")

    requested_splits = max(2, int(requested_splits))

    if task_type == "classification":
        class_counts = pd.Series(y).value_counts(dropna=False)
        min_class_count = int(class_counts.min())

        # StratifiedKFold는 각 클래스에 최소 n_splits개 샘플이 있어야 한다.
        effective_splits = min(requested_splits, min_class_count)

        if effective_splits >= 2:
            return StratifiedKFold(
                n_splits=effective_splits,
                shuffle=True,
                random_state=random_state,
            ), effective_splits

        # 클래스가 너무 불균형해서 StratifiedKFold가 불가능하면 일반 KFold로 fallback.
        fallback_splits = min(requested_splits, n_samples)

        if fallback_splits < 2:
            raise ValueError("Not enough samples for KFold.")

        return KFold(
            n_splits=fallback_splits,
            shuffle=True,
            random_state=random_state,
        ), fallback_splits

    # regression
    effective_splits = min(requested_splits, n_samples)

    if effective_splits < 2:
        raise ValueError("Not enough samples for KFold.")

    return KFold(
        n_splits=effective_splits,
        shuffle=True,
        random_state=random_state,
    ), effective_splits


def run_cross_validation_for_models(
    X: pd.DataFrame,
    y: pd.Series,
    preprocessor: ColumnTransformer,
    model_candidates: Any,
    task_type: str | None,
    cv: int = 5,
    random_state: int = 42,
) -> list[ExperimentResult]:
    """
    여러 모델 후보에 대해 동일한 전처리 + 모델 pipeline으로 cross validation 수행.

    구조:
        Pipeline([
            ("preprocess", preprocessor),
            ("model", estimator)
        ])

    반환:
        ExperimentResult 리스트
    """

    scoring_config = get_scoring_config(task_type=task_type, y=y)
    normalized_models = _normalize_model_candidates(model_candidates)

    cv_strategy, effective_splits = _make_cv(
        y=y,
        task_type=scoring_config.task_type,
        requested_splits=cv,
        random_state=random_state,
    )

    results: list[ExperimentResult] = []

    for model_name, estimator in normalized_models:
        try:
            pipeline = Pipeline(
                steps=[
                    ("preprocess", preprocessor),
                    ("model", clone(estimator)),
                ]
            )

            cv_result = cross_validate(
                estimator=pipeline,
                X=X,
                y=y,
                cv=cv_strategy,
                scoring=scoring_config.scoring,
                return_train_score=False,
                error_score="raise",
                n_jobs=None,
            )

            metrics = summarize_cv_scores(
                cv_result=cv_result,
                scoring_config=scoring_config,
            )

            primary_metric = scoring_config.primary_metric

            if primary_metric not in metrics:
                raise ValueError(f"Primary metric '{primary_metric}' not found in metrics.")

            primary_score_mean = metrics[primary_metric]["mean"]
            primary_score_std = metrics[primary_metric]["std"]

            result = ExperimentResult(
                model_name=model_name,
                task_type=scoring_config.task_type,
                primary_metric=primary_metric,
                primary_score_mean=primary_score_mean,
                primary_score_std=primary_score_std,
                metrics=metrics,
                fit_time_mean=float(cv_result["fit_time"].mean()),
                score_time_mean=float(cv_result["score_time"].mean()),
                cv_splits=effective_splits,
                status="success",
                error=None,
            )

        except Exception as e:
            result = ExperimentResult(
                model_name=model_name,
                task_type=scoring_config.task_type,
                primary_metric=scoring_config.primary_metric,
                primary_score_mean=None,
                primary_score_std=None,
                metrics={},
                fit_time_mean=None,
                score_time_mean=None,
                cv_splits=effective_splits,
                status="failed",
                error=str(e),
            )

        results.append(result)

    return results