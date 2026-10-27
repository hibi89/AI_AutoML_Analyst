"""Bounded, rules-only ML feasibility cues for BASIC; never fit or infer a target.

These are metadata inspection prompts, not algorithmic task selection,
statistical evidence of feasibility, or predictions. Never export row values.
"""
from __future__ import annotations

import pandas as pd


_OUTCOME_HINTS = (
    "target", "label", "outcome", "result", "response", "churn",
    "revenue", "sales", "demand", "conversion", "purchase",
    "매출", "매출액", "판매", "수요", "구매", "이탈", "전환", "결과",
    "목표", "상태", "환불", "불량", "취소",
)
_IDENTIFIER_HINTS = (
    "uuid", "email", "phone", "customer_id", "order_id", "user_id",
    "account_id", "session_id", "identifier", "record_id",
    "식별", "고객번호", "주문번호", "고객id", "전화번호", "이메일",
)
_DATE_HINTS = (
    "date", "datetime", "timestamp", "created_at", "updated_at",
    "날짜", "일자", "일시", "시간",
)


def inspect_ml_feasibility(df: pd.DataFrame) -> dict:
    """Inspect targets for follow-up *questions* without fitting ML models.

    A numeric low-cardinality series is explicitly ambiguous. ID-like and
    datetime-like columns are not nominated automatically. The top three
    prompts favor explicit business-outcome name hints. Raw category values,
    row contents, target distributions and private examples are never emitted.
    """
    candidates: list[dict] = []
    exclusions = {"identifier_or_date": 0, "constant_or_empty": 0, "unusable_category": 0}
    n = len(df)
    for col in df.columns:
        name = str(col)
        lower = name.lower().strip()
        series = df[col]
        nonnull = int(series.notna().sum())
        unique = int(series.nunique(dropna=True))
        missing_pct = round(100.0 * (n - nonnull) / n, 1) if n else 0.0

        if (any(hint in lower for hint in _IDENTIFIER_HINTS)
                or lower in {"id", "index", "번호", "순번"}
                or pd.api.types.is_datetime64_any_dtype(series)
                or any(hint in lower for hint in _DATE_HINTS)):
            exclusions["identifier_or_date"] += 1
            continue
        if unique < 2 or nonnull < 10:
            exclusions["constant_or_empty"] += 1
            continue

        numeric = pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)
        boolean = pd.api.types.is_bool_dtype(series)
        hint = any(word in lower for word in _OUTCOME_HINTS)
        if numeric and unique <= 20:
            kind = "모호한 수치형"
            caveat = "분류/회귀 중 업무 목적 확인 필요"
        elif numeric:
            kind = "수치형"
            caveat = "회귀 목표인지 단위·관측시점 확인 필요"
        elif boolean:
            kind = "이진형"
            caveat = "참/거짓 의미와 클래스 비율 확인 필요"
        elif unique <= 20:
            # A category may be a feature, not necessarily a valid target.
            kind = "범주형"
            caveat = "분류 목표인지, 클래스별 표본 수 확인 필요"
        else:
            exclusions["unusable_category"] += 1
            continue
        if missing_pct > 40:
            caveat += "; 목표 결측 비율 높음"
        candidates.append({
            "column": name,
            "dtype": str(series.dtype),
            "observed_rows": nonnull,
            "unique_values": unique,
            "missing_pct": missing_pct,
            "inspection_type": kind,
            "caution": caveat,
            "outcome_name_hint": hint,
        })

    candidates.sort(key=lambda row: (
        not row["outcome_name_hint"], row["missing_pct"], row["column"]
    ))
    top = candidates[:3]
    constraints = []
    if n < 40:
        constraints.append("행이 40개 미만입니다. 검증용 별도 표본과 클래스별 표본 수 확보가 필요할 수 있습니다.")
    if not top:
        constraints.append("자동으로 검토 가능한 목표열이 없습니다. 고객이 업무 목표와 정답 열을 별도로 지정해야 합니다.")
    if any(item["missing_pct"] > 40 for item in top):
        constraints.append("후보 목표열에 결측이 많아 학습 가능한 정답 행이 부족할 수 있습니다.")
    if any(item["inspection_type"] == "모호한 수치형" for item in top):
        constraints.append("고유값이 적은 수치형은 분류/회귀를 자동 결정할 수 없습니다.")

    return {
        "version": "basic-ml-feasibility-v1",
        "assessment": "검토 자료일 뿐, 목표열 추천/유형 결정/예측 가능성 보장이 아닙니다.",
        "target_confirmed": False,
        "model_fitted": False,
        "candidate_count": len(candidates),
        "candidates": top,
        "excluded_column_counts": exclusions,
        "constraints": constraints,
        "requested_information": [
            "의뢰인이 원하는 예측 결과, 목표열, 단위 및 예측 시점을 명확히 지정",
            "동일 고객/기관의 반복 측정 여부와 관측 이후에만 알 수 있는 변수 표시",
            "시간/그룹이 분리된 추가 검증 자료 및 목표 클래스별 데이터 충분성 확인",
        ],
    }
