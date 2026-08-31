from __future__ import annotations

from typing import Any

from backend.app.services.trainer import ExperimentResult


def rank_experiment_results(
    results: list[ExperimentResult],
) -> list[ExperimentResult]:
    """
    성공한 모델만 primary_score_mean 기준으로 내림차순 정렬.

    classification:
        f1_weighted 높을수록 좋음

    regression:
        r2 높을수록 좋음
    """

    successful_results = [
        result for result in results
        if result.status == "success" and result.primary_score_mean is not None
    ]

    ranked = sorted(
        successful_results,
        key=lambda result: result.primary_score_mean,
        reverse=True,
    )

    return ranked


def get_best_model_result(
    results: list[ExperimentResult],
) -> ExperimentResult | None:
    ranked = rank_experiment_results(results)

    if not ranked:
        return None

    return ranked[0]


def experiment_results_to_dict(
    results: list[ExperimentResult],
) -> list[dict[str, Any]]:
    return [result.to_dict() for result in results]


def ranked_summary(
    results: list[ExperimentResult],
) -> list[dict[str, Any]]:
    ranked = rank_experiment_results(results)

    summary: list[dict[str, Any]] = []

    for rank, result in enumerate(ranked, start=1):
        summary.append(
            {
                "rank": rank,
                "model_name": result.model_name,
                "primary_metric": result.primary_metric,
                "primary_score_mean": result.primary_score_mean,
                "primary_score_std": result.primary_score_std,
                "metrics": result.metrics,
                "fit_time_mean": result.fit_time_mean,
                "score_time_mean": result.score_time_mean,
            }
        )

    return summary