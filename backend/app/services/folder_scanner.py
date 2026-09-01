from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


CSV_ENCODINGS = [
    "utf-8-sig",
    "utf-8",
    "cp949",
    "euc-kr",
    "latin1",
    "ISO-8859-1",
]


def _size_mb(path: Path) -> float:
    return round(path.stat().st_size / 1024 / 1024, 3)


def _safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def _normalize_column_name(col: Any) -> str:
    return str(col).strip().lower()


def _schema_signature(columns: list[str]) -> str:
    normalized = sorted(_normalize_column_name(col) for col in columns)
    return "|".join(normalized)


def _read_csv_try_encodings(
    path: Path,
    nrows: int | None = None,
) -> tuple[pd.DataFrame, str]:
    last_error: Exception | None = None

    for encoding in CSV_ENCODINGS:
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
                nrows=nrows,
                low_memory=False,
            )
            return df, encoding
        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to read CSV: {path}. Last error: {last_error}")


def read_csv_from_path(
    file_path: str | Path,
    nrows: int | None = None,
) -> tuple[pd.DataFrame, str]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() != ".csv":
        raise ValueError(f"Only CSV files are supported: {path}")

    return _read_csv_try_encodings(path, nrows=nrows)


def _to_json_safe_value(value: Any) -> Any:
    """
    numpy/pandas 값을 JSON으로 안전하게 내려주기 위한 변환.
    """
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def _sample_values(series: pd.Series, max_values: int = 5) -> list[Any]:
    values: list[Any] = []

    try:
        unique_values = series.dropna().unique()
    except Exception:
        return values

    for value in unique_values[:max_values]:
        safe_value = _to_json_safe_value(value)
        if safe_value is not None:
            values.append(safe_value)

    return values


def _build_column_profiles(
    df: pd.DataFrame,
    max_values: int = 5,
) -> dict[str, dict[str, Any]]:
    """
    샘플 데이터 기준 컬럼별 간단 프로필 생성.

    주의:
    전체 CSV 기준이 아니라 scan 시 읽은 sample_rows 기준이다.
    """

    profiles: dict[str, dict[str, Any]] = {}

    for col in df.columns:
        series = df[col]

        try:
            sample_unique_count = int(series.nunique(dropna=True))
        except Exception:
            sample_unique_count = 0

        try:
            missing_count = int(series.isna().sum())
        except Exception:
            missing_count = 0

        profiles[str(col)] = {
            "dtype": str(series.dtype),
            "sample_unique_count": sample_unique_count,
            "sample_missing_count": missing_count,
            "sample_values": _sample_values(series, max_values=max_values),
        }

    return profiles


def _merge_column_profiles(
    profile_list: list[dict[str, dict[str, Any]]],
    max_values: int = 8,
) -> dict[str, dict[str, Any]]:
    """
    대표 파일 여러 개에서 나온 column_profiles를 그룹 단위로 병합.
    """

    merged: dict[str, dict[str, Any]] = {}

    for profiles in profile_list:
        for col, profile in profiles.items():
            if col not in merged:
                merged[col] = {
                    "dtype": profile.get("dtype"),
                    "sample_unique_count": profile.get("sample_unique_count", 0),
                    "sample_missing_count": profile.get("sample_missing_count", 0),
                    "sample_values": list(profile.get("sample_values", [])),
                }
                continue

            merged[col]["sample_unique_count"] = max(
                int(merged[col].get("sample_unique_count", 0)),
                int(profile.get("sample_unique_count", 0)),
            )

            merged[col]["sample_missing_count"] = max(
                int(merged[col].get("sample_missing_count", 0)),
                int(profile.get("sample_missing_count", 0)),
            )

            existing_values = merged[col].get("sample_values", [])
            new_values = profile.get("sample_values", [])

            seen = {str(value) for value in existing_values}

            for value in new_values:
                if str(value) not in seen:
                    existing_values.append(value)
                    seen.add(str(value))

                if len(existing_values) >= max_values:
                    break

            merged[col]["sample_values"] = existing_values[:max_values]

    return merged


