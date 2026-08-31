from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.svm import SVC, SVR

from backend.app.services.preprocessor import (
    PreprocessingResult,
    build_preprocessing_pipeline,
)
from backend.app.services.trainer import (
    ExperimentResult,
    run_cross_validation_for_models,
)
from backend.app.services.ranker import (
    get_best_model_result,
    ranked_summary,
    experiment_results_to_dict,
)


@dataclass
class AutoMLRunResult:
    target_column: str
    task_type: str
    preprocessing: PreprocessingResult
    results: list[ExperimentResult]
    ranked_results: list[dict[str, Any]]
    best_result: ExperimentResult | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_column": self.target_column,
            "task_type": self.task_type,
            "preprocessing_summary": self.preprocessing.summary(),
            "results": experiment_results_to_dict(self.results),
            "ranked_results": self.ranked_results,
            "best_result": self.best_result.to_dict() if self.best_result else None,
        }


def get_default_model_candidates(
    task_type: str | None,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    task_type에 따라 기본 모델 후보를 만든다.

    나중에는 registry.py + 데이터 특성 분석 결과로
    후보 모델 3~5개를 더 똑똑하게 고르게 만들 예정.
    지금은 MVP용 기본 후보.
    """

    normalized_task = (task_type or "").lower().strip()

    if normalized_task in ["regression", "regressor"]:
        return {
            "dummy_regressor": DummyRegressor(strategy="mean"),
            "linear_regression": LinearRegression(),
            "ridge": Ridge(),
            "random_forest_regressor": RandomForestRegressor(
                n_estimators=100,
                random_state=random_state,
            ),
            "gradient_boosting_regressor": GradientBoostingRegressor(
                random_state=random_state,
            ),
            "svr": SVR(),
        }

    return {
        "dummy_classifier": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": LogisticRegression(max_iter=1000),
        "random_forest_classifier": RandomForestClassifier(
            n_estimators=100,
            random_state=random_state,
        ),
        "gradient_boosting_classifier": GradientBoostingClassifier(
            random_state=random_state,
        ),
        "svc": SVC(),
    }


def run_automl_experiment(
    df: pd.DataFrame,
    target_column: str,
    task_type: str | None = None,
    model_candidates: Any | None = None,
    cv: int = 5,
    random_state: int = 42,
) -> AutoMLRunResult:
    """
    AutoML 핵심 실행 함수.

    입력:
        df              원본 데이터프레임
        target_column   예측 대상 컬럼
        task_type       classification / regression
        model_candidates 직접 넣을 모델 후보. None이면 기본 후보 사용.
        cv              cross validation split 수

    처리:
        1. preprocessing 생성
        2. 모델 후보 준비
        3. cross validation 실행
        4. 결과 랭킹
        5. best model 선택
    """

    prep = build_preprocessing_pipeline(
        df=df,
        target_column=target_column,
        task_type=task_type,
    )

    effective_task_type = prep.task_type or task_type or "classification"

    if model_candidates is None:
        model_candidates = get_default_model_candidates(
            task_type=effective_task_type,
            random_state=random_state,
        )

    results = run_cross_validation_for_models(
        X=prep.X,
        y=prep.y,
        preprocessor=prep.preprocessor,
        model_candidates=model_candidates,
        task_type=effective_task_type,
        cv=cv,
        random_state=random_state,
    )

    ranked = ranked_summary(results)
    best = get_best_model_result(results)

    return AutoMLRunResult(
        target_column=target_column,
        task_type=effective_task_type,
        preprocessing=prep,
        results=results,
        ranked_results=ranked,
        best_result=best,
    )