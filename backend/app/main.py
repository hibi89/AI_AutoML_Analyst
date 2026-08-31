from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.services.automl_runner import run_automl_experiment
from backend.app.services.ai_analyst import analyze_automl_result
from backend.app.services.report_generator import generate_markdown_report


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
    """
    업로드된 CSV bytes를 DataFrame으로 변환.

    한국어 CSV 대응을 위해 여러 인코딩을 순서대로 시도한다.
    """

    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]

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
    """
    너무 큰 CV는 API 테스트가 느려지므로 일단 2~10 사이로 제한.
    """

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
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.post("/api/analyze")
async def analyze_dataset(
    file: UploadFile = File(...),
    target_column: str = Form(...),
    task_type: str | None = Form(None),
    cv: int = Form(5),
) -> dict[str, Any]:
    """
    CSV 파일을 업로드하면 AutoML 분석을 실행한다.

    입력:
        file            CSV 파일
        target_column   예측 대상 컬럼명
        task_type       classification / regression / auto
        cv              cross validation split 수

    반환:
        dataset_info
        automl_result
        analysis
        report_markdown
    """

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

        return {
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