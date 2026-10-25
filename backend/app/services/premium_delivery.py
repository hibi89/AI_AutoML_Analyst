"""PREMIUM: five-challenger evaluation + audited local model with exact-schema CSV runner."""
from __future__ import annotations

import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd
import sklearn
import skops
import skops.io as sio
from sklearn.base import clone
from sklearn.pipeline import Pipeline

from backend.app.services.basic_report import _csv_safe, build_basic_zip
from backend.app.services.preprocessor import (
    build_preprocessing_pipeline, _expand_datetime_features,
)
from backend.app.services.model_selector import select_model_candidates
from backend.app.services.standard_engine import run_standard
from backend.app.services.standard_delivery import _append_ml_pdf, _comparison_plot


def _final_refit(df: pd.DataFrame, analysis: dict):
    target = analysis["target_column"]
    excluded = [target] + [
        col for col in (analysis["group_column"], analysis["time_column"]) if col
    ]
    data = df[df[target].notna()].reset_index(drop=True)
    # Use training-only feature definitions to avoid holdout-informed selection.
    train = data.iloc[analysis["train_original_indices"]].reset_index(drop=True)
    train_input = train.drop(columns=[col for col in excluded if col != target])
    prep = build_preprocessing_pipeline(
        train_input, target_column=target, task_type=analysis["task_type"]
    )
    selection = select_model_candidates(
        task_type=analysis["task_type"], n_rows=len(prep.X),
        n_features=prep.X.shape[1],
        has_categorical_features=bool(prep.categorical_features), max_models=5,
    )
    winner = analysis["selected_model"]
    if winner not in selection.models:
        raise ValueError("Trained candidate registry drift: winner no longer available.")
    original_features = [col for col in df.columns if col not in excluded]
    full_raw = data[original_features].copy()
    processed = full_raw.copy()
    if prep.datetime_features:
        processed = _expand_datetime_features(processed, prep.datetime_features)
    bool_cols = list(processed.select_dtypes(include=["bool"]).columns)
    for name in bool_cols:
        processed[name] = processed[name].astype(float)
    processed = processed.reindex(columns=prep.X.columns)
    fitted = Pipeline([
        ("preprocess", clone(prep.preprocessor)),
        ("model", clone(selection.models[winner])),
    ]).fit(processed, data[target])
    # Final deployment refit includes holdout ONLY after model selection and
    # holdout evaluation. Holdout scores are not valid metrics of this refit.
    return fitted, {
        "raw_feature_columns": original_features,
        "numeric_raw_columns": [
            name for name in original_features
            if pd.api.types.is_numeric_dtype(full_raw[name])
            and not pd.api.types.is_bool_dtype(full_raw[name])
        ],
        "boolean_raw_columns": [
            name for name in original_features if pd.api.types.is_bool_dtype(full_raw[name])
        ],
        "datetime_features": list(prep.datetime_features),
        "prepared_feature_columns": list(prep.X.columns),
    }


def _premium_page(analysis: dict, model_name: str) -> bytes:
    from pypdf import PdfReader, PdfWriter
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from xml.sax.saxutils import escape
    from backend.app.services.basic_p3 import _korean_font

    font = _korean_font()
    body = ParagraphStyle(
        "premium_body", fontName=font, fontSize=10, leading=19,
        textColor=colors.HexColor("#253b4d"), spaceAfter=13,
    )
    heading = ParagraphStyle(
        "premium_heading", fontName=font, fontSize=20, leading=30,
        textColor=colors.HexColor("#163f61"), spaceAfter=22,
    )
    def p(text, heading_style=False):
        return Paragraph(escape(text), heading if heading_style else body)
    story = [
        p("PREMIUM — 재예측 모델과 사용 안내", True),
        p("CV에서 비교한 모델: 최대 5종 + Dummy 기준선."),
        p("최종 선택 모델: " + model_name),
        p("선정 근거: 학습 파티션의 교차검증 성능. 독립 검증 데이터는 선정에 사용하지 않았습니다."),
        p("중요: 독립 검증 점수는 학습 파티션 모델의 점수입니다. "
          "PREMIUM 납품 모델은 평가 완료 후 전체 라벨 보유 데이터에 재학습한 별도 모델이므로, "
          "동일한 독립 검증 점수라고 주장하지 않습니다."),
        Spacer(1, 18),
        p("재예측 실행 순서", True),
        p("1. 신뢰하는 원본 ZIP 파일을 로컬에서 압축 해제하세요."),
        p("2. Windows에서 Python 및 requirements-premium.txt의 정확한 버전을 설치하세요."),
        p("3. sample_input.csv와 정확히 같은 열 이름·순서를 가진 새 CSV를 준비하세요."),
        p("4. predict.cmd new_data.csv predicted.csv 를 실행하세요. 기존 출력 파일은 덮어쓰지 않습니다."),
        p("5. 결과 CSV에는 prediction 열만 있습니다. 개인 데이터/특정 행은 자동 전송되지 않습니다."),
        Spacer(1, 10),
        p("보안 및 해석", True),
        p("skops 모델은 신뢰한 원본만 열어야 합니다. SHA-256은 무결성 검사용이며 "
          "출처를 보증하는 디지털 서명이 아닙니다."),
        p("고객·시간 단위의 독립성, 목표값에서 파생된 변수, 수집 편향 및 미래 성능은 사용 전 확인해야 합니다."),
    ]
    out = BytesIO()
    SimpleDocTemplate(out, pagesize=A4, leftMargin=49, rightMargin=49,
                      topMargin=48, bottomMargin=52).build(story)
    return out.getvalue()


