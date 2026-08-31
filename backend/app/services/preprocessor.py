from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class PreprocessingResult:
    X: pd.DataFrame
    y: pd.Series
    preprocessor: ColumnTransformer
    target_column: str
    task_type: str | None
    numeric_features: list[str]
    categorical_features: list[str]
    datetime_features: list[str]
    dropped_features: list[str]

    def summary(self) -> dict[str, Any]:
        return {
            "target_column": self.target_column,
            "task_type": self.task_type,
            "n_rows": len(self.X),
            "n_features_before_encoding": self.X.shape[1],
            "numeric_features": self.numeric_features,
            "categorical_features": self.categorical_features,
            "datetime_features": self.datetime_features,
            "dropped_features": self.dropped_features,
        }


def _make_one_hot_encoder() -> OneHotEncoder:
    """
    sklearn 버전 차이 대응.
    최신 버전은 sparse_output,
    구버전은 sparse 파라미터를 쓴다.
    """
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def _is_probably_datetime(series: pd.Series) -> bool:
    """
    날짜형 컬럼 추정.
    너무 공격적으로 날짜 변환하면 일반 문자열까지 날짜로 오해할 수 있어서
    컬럼명 힌트를 같이 본다.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    if not (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
    ):
        return False

    name = str(series.name).lower()
    datetime_name_hints = [
        "date",
        "time",
        "datetime",
        "timestamp",
        "created",
        "updated",
        "날짜",
        "일자",
        "시간",
    ]

    has_name_hint = any(hint in name for hint in datetime_name_hints)
    if not has_name_hint:
        return False

    sample = series.dropna().astype(str).head(300)
    if len(sample) == 0:
        return False

    parsed = pd.to_datetime(sample, errors="coerce")
    success_ratio = parsed.notna().mean()

    return success_ratio >= 0.8


def _expand_datetime_features(
    X: pd.DataFrame,
    datetime_features: list[str],
) -> pd.DataFrame:
    """
    datetime 컬럼을 ML이 먹을 수 있는 숫자형 파생변수로 변환.
    원본 날짜 컬럼은 제거한다.
    """
    X = X.copy()

    for col in datetime_features:
        dt = pd.to_datetime(X[col], errors="coerce")

        X[f"{col}__year"] = dt.dt.year
        X[f"{col}__month"] = dt.dt.month
        X[f"{col}__day"] = dt.dt.day
        X[f"{col}__dayofweek"] = dt.dt.dayofweek
        X[f"{col}__hour"] = dt.dt.hour

        X = X.drop(columns=[col])

    return X


def build_preprocessing_pipeline(
    df: pd.DataFrame,
    target_column: str,
    task_type: str | None = None,
    high_cardinality_threshold: int = 50,
    high_cardinality_ratio: float = 0.5,
) -> PreprocessingResult:
    """
    AutoML 학습 전에 사용할 전처리 파이프라인 생성.

    역할:
    1. target 분리
    2. target 결측 행 제거
    3. 빈 컬럼 / 상수 컬럼 제거
    4. datetime 컬럼 파생변수화
    5. high-cardinality 범주형 컬럼 제거
    6. 숫자형 / 범주형 컬럼 분리
    7. sklearn ColumnTransformer 생성

    반환된 preprocessor는 Trainer에서 이렇게 사용한다.

    Pipeline([
        ("preprocess", result.preprocessor),
        ("model", estimator)
    ])
    """

    if target_column not in df.columns:
        raise ValueError(f"target_column '{target_column}' not found in dataframe.")

    data = df.copy()

    # target 결측치는 학습 불가능하므로 제거
    data = data[data[target_column].notna()].reset_index(drop=True)

    if data.empty:
        raise ValueError("No rows left after removing missing target values.")

    y = data[target_column].copy()
    X = data.drop(columns=[target_column]).copy()

    dropped_features: list[str] = []

    # 1. 전체 결측 컬럼 제거
    all_missing_cols = [
        col for col in X.columns
        if X[col].isna().all()
    ]
    if all_missing_cols:
        X = X.drop(columns=all_missing_cols)
        dropped_features.extend(all_missing_cols)

    # 2. 상수 컬럼 제거
    constant_cols = [
        col for col in X.columns
        if X[col].nunique(dropna=True) <= 1
    ]
    if constant_cols:
        X = X.drop(columns=constant_cols)
        dropped_features.extend(constant_cols)

    # 3. datetime 컬럼 탐지 및 확장
    datetime_features = [
        col for col in X.columns
        if _is_probably_datetime(X[col])
    ]

    if datetime_features:
        X = _expand_datetime_features(X, datetime_features)

    # 4. bool 컬럼은 숫자로 변환
    bool_cols = list(X.select_dtypes(include=["bool"]).columns)
    for col in bool_cols:
        X[col] = X[col].astype(float)

    # 5. high-cardinality 문자열 컬럼 제거
    candidate_categorical_cols = list(
        X.select_dtypes(include=["object", "category", "string"]).columns
    )

    high_cardinality_cols: list[str] = []
    n_rows = len(X)

    for col in candidate_categorical_cols:
        nunique = X[col].nunique(dropna=True)
        unique_ratio = nunique / max(n_rows, 1)

        if (
            nunique > high_cardinality_threshold
            and unique_ratio > high_cardinality_ratio
        ):
            high_cardinality_cols.append(col)

    if high_cardinality_cols:
        X = X.drop(columns=high_cardinality_cols)
        dropped_features.extend(high_cardinality_cols)

    # 6. 최종 숫자형 / 범주형 컬럼 분리
    numeric_features = list(X.select_dtypes(include=["number"]).columns)

    categorical_features = list(
        X.select_dtypes(include=["object", "category", "string"]).columns
    )

    if not numeric_features and not categorical_features:
        raise ValueError("No usable feature columns after preprocessing detection.")

    transformers = []

    if numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )

        transformers.append(
            ("numeric", numeric_pipeline, numeric_features)
        )

    if categorical_features:
        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", _make_one_hot_encoder()),
            ]
        )

        transformers.append(
            ("categorical", categorical_pipeline, categorical_features)
        )

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )

    return PreprocessingResult(
        X=X,
        y=y,
        preprocessor=preprocessor,
        target_column=target_column,
        task_type=task_type,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        datetime_features=datetime_features,
        dropped_features=dropped_features,
    )