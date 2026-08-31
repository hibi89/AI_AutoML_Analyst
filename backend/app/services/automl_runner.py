from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

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
from backend.app.services.model_selector import (
    ModelSelectionResult,
    select_model_candidates,
)


@dataclass
class AutoMLRunResult:
    target_column: str
    task_type: str
    preprocessing: PreprocessingResult
    results: list[ExperimentResult]
    ranked_results: list[dict[str, Any]]
    best_result: ExperimentResult | None
    model_selection: ModelSelectionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_column": self.target_column,
            "task_type": self.task_type,
            "preprocessing_summary": self.preprocessing.summary(),
            "model_selection": (
                self.model_selection.to_dict()
                if self.model_selection
                else None
            ),
            "results": experiment_results_to_dict(self.results),
            "ranked_results": self.ranked_results,
            "best_result": self.best_result.to_dict() if self.best_result else None,
        }


def get_default_model_candidates(
    task_type: str | None,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    기존 호환용 함수.

    실제 AutoML 실행에서는 select_model_candidates()를 통해
    데이터 크기 기반으로 후보를 선택한다.
    """

    selection = select_model_candidates(
        task_type=task_type,
        n_rows=5_000,
        n_features=20,
        has_categorical_features=False,
        random_state=random_state,
    )

    return selection.models


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

    처리:
        1. preprocessing 생성
        2. 데이터 크기/feature 구조 기반 모델 후보 선택
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

    model_selection: ModelSelectionResult | None = None

    if model_candidates is None:
        model_selection = select_model_candidates(
            task_type=effective_task_type,
            n_rows=len(prep.X),
            n_features=prep.X.shape[1],
            has_categorical_features=bool(prep.categorical_features),
            random_state=random_state,
        )

        model_candidates = model_selection.models

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
        model_selection=model_selection,
    )