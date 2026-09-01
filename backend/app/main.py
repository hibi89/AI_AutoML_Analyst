from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.app.services.automl_runner import run_automl_experiment
from backend.app.services.ai_analyst import analyze_automl_result
from backend.app.services.report_generator import generate_markdown_report
from backend.app.services.folder_scanner import (
    read_csv_from_path,
    scan_folder_schema_groups,
)
from backend.app.services.storage import (
    list_jobs,
    load_report,
    load_result,
    save_analysis_result,
)


app = FastAPI(
    title="AI AutoML Analyst API",
    description="Upload a CSV file and run automated ML analysis.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_csv_from_bytes(content: bytes) -> pd.DataFrame:
    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp949",
        "euc-kr",
        "latin1",
        "ISO-8859-1",
    ]

    last_error: Exception | None = None

    for encoding in encodings:
        try:
            return pd.read_csv(BytesIO(content), encoding=encoding)
        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to read CSV file. Last error: {last_error}")


def _normalize_task_type(task_type: str | None) -> str | None:
    if task_type is None:
        return None

    normalized = task_type.strip().lower()

    if normalized in ["", "auto", "none", "null"]:
        return None

    if normalized in ["classification", "classifier", "class"]:
        return "classification"

    if normalized in ["regression", "regressor", "reg"]:
        return "regression"

    raise ValueError(
        "task_type must be one of: classification, regression, auto"
    )


def _normalize_cv(cv: int) -> int:
    if cv < 2:
        return 2

    if cv > 10:
        return 10

    return cv


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "message": "AI AutoML Analyst API",
        "docs": "/docs",
        "health": "/health",
        "analyze_upload": "/api/analyze",
        "folder_scan": "/api/folder/scan",
        "folder_browse": "/api/folders/browse",
        "analyze_path": "/api/analyze-path",
        "results": "/api/results",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get("/api/folders/browse")
def browse_folders(
    path: str | None = Query(None),
) -> dict[str, Any]:
    """
    로컬 개발용 폴더 탐색 API.

    브라우저는 보안상 로컬 절대경로를 직접 가져오기 어렵기 때문에,
    FastAPI 서버가 접근 가능한 폴더 목록을 읽어서 반환한다.

    주의:
        실제 배포 환경에서 아무 경로나 탐색하게 두면 보안상 위험하다.
        현재는 로컬 개발/포트폴리오 데모용 기능이다.
    """

    try:
        if path is None or path.strip() == "":
            # Docker에서는 /data가 있으면 우선 보여주고,
            # 로컬 Windows에서는 사용자의 home/Desktop을 기본 후보로 제공한다.
            home = Path.home()
            candidates: list[Path] = []

            if Path("/data").exists():
                candidates.append(Path("/data"))

            candidates.extend(
                [
                    home,
                    home / "Desktop",
                    home / "OneDrive" / "Desktop",
                    Path.cwd(),
                ]
            )

            folders = []

            seen: set[str] = set()

            for candidate in candidates:
                try:
                    if candidate.exists() and candidate.is_dir():
                        key = str(candidate)
                        if key not in seen:
                            folders.append(
                                {
                                    "name": candidate.name or str(candidate),
                                    "path": str(candidate),
                                }
                            )
                            seen.add(key)
                except Exception:
                    continue

            return {
                "current_path": None,
                "parent_path": None,
                "folders": folders,
                "note": "시작 위치 후보입니다. 폴더를 클릭해서 이동하거나 직접 경로를 입력할 수 있습니다.",
            }

        current = Path(path).expanduser()

        if not current.exists():
            raise FileNotFoundError(f"Folder not found: {current}")

        if not current.is_dir():
            raise ValueError(f"Path is not a folder: {current}")

        folders: list[dict[str, Any]] = []

        for item in sorted(current.iterdir(), key=lambda p: p.name.lower()):
            try:
                if item.is_dir():
                    folders.append(
                        {
                            "name": item.name,
                            "path": str(item),
                        }
                    )
            except Exception:
                continue

        parent = current.parent if current.parent != current else None

        return {
            "current_path": str(current),
            "parent_path": str(parent) if parent else None,
            "folders": folders,
            "note": None,
        }

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {e}",
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}",
        ) from e