def build_premium_zip(
    df: pd.DataFrame,
    target_column: str,
    task_type: str | None = None,
    split_policy: str = "random",
    group_column: str | None = None,
    time_column: str | None = None,
    cv: int = 3,
) -> bytes:
    analysis = run_standard(
        df, target_column, task_type, split_policy, group_column, time_column,
        cv=cv, max_challengers=5,
    )
    model, raw_schema = _final_refit(df, analysis)
    model_data = sio.dumps(model)
    unknown_types = sio.get_untrusted_types(data=model_data)
    allowed_types = {"numpy.dtype"}  # Explicitly reviewed NumPy scalar dtype metadata.
    forbidden = set(unknown_types) - allowed_types
    if forbidden:
        raise ValueError(
            "skops requires unapproved model types. No unsafe model bundle will be generated: "
            + ", ".join(sorted(forbidden)[:5])
        )
    schema = {
        "format": "automl-premium-v1",
        "model_sha256": sha256(model_data).hexdigest(),
        "selected_model": analysis["selected_model"],
        "target_column": target_column,
        "task_type": analysis["task_type"],
        "training_strategy": "Refit CV-selected model on all labelled rows after untouched holdout evaluation",
        "evaluated_on": "Train-only final fit; independent holdout metrics not for the later full refit",
        "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
        "versions": {
            "sklearn": sklearn.__version__, "pandas": pd.__version__,
            "numpy": np.__version__, "skops": skops.__version__,
        },
        **raw_schema,
    }

    with ZipFile(BytesIO(build_basic_zip(df))) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()
                 if name not in ("manifest.json", "README.txt", "report.pdf")}
        basic_pdf = archive.read("report.pdf")
    ml_chart = _comparison_plot(analysis)
    parts["charts/06_ml_comparison.png"] = ml_chart
    standard_pdf = _append_ml_pdf(basic_pdf, analysis, ml_chart)
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(standard_pdf)))
    writer.append(PdfReader(BytesIO(_premium_page(analysis, analysis["selected_model"]))))
    merged = BytesIO()
    writer.write(merged)

    parts["report.pdf"] = merged.getvalue()
    parts["model_pipeline.skops"] = model_data
    parts["model_schema.json"] = json.dumps(schema, ensure_ascii=False, indent=2).encode("utf-8")
    public = {k: v for k, v in analysis.items()
              if k not in ("train_original_indices", "holdout_original_indices",
                           "train_group_values", "holdout_group_values")}
    parts["premium_summary.json"] = json.dumps(public, ensure_ascii=False, indent=2).encode("utf-8")
    csv_out = StringIO()
    scores = csv.writer(csv_out)
    scores.writerow(["model", "role", "status", "cv_primary", "cv_std", "error"])
    for row in analysis["models"]:
        scores.writerow([_csv_safe(row["model"]), row["role"], row["status"],
                         row["cv_primary"] if row["cv_primary"] is not None else "",
                         row["cv_std"] if row["cv_std"] is not None else "", row["error"] or ""])
    parts["model_scores.csv"] = ("\ufeff" + csv_out.getvalue()).encode("utf-8")
    input_example = StringIO()
    csv.writer(input_example).writerow(raw_schema["raw_feature_columns"])
    parts["sample_input.csv"] = ("\ufeff" + input_example.getvalue()).encode("utf-8")
    parts["sample_predictions.csv"] = b"prediction\r\n"
    parts["predict.py"] = Path(__file__).with_name("premium_predict.py").read_bytes()
    parts["predict.cmd"] = (
        '@echo off\r\n'
        'if "%~2"=="" (echo Usage: predict.cmd new_data.csv predicted.csv & exit /b 2)\r\n'
        'python "%~dp0predict.py" --model-dir "%~dp0" --input "%~1" --output "%~2"\r\n'
    ).encode("utf-8")
    v = schema["versions"]
    parts["requirements-premium.txt"] = (
        f"numpy=={v['numpy']}\npandas=={v['pandas']}\nscikit-learn=={v['sklearn']}\n"
        f"skops=={v['skops']}\n"
    ).encode()
    parts["README.txt"] = (
        "AI AutoML Analyst PREMIUM\n"
        "1) 신뢰하는 ZIP만 로컬 압축 해제. Python 환경 설치: pip install -r requirements-premium.txt\n"
        "2) sample_input.csv는 행이 없는 컬럼 템플릿입니다. 예시 결과를 만들어내지 않습니다.\n"
        "3) 새 CSV를 sample_input.csv와 동일한 컬럼명/순서로 만든 뒤\n"
        "   predict.cmd new_data.csv predicted.csv (Windows) 또는\n"
        "   python predict.py --input new_data.csv --output predicted.csv\n"
        "4) 모델은 오직 신뢰한 원본 ZIP에서 로드하세요. 모델 파일·스키마 SHA만으로 출처를 증명할 수 없습니다.\n"
        "5) 데이터는 외부로 보내지 않습니다. 기존 결과 파일은 덮어쓰지 않습니다.\n"
        "6) 홀드아웃 결과는 평가 당시 학습 모델에만 적용되며, 최종 전체 재학습 모델에 동일한 성능을 보장하지 않습니다.\n"
    ).encode("utf-8")
    manifest = {
        "format": "premium-v1", "tier": "PREMIUM", "no_raw_dataset": True,
        "files": [
            {"path": key, "size": len(value), "sha256": sha256(value).hexdigest()}
            for key, value in sorted(parts.items())
        ],
    }
    parts["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for key, value in parts.items():
            archive.writestr(key, value)
    return output.getvalue()