def _guess_target_candidates(df: pd.DataFrame) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    strong_keywords = [
        "target", "label", "class", "result", "outcome", "answer",
        "binary", "diabetes", "default", "churn", "fraud",
        "정답", "타겟", "라벨", "결과",
    ]

    classification_keywords = [
        "여부", "구분", "분류", "등급", "상태", "유형",
        "category", "type", "class", "label", "status", "binary",
    ]

    regression_keywords = [
        "price", "amount", "sales", "revenue", "score",
        "매출", "금액", "가격", "점수", "수량", "건수", "인구", "방문",
        "지출", "점포", "율", "_amt", "_co", "selng", "population",
        "count_", "_count",
    ]

    id_keywords = [
        "id", "idx", "index", "code", "_cd", "_id",
        "코드", "번호", "순번",
    ]

    n_rows = len(df)

    for col in df.columns:
        series = df[col]
        col_name = str(col)
        lower = col_name.lower()
        nunique = int(series.nunique(dropna=True))

        score = 0
        guessed_task = "unknown"
        reasons: list[str] = []

        is_id_like = (
            lower in ["id", "idx", "index"]
            or lower.endswith("_id")
            or lower.endswith("_cd")
            or any(k in lower for k in ["code"])
            or "코드" in col_name
            or "번호" in col_name
            or "순번" in col_name
        )

        looks_regression_by_name = any(k in lower or k in col_name for k in regression_keywords)
        looks_classification_by_name = any(k in lower or k in col_name for k in classification_keywords)

        if any(k in lower or k in col_name for k in strong_keywords):
            score += 45
            reasons.append("target/label/binary 계열 컬럼명입니다.")

        if looks_classification_by_name:
            score += 25
            guessed_task = "classification"
            reasons.append("분류 target 후보로 보이는 컬럼명입니다.")

        if looks_regression_by_name:
            score += 25
            guessed_task = "regression"
            reasons.append("회귀 target 후보로 보이는 컬럼명입니다.")

        if pd.api.types.is_numeric_dtype(series):
            if looks_regression_by_name:
                score += 15
                guessed_task = "regression"
                reasons.append("숫자형이며 금액/수량/인구/점포/지출 계열 컬럼입니다.")
            elif 2 <= nunique <= 20:
                score += 15
                if guessed_task == "unknown":
                    guessed_task = "classification"
                reasons.append("고유값이 적은 숫자형 컬럼입니다.")
            elif nunique > 20:
                score += 10
                if guessed_task == "unknown":
                    guessed_task = "regression"
                reasons.append("연속형 숫자 컬럼입니다.")
        else:
            if 2 <= nunique <= 50:
                score += 15
                if guessed_task == "unknown":
                    guessed_task = "classification"
                reasons.append("범주형 target 후보일 수 있습니다.")

        # 고유값 비율이 높으면 ID 가능성.
        # 단, 매출/금액/인구/점포 같은 명확한 회귀형 이름이면 ID 감점하지 않음.
        if n_rows > 0 and nunique / max(n_rows, 1) > 0.9 and not looks_regression_by_name:
            score -= 20
            reasons.append("고유값 비율이 높아 ID 컬럼일 수 있습니다.")

        if is_id_like:
            score -= 25
            reasons.append("ID/코드성 컬럼일 수 있어 우선순위를 낮췄습니다.")

        if score > 0:
            candidates.append(
                {
                    "column": col_name,
                    "score": score,
                    "guessed_task_type": guessed_task,
                    "dtype": str(series.dtype),
                    "unique_count_in_sample": nunique,
                    "sample_values": _sample_values(series, max_values=5),
                    "reasons": reasons,
                }
            )

    return sorted(candidates, key=lambda x: x["score"], reverse=True)[:10]


def _guess_join_keys(columns: list[str]) -> list[str]:
    key_hints = [
        "id", "code", "코드", "번호", "key",
        "년", "월", "분기", "일자", "날짜", "date",
        "상권", "업종", "지역", "시군구", "행정동",
    ]

    keys: list[str] = []

    for col in columns:
        lower = str(col).lower()
        if any(hint in lower or hint in str(col) for hint in key_hints):
            keys.append(str(col))

    return keys[:20]


