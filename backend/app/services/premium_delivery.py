"""PREMIUM: five-challenger evaluation + audited local model with exact-schema CSV runner."""
from __future__ import annotations

from backend.app.services.font_coverage import font_usage_notice
from backend.app.services.privacy_review import inspect_header_privacy, privacy_header_notice

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
from backend.app.services.basic_p3 import NANUM_FONT_CREDIT
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
    final_estimator = clone(selection.models[winner])
    if analysis.get("selected_hyperparameters"):
        final_estimator.set_params(**analysis["selected_hyperparameters"])
    fitted = Pipeline([
        ("preprocess", clone(prep.preprocessor)),
        ("model", final_estimator),
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


def _premium_page(analysis: dict, model_name: str, raw_schema: dict) -> bytes:
    """Two-page, data-grounded PREMIUM handover; no invented performance claims."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    )
    from xml.sax.saxutils import escape
    from backend.app.services.basic_p3 import _korean_font

    from backend.app.services.font_coverage import resolve_report_fonts, safe_pdf_markup
    required = "".join(str(col) for col in raw_schema["raw_feature_columns"])
    font, fallback_font = resolve_report_fonts(required)
    ink = colors.HexColor("#233B4D")
    blue = colors.HexColor("#163F61")
    teal = colors.HexColor("#087F8C")
    styles = {
        "title": ParagraphStyle("premium_title", fontName=font, fontSize=19,
                                leading=27, textColor=blue, spaceAfter=11),
        "head": ParagraphStyle("premium_head", fontName=font, fontSize=12,
                               leading=18, textColor=teal, spaceBefore=10, spaceAfter=7),
        "body": ParagraphStyle("premium_body", fontName=font, fontSize=9.2,
                               leading=15, textColor=ink, spaceAfter=6),
        "small": ParagraphStyle("premium_small", fontName=font, fontSize=8.2,
                                leading=13, textColor=ink, spaceAfter=4),
    }

    def p(value: object, style: str = "body"):
        return Paragraph(safe_pdf_markup(value, font, fallback_font), styles[style])

    def panel(rows: list[tuple[str, str]]) -> Table:
        # Paragraphs, rather than unwrapped strings, allow long column names to
        # wrap without intruding into the adjacent PDF column.
        data = [[p(a, "small"), p(b, "small")] for a, b in rows]
        table = Table(data, colWidths=[127, 368], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1),
             [colors.HexColor("#F0F6F8"), colors.white]),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#D8E6ED")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CFDFE7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    primary = analysis["primary_metric"]
    selected_score = analysis["selected_holdout_metrics"][primary]
    baseline_score = analysis["dummy_holdout_metrics"][primary]
    columns = raw_schema["raw_feature_columns"]
    example_names = ", ".join(str(col)[:34] for col in columns[:8])
    if len(columns) > 8:
        example_names += f" 외 {len(columns) - 8}개 (전체는 model_schema.json)"
    story = [
        p("PREMIUM / 재사용 모델 인수인계", "title"),
        p("학습된 모델과 재예측 도구의 사용 조건을 확인하는 납품 설명서입니다.", "small"),
        p("모델 검증 스냅샷", "head"),
        panel([
            ("선정 모델", model_name),
            ("목표 / 문제 유형", f"{analysis['target_column']} / {analysis['task_type']}"),
            ("선발 기준", f"학습 내부 {analysis['cv_splits']}폴드 CV / {primary}"),
            ("평가 데이터", f"학습 {analysis['train_rows']:,}행 · 독립 검증 {analysis['holdout_rows']:,}행"),
            ("독립 검증 점수", f"선정 모델 {selected_score:.4f} / Dummy {baseline_score:.4f} ({primary})"),
        ]),
        p("이 점수는 독립 검증 시점의 학습 모델에 대한 것입니다. "
          "납품 모델은 평가 완료 후 전체 라벨 보유 데이터로 다시 학습하므로 "
          "같은 점수를 보장하지 않습니다.", "small"),
        p("새 CSV로 예측하기", "head"),
        panel([
            ("01 / 원본 확인", "발신자와 전달 경로를 확인한 신뢰 가능한 ZIP만 압축 해제"),
            ("02 / 환경 설치", "Python과 requirements-premium.txt의 호환 버전 설치"),
            ("03 / 입력 작성", "sample_input.csv의 필수 열 이름과 순서를 그대로 유지하여 새 CSV 작성"),
            ("04 / 실행", "Windows: predict.cmd new_data.csv predicted.csv (일본어 CP932는 끝에 cp932 추가)"),
            ("05 / 결과 확인", "prediction 열을 검토하고 원본 입력과 함께 안전하게 보관"),
        ]),
        p("실행 전 주의", "head"),
        p("기존 결과 파일은 덮어쓰지 않습니다. 모델 및 스키마 파일을 수정했거나 "
          "잘못된 열 순서로 입력하면 실행을 중단해야 합니다."),
        p("skops 파일 내부에는 학습 범주 메타데이터가 남을 수 있으므로 "
          "모델 ZIP은 해당 고객에게만 비공개 전달해야 합니다.", "small"),
        p("SHA-256은 무결성을 점검할 뿐 발신자를 인증하는 서명이 아닙니다.", "small"),
        PageBreak(),
        p("PREMIUM / 입력 스키마와 검수", "title"),
        p("입력 계약 요약", "head"),
        panel([
            ("필수 입력 열", f"{len(columns)}개 · 순서와 이름이 정확히 일치해야 함"),
            ("숫자형 입력", f"{len(raw_schema['numeric_raw_columns'])}개"),
            ("날짜형 변환", f"{len(raw_schema['datetime_features'])}개"),
            ("불리언 입력", f"{len(raw_schema['boolean_raw_columns'])}개"),
            ("학습용 전처리 열", f"{len(raw_schema['prepared_feature_columns'])}개"),
        ]),
        p("필수 열 미리보기", "head"),
        p(example_names or "필수 입력 열 없음"),
        p("전체 순서·유형 정보는 동봉된 model_schema.json이 기준입니다. "
          "목표 변수는 새로운 예측 CSV에 포함하지 않습니다.", "small"),
        p("납품 구성품", "head"),
        panel([
            ("model_pipeline.skops", "학습된 전처리 + 예측 모델; 신뢰된 원본만 로드"),
            ("model_schema.json", "입력 열 순서, 유형, 버전 및 모델 해시"),
            ("predict.py / predict.cmd", "동일 스키마 새 CSV를 예측하는 로컬 실행 도구"),
            ("sample_input.csv", "실제 고객 행을 담지 않은 빈 헤더 템플릿"),
            ("sample_predictions.csv", "예시 예측값을 조작하지 않은 빈 결과 헤더"),
        ]),
        p("반복 예측 전 체크", "head"),
        p("1) 원본 발신자 확인  2) Python/라이브러리 버전 일치  "
          "3) 열 이름·순서 확인  4) 출력 경로 중복 확인"),
        p("시간·고객별 반복 관측, 목표 누수, 데이터 분포 변화가 있다면 "
          "CV/holdout 점수를 실제 미래 성능처럼 사용하지 마세요.", "small"),
        p("중요한 의사결정에는 별도의 업무 검수 및 모델 위험 평가가 필요합니다.", "small"),
    ]
    out = BytesIO()
    SimpleDocTemplate(out, pagesize=A4, leftMargin=49, rightMargin=49,
                      topMargin=48, bottomMargin=52,
                      title="AI AutoML Analyst PREMIUM handover",
                      author="AI AutoML Analyst").build(story)
    return out.getvalue()


def windows_predict_command() -> bytes:
    """Exactly the batch file shipped to customers; exercise in Windows CI."""
    return (
        '@echo off\r\n'
        'if "%~2"=="" (echo Usage: predict.cmd new_data.csv predicted.csv [cp932] & exit /b 2)\r\n'
        'if "%~3"=="" (\r\n'
        '  python "%~dp0predict.py" --model-dir "%~dp0." --input "%~1" --output "%~2"\r\n'
        ') else (\r\n'
        '  python "%~dp0predict.py" --model-dir "%~dp0." --input "%~1" --output "%~2" --csv-encoding "%~3"\r\n'
        ')\r\n'
    ).encode("utf-8")


def _reject_unsafe_sample_headers(
    df: pd.DataFrame, target_column: str,
    group_column: str | None, time_column: str | None,
) -> None:
    """A PREMIUM CSV header is both an exact prediction schema and an Excel cell.

    Escaping these names in sample_input.csv would make the trusted predictor
    reject the template. Reject formula-shaped feature names *before* training
    rather than shipping an executable spreadsheet header or changing schema.
    """
    excluded = {target_column}
    if group_column is not None:
        excluded.add(group_column)
    if time_column is not None:
        excluded.add(time_column)
    for name in df.columns:
        if name not in excluded and isinstance(name, str) and name.lstrip().startswith(("=", "+", "-", "@")):
            raise ValueError(
                "PREMIUM cannot export a safe exact-schema CSV template with "
                "spreadsheet formula-like feature headers. Rename columns "
                "starting with =, +, - or @, then retry."
            )


def build_premium_zip(
    df: pd.DataFrame,
    target_column: str,
    task_type: str | None = None,
    split_policy: str = "random",
    group_column: str | None = None,
    time_column: str | None = None,
    cv: int = 3,
) -> bytes:
    # The generated sample_input.csv is opened in spreadsheets by customers.
    # Enforce its safe/exact column contract before expensive model fitting.
    _reject_unsafe_sample_headers(df, target_column, group_column, time_column)
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
        "selected_hyperparameters": analysis["selected_hyperparameters"],
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

    with ZipFile(BytesIO(build_basic_zip(df, report_tier="PREMIUM"))) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()
                 if name not in ("manifest.json", "README.txt", "report.pdf")}
        basic_pdf = archive.read("report.pdf")
    ml_chart = _comparison_plot(analysis)
    parts["charts/06_ml_comparison.png"] = ml_chart
    standard_pdf = _append_ml_pdf(basic_pdf, analysis, ml_chart, report_tier="PREMIUM")
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(standard_pdf)))
    writer.append(PdfReader(BytesIO(_premium_page(analysis, analysis["selected_model"], raw_schema))))
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
    parts["predict.cmd"] = windows_predict_command()
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
        "   일본어 Windows CSV(CP932)일 때: predict.cmd new_data.csv predicted.csv cp932\n"
        "   (일반 UTF-8/한국어 CSV는 기존 기본 실행 방식 유지)\n"
        "4) 모델은 오직 신뢰한 원본 ZIP에서 로드하세요. 모델 파일·스키마 SHA만으로 출처를 증명할 수 없습니다.\n"
        "5) 데이터는 외부로 보내지 않습니다. 기존 결과 파일은 덮어쓰지 않습니다.\n"
        "6) 홀드아웃 결과는 평가 당시 학습 모델에만 적용되며, 최종 전체 재학습 모델에 동일한 성능을 보장하지 않습니다.\n"
        + privacy_header_notice(inspect_header_privacy(df.columns)) + "\n"
        + font_usage_notice("".join(str(col) for col in df.columns), pdf_bytes=parts["report.pdf"])
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