@app.post("/api/analyze")
async def analyze_dataset(
    file: UploadFile = File(...),
    target_column: str = Form(...),
    task_type: str | None = Form(None),
    cv: int = Form(5),
) -> dict[str, Any]:
    filename = file.filename or ""

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported in this MVP version.",
        )

    try:
        normalized_task_type = _normalize_task_type(task_type)
        normalized_cv = _normalize_cv(cv)

        content = await file.read()

        if not content:
            raise ValueError("Uploaded file is empty.")

        df = _read_csv_from_bytes(content)

        if df.empty:
            raise ValueError("CSV file has no rows.")

        if target_column not in df.columns:
            raise ValueError(
                f"target_column '{target_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )

        automl_result = run_automl_experiment(
            df=df,
            target_column=target_column,
            task_type=normalized_task_type,
            cv=normalized_cv,
        )

        analysis = analyze_automl_result(automl_result)

        report = generate_markdown_report(
            automl_result=automl_result,
            analysis=analysis,
        )

        response_payload: dict[str, Any] = {
            "filename": filename,
            "dataset_info": {
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "column_names": list(df.columns),
            },
            "request": {
                "target_column": target_column,
                "task_type": normalized_task_type or "auto/default",
                "cv": normalized_cv,
            },
            "automl_result": automl_result.to_dict(),
            "analysis": analysis,
            "report_markdown": report,
        }

        job_info = save_analysis_result(
            result_payload=response_payload,
            report_markdown=report,
        )

        response_payload["job"] = job_info

        return response_payload

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}",
        ) from e


@app.post("/api/folder/scan")
def scan_folder(
    root_path: str = Form(...),
    recursive: bool = Form(True),
    max_files: int = Form(500),
    sample_rows: int = Form(50),
    representatives_per_group: int = Form(3),
) -> dict[str, Any]:
    try:
        return scan_folder_schema_groups(
            root_path=root_path,
            recursive=recursive,
            max_files=max_files,
            sample_rows=sample_rows,
            representatives_per_group=representatives_per_group,
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}",
        ) from e


@app.post("/api/analyze-path")
def analyze_csv_by_path(
    file_path: str = Form(...),
    target_column: str = Form(...),
    task_type: str | None = Form(None),
    cv: int = Form(3),
    sample_rows: int | None = Form(50000),
) -> dict[str, Any]:
    try:
        normalized_task_type = _normalize_task_type(task_type)
        normalized_cv = _normalize_cv(cv)

        nrows: int | None = None
        if sample_rows is not None and sample_rows > 0:
            nrows = sample_rows

        df, encoding = read_csv_from_path(
            file_path=file_path,
            nrows=nrows,
        )

        if df.empty:
            raise ValueError("CSV file has no rows.")

        if target_column not in df.columns:
            raise ValueError(
                f"target_column '{target_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )

        automl_result = run_automl_experiment(
            df=df,
            target_column=target_column,
            task_type=normalized_task_type,
            cv=normalized_cv,
        )

        analysis = analyze_automl_result(automl_result)

        report = generate_markdown_report(
            automl_result=automl_result,
            analysis=analysis,
        )

        response_payload: dict[str, Any] = {
            "source": {
                "type": "local_csv_path",
                "file_path": file_path,
                "encoding": encoding,
                "sample_rows": nrows,
            },
            "dataset_info": {
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "column_names": list(df.columns),
            },
            "request": {
                "target_column": target_column,
                "task_type": normalized_task_type or "auto/default",
                "cv": normalized_cv,
            },
            "automl_result": automl_result.to_dict(),
            "analysis": analysis,
            "report_markdown": report,
        }

        job_info = save_analysis_result(
            result_payload=response_payload,
            report_markdown=report,
        )

        response_payload["job"] = job_info

        return response_payload

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}",
        ) from e


@app.get("/api/results")
def get_results(limit: int = 50) -> dict[str, Any]:
    if limit < 1:
        limit = 1

    if limit > 200:
        limit = 200

    jobs = list_jobs(limit=limit)

    return {
        "count": len(jobs),
        "jobs": jobs,
    }


@app.get("/api/results/{job_id}")
def get_result(job_id: str) -> dict[str, Any]:
    try:
        return load_result(job_id)

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e


@app.get("/api/reports/{job_id}", response_class=PlainTextResponse)
def get_report(job_id: str) -> PlainTextResponse:
    try:
        report = load_report(job_id)

        return PlainTextResponse(
            content=report,
            media_type="text/markdown; charset=utf-8",
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e