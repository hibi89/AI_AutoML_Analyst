from __future__ import annotations

from typing import Any

from backend.app.services.automl_runner import AutoMLRunResult
from backend.app.services.trainer import ExperimentResult


def _find_baseline_result(results: list[ExperimentResult]) -> ExperimentResult | None:
    baseline_names = [
        "dummy_classifier",
        "dummy_regressor",
        "dummy",
    ]

    for result in results:
        if result.model_name in baseline_names:
            return result

    for result in results:
        if "dummy" in result.model_name.lower():
            return result

    return None


def _make_model_observations(
    result: ExperimentResult,
    baseline: ExperimentResult | None,
    rank: int,
) -> list[str]:
    observations: list[str] = []

    score = result.primary_score_mean
    std = result.primary_score_std

    if rank == 1:
        observations.append("현재 실험 조건에서 가장 높은 주요 평가 점수를 기록했습니다.")
    else:
        observations.append(f"현재 실험 조건에서 전체 후보 중 {rank}위 성능을 기록했습니다.")

    if score is not None:
        observations.append(
            f"주요 지표 {result.primary_metric} 평균 점수는 {score:.4f}입니다."
        )

    if std is not None:
        if std <= 0.03:
            observations.append("교차검증 fold 간 점수 변동이 작아 비교적 안정적인 결과입니다.")
        elif std <= 0.10:
            observations.append("교차검증 fold 간 점수 변동은 보통 수준입니다.")
        else:
            observations.append("교차검증 fold 간 점수 변동이 큰 편이므로 데이터 분할에 민감할 수 있습니다.")

    if baseline and baseline.primary_score_mean is not None and score is not None:
        diff = score - baseline.primary_score_mean

        if diff > 0.15:
            observations.append(
                f"단순 기준 모델보다 {diff:.4f}p 높은 성능을 보여 의미 있는 개선이 관찰됩니다."
            )
        elif diff > 0:
            observations.append(
                f"단순 기준 모델보다 {diff:.4f}p 높지만 개선 폭은 크지 않습니다."
            )
        elif diff == 0:
            observations.append("단순 기준 모델과 성능 차이가 거의 없습니다.")
        else:
            observations.append("단순 기준 모델보다 성능이 낮아 현재 설정에서는 주의가 필요합니다.")

    if result.fit_time_mean is not None:
        if result.fit_time_mean < 0.05:
            observations.append("학습 시간이 짧아 빠른 반복 실험에 유리합니다.")
        elif result.fit_time_mean < 1.0:
            observations.append("학습 시간은 부담스럽지 않은 수준입니다.")
        else:
            observations.append("학습 시간이 긴 편이므로 대용량 데이터에서는 실행 비용을 확인해야 합니다.")

    return observations


def generate_model_recommendations(
    automl_result: AutoMLRunResult,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    """
    AutoML 결과를 바탕으로 상위 모델 결과를 요약한다.

    이름은 기존 호환을 위해 recommendation으로 유지하지만,
    실제 의미는 '추천'이 아니라 '현재 실험 조건에서의 상위 결과 요약'이다.
    """

    ranked = automl_result.ranked_results
    baseline = _find_baseline_result(automl_result.results)

    summaries: list[dict[str, Any]] = []

    result_by_name = {
        result.model_name: result
        for result in automl_result.results
    }

    for item in ranked[:top_n]:
        rank = item["rank"]
        model_name = item["model_name"]
        result = result_by_name.get(model_name)

        if result is None:
            continue

        summaries.append(
            {
                "rank": rank,
                "model_name": result.model_name,
                "primary_metric": result.primary_metric,
                "primary_score_mean": result.primary_score_mean,
                "primary_score_std": result.primary_score_std,
                "fit_time_mean": result.fit_time_mean,
                "score_time_mean": result.score_time_mean,
                "observations": _make_model_observations(
                    result=result,
                    baseline=baseline,
                    rank=rank,
                ),
            }
        )

    return summaries