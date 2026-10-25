from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
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
    # Only exact same-origin UI is used in the local commercial app.
    allow_origins=[],
    allow_credentials=False,
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
            detail="Internal server error.",
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

        from backend.app.services.basic_report import MAX_UPLOAD_BYTES, validate_basic_frame
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="CSV exceeds 30 MiB upload limit.")

        if not content:
            raise ValueError("Uploaded file is empty.")

        df = _read_csv_from_bytes(content)
        validate_basic_frame(df)
        # The legacy endpoint also trains models: cap it independently from
        # BASIC's 20k-row descriptive-report limit.
        from backend.app.services.ml_workload_policy import check_rows
        check_rows(len(df), 3)

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

    except HTTPException:
        # Preserve 413 and other intentional API errors instead of converting to 500.
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error.",
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
            detail="Internal server error.",
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
            detail="Internal server error.",
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

# Commercial MVP preview: local-only access, no raw upload persistence.
# Legacy filesystem routes above remain unchanged and must never be hosted publicly.
def _require_local_mvp_request(request: Request) -> None:
    from urllib.parse import urlsplit

    client_host = request.client.host if request.client else ""
    host = (request.url.hostname or "").lower()
    if client_host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status_code=403, detail="BASIC MVP requires localhost access.")
    if host not in {"127.0.0.1", "localhost", "::1", "testserver"}:
        raise HTTPException(status_code=403, detail="BASIC MVP requires a local Host.")
    origin = request.headers.get("origin")
    if origin:
        parsed_origin = urlsplit(origin)
        if (
            parsed_origin.scheme not in {"http", "https"}
            or (parsed_origin.hostname or "").lower() not in {"127.0.0.1", "localhost", "::1"}
        ):
            raise HTTPException(status_code=403, detail="Cross-origin upload is not allowed.")


@app.get("/basic-mvp")
def basic_mvp_page(request: Request):
    from fastapi.responses import FileResponse

    _require_local_mvp_request(request)
    html_path = Path(__file__).resolve().parents[2] / "frontend" / "basic_mvp.html"
    return FileResponse(html_path, media_type="text/html; charset=utf-8")


@app.post("/api/basic-report")
async def basic_report_download(request: Request, file: UploadFile = File(...)):
    from fastapi.responses import Response

    from backend.app.services.basic_report import MAX_UPLOAD_BYTES, build_basic_zip
    from backend.app.services.tabular_input import read_uploaded_table

    _require_local_mvp_request(request)
    if not (file.filename or "").lower().endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="BASIC accepts CSV or XLSX only.")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Input must be at most 30 MiB.")
    if not data:
        raise HTTPException(status_code=400, detail="Empty CSV.")
    try:
        df = read_uploaded_table(data, file.filename or "")
        payload = build_basic_zip(df)
    except (ValueError, pd.errors.ParserError, UnicodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="automl_basic_mvp.zip"'},
    )


# STANDARD commercial development preview: synthetic/authorized CSV only.
# Reuse BASIC localhost/Host/Origin access guard; legacy APIs remain unsafe publicly.
@app.get("/standard-mvp")
def standard_mvp_page(request: Request):
    from fastapi.responses import FileResponse

    _require_local_mvp_request(request)
    html_path = Path(__file__).resolve().parents[2] / "frontend" / "standard_mvp.html"
    return FileResponse(html_path, media_type="text/html; charset=utf-8")


@app.post("/api/standard-report")
async def standard_report_download(
    request: Request,
    file: UploadFile = File(...),
    target_column: str = Form(...),
    task_type: str = Form("auto"),
    split_policy: str = Form("random"),
    group_column: str = Form(""),
    time_column: str = Form(""),
    cv: int = Form(3),
):
    from fastapi.responses import Response
    from backend.app.services.basic_report import MAX_UPLOAD_BYTES
    from backend.app.services.standard_delivery import build_standard_zip
    from backend.app.services.tabular_input import read_uploaded_table

    _require_local_mvp_request(request)
    if not (file.filename or "").lower().endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="STANDARD accepts CSV or XLSX only.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Input must be at most 30 MiB.")
    if not content:
        raise HTTPException(status_code=400, detail="Empty CSV.")
    try:
        data = read_uploaded_table(content, file.filename or "")
        payload = build_standard_zip(
            data, target_column=target_column,
            task_type=_normalize_task_type(task_type),
            split_policy=split_policy,
            group_column=group_column.strip() or None,
            time_column=time_column.strip() or None,
            cv=cv,
        )
    except (ValueError, pd.errors.ParserError, UnicodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(
        content=payload, media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="automl_standard_preview.zip"'},
    )


# PREMIUM local-only developer preview. No external model ingestion route.
@app.get("/premium-mvp")
def premium_mvp_page(request: Request):
    from fastapi.responses import FileResponse

    _require_local_mvp_request(request)
    html_path = Path(__file__).resolve().parents[2] / "frontend" / "premium_mvp.html"
    return FileResponse(html_path, media_type="text/html; charset=utf-8")


@app.post("/api/premium-report")
async def premium_report_download(
    request: Request,
    file: UploadFile = File(...),
    target_column: str = Form(...),
    task_type: str = Form("auto"),
    split_policy: str = Form("random"),
    group_column: str = Form(""),
    time_column: str = Form(""),
    cv: int = Form(3),
):
    from fastapi.responses import Response
    from backend.app.services.basic_report import MAX_UPLOAD_BYTES
    from backend.app.services.premium_delivery import build_premium_zip
    from backend.app.services.tabular_input import read_uploaded_table

    _require_local_mvp_request(request)
    if not (file.filename or "").lower().endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="PREMIUM accepts CSV or XLSX only.")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Input must be at most 30 MiB.")
    if not raw:
        raise HTTPException(status_code=400, detail="Empty CSV.")
    try:
        df = read_uploaded_table(raw, file.filename or "")
        payload = build_premium_zip(
            df, target_column=target_column, task_type=_normalize_task_type(task_type),
            split_policy=split_policy, group_column=group_column.strip() or None,
            time_column=time_column.strip() or None, cv=cv,
        )
    except (ValueError, pd.errors.ParserError, UnicodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(
        content=payload, media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="automl_premium_preview.zip"'},
    )


# P6 safety boundary: disable legacy arbitrary-file-path endpoints altogether.
# All remaining services require same-machine clients and local Host/Origin.
@app.middleware("http")
async def _local_commercial_boundary(request: Request, call_next):
    from fastapi.responses import JSONResponse
    from urllib.parse import urlsplit

    def forbidden(reason: str):
        return JSONResponse({"detail": reason}, status_code=403)

    peer = request.client.host if request.client else ""
    host = (request.url.hostname or "").lower()
    if peer not in {"127.0.0.1", "::1", "testclient"}:
        return forbidden("Local-only service. Remote clients are not supported.")
    if host not in {"127.0.0.1", "localhost", "::1", "testserver"}:
        return forbidden("Invalid Host. Use localhost.")
    origin = request.headers.get("origin")
    if origin:
        try:
            parsed = urlsplit(origin)
            expected_port = request.url.port
            if (parsed.scheme != request.url.scheme
                    or parsed.hostname != host
                    or parsed.port != expected_port
                    or parsed.username is not None
                    or parsed.password is not None):
                return forbidden("Cross-origin request refused.")
        except ValueError:
            return forbidden("Invalid Origin.")
    if request.url.path in {
        "/api/folders/browse", "/api/folder/scan", "/api/analyze-path",
    }:
        return forbidden("Legacy direct filesystem access is disabled. Upload an authorized CSV instead.")
    return await call_next(request)
