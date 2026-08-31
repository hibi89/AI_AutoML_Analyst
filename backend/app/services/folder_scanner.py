from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


CSV_ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]


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
    """
    컬럼 순서가 달라도 같은 schema로 보기 위해 정렬해서 signature 생성.
    """
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


def _guess_target_candidates(df: pd.DataFrame) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    strong_keywords = [
        "target", "label", "class", "result", "outcome", "answer",
        "정답", "타겟", "라벨", "결과",
    ]

    classification_keywords = [
        "여부", "구분", "분류", "등급", "상태", "유형",
        "category", "type", "class", "label", "status",
    ]

    regression_keywords = [
        "price", "amount", "sales", "revenue", "score", "count",
        "매출", "금액", "가격", "점수", "수량", "건수", "인구", "방문",
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

        if any(k in lower for k in strong_keywords):
            score += 50
            reasons.append("target/label 계열 컬럼명입니다.")

        if any(k in lower for k in classification_keywords):
            score += 25
            guessed_task = "classification"
            reasons.append("분류 target 후보로 보이는 컬럼명입니다.")

        if any(k in lower for k in regression_keywords):
            score += 25
            guessed_task = "regression"
            reasons.append("회귀 target 후보로 보이는 컬럼명입니다.")

        if pd.api.types.is_numeric_dtype(series):
            if 2 <= nunique <= 20:
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

        if n_rows > 0 and nunique / max(n_rows, 1) > 0.9:
            score -= 20
            reasons.append("고유값 비율이 높아 ID 컬럼일 수 있습니다.")

        if (
            lower in ["id", "idx", "index"]
            or lower.endswith("_id")
            or "코드" in col_name
            or "id" == lower
        ):
            score -= 15
            reasons.append("ID/코드성 컬럼일 수 있어 우선순위를 낮췄습니다.")

        if score > 0:
            candidates.append(
                {
                    "column": col_name,
                    "score": score,
                    "guessed_task_type": guessed_task,
                    "dtype": str(series.dtype),
                    "unique_count_in_sample": nunique,
                    "reasons": reasons,
                }
            )

    return sorted(candidates, key=lambda x: x["score"], reverse=True)[:10]


def _guess_join_keys(columns: list[str]) -> list[str]:
    """
    여러 CSV를 나중에 병합할 때 공통 key 후보가 될 수 있는 컬럼 추정.
    지금은 분석 참고용.
    """
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

        for rep in representatives:
            path = Path(rep["file_path"])

            try:
                sample_df, encoding = _read_csv_try_encodings(
                    path,
                    nrows=sample_rows,
                )

                target_candidates = _guess_target_candidates(sample_df)
                target_candidate_lists.append(target_candidates)

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

        schema_groups.append(
            {
                "schema_id": f"schema_{idx:03d}",
                "file_count": len(files_sorted),
                "total_size_mb": round(sum(f["size_mb"] for f in files_sorted), 3),
                "columns": columns,
                "column_count": len(columns),
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