def _merge_target_candidates(
    candidate_lists: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    for candidates in candidate_lists:
        for cand in candidates:
            col = cand["column"]

            if col not in merged:
                merged[col] = dict(cand)
                merged[col]["seen_in_representatives"] = 1
            else:
                merged[col]["score"] = max(merged[col]["score"], cand["score"])
                merged[col]["seen_in_representatives"] += 1

                existing_values = merged[col].get("sample_values", [])
                new_values = cand.get("sample_values", [])

                seen = {str(v) for v in existing_values}

                for value in new_values:
                    if str(value) not in seen:
                        existing_values.append(value)
                        seen.add(str(value))

                    if len(existing_values) >= 8:
                        break

                merged[col]["sample_values"] = existing_values[:8]

    return sorted(
        merged.values(),
        key=lambda x: (x["score"], x["seen_in_representatives"]),
        reverse=True,
    )[:10]


def scan_folder_schema_groups(
    root_path: str | Path,
    recursive: bool = True,
    max_files: int = 500,
    sample_rows: int = 50,
    representatives_per_group: int = 3,
) -> dict[str, Any]:
    """
    폴더 내 CSV를 전부 찾고,
    컬럼 구조가 같은 CSV끼리 schema group으로 묶는다.
    각 그룹에서는 대표 파일 2~3개만 샘플로 읽어서 패턴을 파악한다.
    """

    root = Path(root_path)

    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    if not root.is_dir():
        raise ValueError(f"Path is not a folder: {root}")

    max_files = max(1, min(int(max_files), 2000))
    sample_rows = max(1, min(int(sample_rows), 1000))
    representatives_per_group = max(1, min(int(representatives_per_group), 5))

    pattern = "**/*.csv" if recursive else "*.csv"

    csv_paths = [
        path
        for path in root.glob(pattern)
        if path.is_file() and path.suffix.lower() == ".csv"
    ]

    csv_paths = sorted(
        csv_paths,
        key=lambda p: p.stat().st_size,
        reverse=True,
    )[:max_files]

    file_infos: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    unreadable_files: list[dict[str, Any]] = []

    for path in csv_paths:
        info: dict[str, Any] = {
            "file_name": path.name,
            "file_path": str(path),
            "relative_path": _safe_relative(path, root),
            "size_mb": _size_mb(path),
        }

        try:
            header_df, encoding = _read_csv_try_encodings(path, nrows=0)
            columns = [str(col) for col in header_df.columns]
            signature = _schema_signature(columns)

            info.update(
                {
                    "readable": True,
                    "encoding": encoding,
                    "columns": columns,
                    "column_count": len(columns),
                    "schema_signature": signature,
                }
            )

            grouped[signature].append(info)
            file_infos.append(info)

        except Exception as e:
            info.update(
                {
                    "readable": False,
                    "encoding": None,
                    "columns": [],
                    "column_count": 0,
                    "schema_signature": None,
                    "error": str(e),
                }
            )
            unreadable_files.append(info)
            file_infos.append(info)

    schema_groups: list[dict[str, Any]] = []

    for idx, (signature, files) in enumerate(grouped.items(), start=1):
        files_sorted = sorted(files, key=lambda x: x["size_mb"], reverse=True)
        representatives = files_sorted[:representatives_per_group]

        representative_analyses: list[dict[str, Any]] = []
        target_candidate_lists: list[list[dict[str, Any]]] = []
        column_profile_list: list[dict[str, dict[str, Any]]] = []

        for rep in representatives:
            path = Path(rep["file_path"])

            try:
                sample_df, encoding = _read_csv_try_encodings(
                    path,
                    nrows=sample_rows,
                )

                target_candidates = _guess_target_candidates(sample_df)
                target_candidate_lists.append(target_candidates)

                column_profiles = _build_column_profiles(
                    sample_df,
                    max_values=5,
                )
                column_profile_list.append(column_profiles)

                representative_analyses.append(
                    {
                        "file_name": path.name,
                        "file_path": str(path),
                        "size_mb": _size_mb(path),
                        "encoding": encoding,
                        "sample_rows": int(len(sample_df)),
                        "columns": [str(col) for col in sample_df.columns],
                        "dtypes": {
                            str(col): str(dtype)
                            for col, dtype in sample_df.dtypes.items()
                        },
                        "column_profiles": column_profiles,
                        "target_candidates": target_candidates,
                    }
                )

            except Exception as e:
                representative_analyses.append(
                    {
                        "file_name": path.name,
                        "file_path": str(path),
                        "size_mb": _size_mb(path),
                        "error": str(e),
                    }
                )

        columns = files_sorted[0]["columns"] if files_sorted else []
        group_column_profiles = _merge_column_profiles(column_profile_list)

        schema_groups.append(
            {
                "schema_id": f"schema_{idx:03d}",
                "file_count": len(files_sorted),
                "total_size_mb": round(sum(f["size_mb"] for f in files_sorted), 3),
                "columns": columns,
                "column_count": len(columns),
                "column_profiles": group_column_profiles,
                "possible_join_keys": _guess_join_keys(columns),
                "representative_files": [
                    {
                        "file_name": f["file_name"],
                        "file_path": f["file_path"],
                        "relative_path": f["relative_path"],
                        "size_mb": f["size_mb"],
                    }
                    for f in representatives
                ],
                "target_candidates": _merge_target_candidates(target_candidate_lists),
                "representative_analyses": representative_analyses,
                "all_files": [
                    {
                        "file_name": f["file_name"],
                        "file_path": f["file_path"],
                        "relative_path": f["relative_path"],
                        "size_mb": f["size_mb"],
                    }
                    for f in files_sorted
                ],
            }
        )

    schema_groups = sorted(
        schema_groups,
        key=lambda g: g["total_size_mb"],
        reverse=True,
    )

    return {
        "root_path": str(root),
        "recursive": recursive,
        "total_csv_found": len(csv_paths),
        "readable_csv_count": len(file_infos) - len(unreadable_files),
        "unreadable_csv_count": len(unreadable_files),
        "schema_group_count": len(schema_groups),
        "total_csv_size_mb": round(sum(info["size_mb"] for info in file_infos), 3),
        "sample_rows_per_representative": sample_rows,
        "representatives_per_group": representatives_per_group,
        "schema_groups": schema_groups,
        "unreadable_files": unreadable_files,
    }