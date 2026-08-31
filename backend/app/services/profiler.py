from pathlib import Path

import pandas as pd


def detect_target_candidates(
    df: pd.DataFrame,
    column_profiles: dict,
) -> list[dict]:
    candidates = []
    rows = len(df)

    total_columns = len(df.columns)

    for index, column in enumerate(df.columns):
        series = df[column]
        profile = column_profiles[column]

        unique_count = profile["unique_count"]
        unique_rate = profile["unique_rate"]
        missing_rate = profile["missing_rate"]

        score = 0
        reasons = []

        # 마지막 컬럼일 가능성
        if index == total_columns - 1:
            score += 30
            reasons.append("last column")

        # 고유값이 적은 컬럼
        if unique_count == 2:
            score += 40
            reasons.append("binary target candidate")
        elif 2 < unique_count <= 10 and unique_rate <= 0.5:
            score += 20
            reasons.append("low cardinality")

        # 고유값 비율이 지나치게 높은 경우 ID 가능성
        if rows >= 50 and unique_rate > 0.95:
            score -= 40
            reasons.append("high cardinality")

        # 결측치가 많은 컬럼은 감점
        if missing_rate > 0.5:
            score -= 30
            reasons.append("high missing rate")

        # 컬럼명 기반 힌트
        column_name = column.lower()

        target_keywords = [
            "target",
            "label",
            "class",
            "churn",
            "outcome",
            "response",
            "y",
        ]

        if any(keyword == column_name for keyword in target_keywords):
            score += 40
            reasons.append("target-like column name")

        candidates.append(
            {
                "column": column,
                "score": max(score, 0),
                "reasons": reasons,
            }
        )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return candidates


def profile_csv(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".csv":
        raise ValueError("Only CSV files are supported.")

    df = pd.read_csv(path)

    rows = len(df)
    columns = len(df.columns)

    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    datetime_columns = df.select_dtypes(
        include=["datetime"]
    ).columns.tolist()

    column_profiles = {}

    for column in df.columns:
        series = df[column]

        profile = {
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_rate": round(
                float(series.isna().mean()),
                4,
            ),
            "unique_count": int(
                series.nunique(dropna=True)
            ),
            "unique_rate": round(
                float(series.nunique(dropna=True) / rows),
                4,
            ) if rows > 0 else 0.0,
        }

        if pd.api.types.is_numeric_dtype(series):
            profile.update(
                {
                    "min": float(series.min())
                    if not series.dropna().empty
                    else None,

                    "max": float(series.max())
                    if not series.dropna().empty
                    else None,

                    "mean": round(
                        float(series.mean()),
                        4,
                    )
                    if not series.dropna().empty
                    else None,

                    "median": round(
                        float(series.median()),
                        4,
                    )
                    if not series.dropna().empty
                    else None,

                    "std": round(
                        float(series.std()),
                        4,
                    )
                    if not series.dropna().empty
                    else None,
                }
            )

        else:
            value_counts = series.value_counts(
                dropna=True
            ).head(5)

            profile["top_values"] = {
                str(value): int(count)
                for value, count in value_counts.items()
            }

        column_profiles[column] = profile

    missing_columns = {
        column: {
            "count": profile["missing_count"],
            "rate": profile["missing_rate"],
        }
        for column, profile in column_profiles.items()
        if profile["missing_count"] > 0
    }

    constant_columns = [
        column
        for column, profile in column_profiles.items()
        if profile["unique_count"] <= 1
    ]

    target_candidates = detect_target_candidates(
        df,
        column_profiles,
    )

    return {
        "file": {
            "name": path.name,
            "size_bytes": path.stat().st_size,
        },

        "dataset": {
            "rows": rows,
            "columns": columns,
            "numeric_columns": len(numeric_columns),
            "categorical_columns": len(categorical_columns),
            "datetime_columns": len(datetime_columns),
        },

        "quality": {
            "duplicate_rows": int(
                df.duplicated().sum()
            ),
            "missing_columns": missing_columns,
            "constant_columns": constant_columns,
        },

        "target_candidates": target_candidates,

        "columns": column_profiles,
    }