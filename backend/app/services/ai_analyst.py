from __future__ import annotations

from typing import Any

from backend.app.services.automl_runner import AutoMLRunResult
from backend.app.services.recommendation import generate_model_recommendations


def _interpret_task_type(task_type: str) -> str:
    if task_type == "regression":
        return "연속형 숫자 값을 예측하는 회귀 문제로 해석할 수 있습니다."

    if task_type == "classification":
        return "정답 클래스를 예측하는 분류 문제로 해석할 수 있습니다."

    return "문제 유형이 명확하지 않아 기본 분석 기준을 적용했습니다."


def _interpret_primary_metric(task_type: str, primary_metric: str) -> str:
    if task_type == "classification":
        if primary_metric == "f1_weighted":
            return (
                "f1_weighted는 클래스별 F1 점수를 샘플 수 비중에 따라 평균낸 지표입니다. "
                "클래스 불균형이 있을 때 accuracy만 보는 것보다 더 안정적인 판단에 도움이 됩니다."
            )

        if primary_metric == "accuracy":
            return "accuracy는 전체 샘플 중 맞춘 비율입니다."

    if task_type == "regression":
        if primary_metric == "r2":
            return (
                "R2는 모델이 타깃 값의 변동성을 얼마나 설명하는지 나타내는 지표입니다. "
                "1에 가까울수록 좋고, 0 근처면 단순 평균 예측과 비슷한 수준입니다."
            )

    return f"{primary_metric} 지표를 주요 기준으로 사용했습니다."


def _score_quality_comment(task_type: str, score: float | None) -> str:
    if score is None:
        return "성공한 모델 결과가 없어 성능 수준을 판단할 수 없습니다."

    if task_type == "classification":
        if score >= 0.90:
            return "현재 실험 데이터 기준으로 매우 높은 분류 성능을 보였습니다."
        if score >= 0.75:
            return "현재 실험 데이터 기준으로 준수한 분류 성능을 보였습니다."
        if score >= 0.60:
            return "현재 실험 데이터 기준으로 어느 정도 신호는 있으나 개선 여지가 있습니다."
        return "현재 실험 데이터 기준으로 성능이 낮아 feature 개선이나 데이터 품질 점검이 필요합니다."

    if task_type == "regression":
        if score >= 0.80:
            return "현재 실험 데이터 기준으로 설명력이 높은 회귀 결과입니다."
        if score >= 0.50:
            return "현재 실험 데이터 기준으로 어느 정도 설명력이 있습니다."
        if score >= 0.20:
            return "현재 실험 데이터 기준으로 설명력이 낮은 편입니다."
        return "현재 실험 데이터 기준으로 회귀 성능이 낮아 데이터/특성/타깃 관계 점검이 필요합니다."

    return "성능 점수를 기준으로 추가 검토가 필요합니다."


def _detect_risks(automl_result: AutoMLRunResult) -> list[str]:
    risks: list[str] = []

    prep_summary = automl_result.preprocessing.summary()
    n_rows = prep_summary["n_rows"]
    dropped_features = prep_summary["dropped_features"]

    top_result = automl_result.best_result

    failed_results = [
        result
        for result in automl_result.results
        if result.status != "success"
    ]

    if n_rows < 50:
        risks.append(
            "데이터 행 수가 매우 적습니다. 교차검증 점수가 높게 나와도 일반화 성능을 신뢰하기 어렵습니다."
        )
    elif n_rows < 200:
        risks.append(
            "데이터 행 수가 적은 편입니다. 성능 해석 시 과적합 가능성을 함께 확인해야 합니다."
        )

    if dropped_features:
        risks.append(
            f"전처리 과정에서 {len(dropped_features)}개 컬럼이 제거되었습니다: {dropped_features}"
        )

    if top_result and top_result.primary_score_mean is not None:
        if top_result.primary_score_mean >= 0.98 and n_rows < 100:
            risks.append(
                "작은 데이터에서 거의 완벽한 점수가 나왔습니다. 데이터 누수나 너무 쉬운 샘플 구성인지 확인이 필요합니다."
            )

        if top_result.primary_score_std is not None and top_result.primary_score_std > 0.10:
            risks.append(
                "교차검증 fold 간 성능 편차가 큽니다. 데이터 분할에 따라 성능이 흔들릴 수 있습니다."
            )

    if failed_results:
        failed_names = [result.model_name for result in failed_results]
        risks.append(
            f"일부 모델 학습/평가가 실패했습니다: {failed_names}"
        )

    if not risks:
        risks.append("현재 자동 점검 기준에서 큰 위험 요소는 발견되지 않았습니다.")

    return risks


def analyze_automl_result(
    automl_result: AutoMLRunResult,
) -> dict[str, Any]:
    """
    AutoML 결과를 해석 가능한 분석 dict로 변환한다.

    이 분석은 특정 모델을 절대적으로 추천하는 것이 아니라,
    현재 데이터/전처리/평가지표/교차검증 설정에서 관찰된 결과를 요약한다.
    """

    top_result = automl_result.best_result
    prep_summary = automl_result.preprocessing.summary()

    if top_result:
        top_model_summary = {
            "model_name": top_result.model_name,
            "primary_metric": top_result.primary_metric,
            "primary_score_mean": top_result.primary_score_mean,
            "primary_score_std": top_result.primary_score_std,
            "quality_comment": _score_quality_comment(
                task_type=automl_result.task_type,
                score=top_result.primary_score_mean,
            ),
        }
    else:
        top_model_summary = None

    top_model_summaries = generate_model_recommendations(
        automl_result=automl_result,
        top_n=3,
    )

    return {
        "task_interpretation": _interpret_task_type(automl_result.task_type),
        "metric_interpretation": _interpret_primary_metric(
            task_type=automl_result.task_type,
            primary_metric=top_result.primary_metric if top_result else "unknown",
        ),
        "dataset_summary": {
            "n_rows": prep_summary["n_rows"],
            "n_features_before_encoding": prep_summary["n_features_before_encoding"],
            "numeric_feature_count": len(prep_summary["numeric_features"]),
            "categorical_feature_count": len(prep_summary["categorical_features"]),
            "datetime_feature_count": len(prep_summary["datetime_features"]),
            "dropped_feature_count": len(prep_summary["dropped_features"]),
        },
        "top_model_summary": top_model_summary,
        "top_model_summaries": top_model_summaries,
        # 기존 호환용 키. 의미는 추천이 아니라 상위 결과 요약.
        "recommendations": top_model_summaries,
        "risks": _detect_risks(automl_result),
        "next_actions": [
            "현재 결과는 선택한 샘플, 전처리 방식, 평가 지표 기준의 실험 결과로 해석합니다.",
            "타깃 컬럼이 feature에 섞여 들어간 데이터 누수가 없는지 확인합니다.",
            "필요하면 분석할 target 컬럼을 바꿔 다른 관점의 실험을 수행합니다.",
            "최종 후보 모델은 별도 hold-out test set으로 검증합니다.",
        ],
    }