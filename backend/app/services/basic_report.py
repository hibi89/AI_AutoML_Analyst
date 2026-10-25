"""Local, synthetic-safe BASIC MVP diagnostics and ZIP packaging.

This is intentionally a Markdown/PNG MVP, NOT a customer-ready PDF report.
No dataset rows or raw uploaded CSV are persisted or bundled.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile

import pandas as pd

MAX_UPLOAD_BYTES = 30 * 1024 * 1024
MAX_ROWS = 20_000
MAX_COLUMNS = 50


def validate_basic_frame(df: pd.DataFrame) -> None:
    if df.empty or len(df.columns) == 0:
        raise ValueError("CSV has no usable rows or columns.")
    if len(df) > MAX_ROWS or len(df.columns) > MAX_COLUMNS:
        raise ValueError(f"Limit exceeded: max {MAX_ROWS} rows / {MAX_COLUMNS} columns.")
    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names are not supported.")
    if not all(isinstance(x, str) and x.strip() for x in df.columns):
        raise ValueError("All columns must have non-empty text names.")


def _csv_safe(value: object) -> str:
    """Prevent spreadsheet formula execution when exported CSV is opened."""
    result = str(value)
    if result and result.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + result
    return result


def _quality_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for col in df.columns:
        values = df[col]
        rows.append(
            {
                "column": str(col),
                "dtype": str(values.dtype),
                "missing": int(values.isna().sum()),
                "missing_pct": round(float(values.isna().mean() * 100), 2),
                "unique": int(values.nunique(dropna=True)),
            }
        )
    return rows


def _render_chart(df: pd.DataFrame, quality: list[dict]) -> bytes | None:
    # Import lazily, allowing legacy AutoML endpoints to run without rendering.
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    numeric_columns = [
        col for col in df.select_dtypes(include="number").columns
        if df[col].nunique(dropna=True) > 1
    ]
    try:
        if numeric_columns:
            col = numeric_columns[0]
            numeric = pd.to_numeric(df[col], errors="coerce").dropna()
            if numeric.empty:
                return None
            ax.hist(numeric, bins=min(15, max(3, int(len(numeric) ** 0.5))), edgecolor="white")
            ax.set_title("Numeric value distribution")
            ax.set_xlabel(str(col)[:60])
            ax.set_ylabel("Number of rows")
        elif any(item["missing"] for item in quality):
            nonzero = [item for item in quality if item["missing"]][:12]
            ax.bar(range(len(nonzero)), [item["missing_pct"] for item in nonzero])
            ax.set_xticks(range(len(nonzero)), [x["column"][:12] for x in nonzero], rotation=35, ha="right")
            ax.set_ylabel("Missing (%)")
            ax.set_title("Missing values by column")
        else:
            candidates = [
                col for col in df.columns
                if 2 <= df[col].nunique(dropna=True) <= 15
            ]
            if not candidates:
                return None
            counts = df[candidates[0]].value_counts(dropna=True).head(6)
            # Aggregate labels prevent chart images disclosing raw category values.
            ax.bar([f"Group {i + 1}" for i in range(len(counts))], counts.to_numpy())
            ax.set_title("Top category frequencies (labels anonymized)")
            ax.set_ylabel("Number of rows")
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120)
        return buffer.getvalue()
    finally:
        plt.close(fig)


def build_basic_zip(df: pd.DataFrame) -> bytes:
    """Build a ZIP for a single bounded DataFrame, no ML training."""
    validate_basic_frame(df)
    quality = _quality_rows(df)
    duplicates = int(df.duplicated().sum())
    missing_cells = int(df.isna().sum().sum())
    numerics = df.select_dtypes(include="number").columns.tolist()

    findings = [
        f"전체 {len(df):,}행, {len(df.columns)}열의 표 형식 데이터입니다.",
        f"전체 결측 셀은 {missing_cells:,}개입니다.",
        f"완전히 동일한 중복 행은 {duplicates:,}개입니다.",
    ]
    if numerics:
        col = numerics[0]
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if not vals.empty:
            findings.append(
                f"숫자형 '{col}' 컬럼 중앙값은 {float(vals.median()):,.3g}입니다."
            )
    if any(x["unique"] <= 1 for x in quality):
        findings.append("값이 한 종류 이하인 컬럼이 있어 분석 효용을 검토해야 합니다.")

    suggestions = []
    if missing_cells:
        suggestions.append("결측의 발생 원인과 대체/제외 기준을 확인하세요.")
    if duplicates:
        suggestions.append("중복 행이 관측 단위상 실제 중복인지 확인하세요.")
    suggestions.append("예측하려는 목표값과 관측 시점을 정의한 후 ML 적합성을 검토하세요.")
    suggestions = suggestions[:3]

    report = "\n".join(
        [
            "# AI AutoML Analyst | BASIC MVP",
            "",
            "이 문서는 자동화된 탐색적 데이터 진단 초안입니다. 최종 유료 PDF 산출물이 아닙니다.",
            "통계적 상관이나 분포만으로 인과관계를 주장하지 않습니다.",
            "",
            "## 데이터 개요",
            f"- 행: {len(df):,}",
            f"- 열: {len(df.columns)}",
            f"- 숫자형 열: {len(numerics)}",
            f"- 결측 셀: {missing_cells:,}",
            f"- 중복 행: {duplicates:,}",
            "",
            "## 확인된 사실",
            *[f"- {item}" for item in findings],
            "",
            "## 권장 점검",
            *[f"- {item}" for item in suggestions],
            "",
            "## 분석 한계",
            "- ML 모델 학습, 예측 성능 검증, 데이터 누수 판단은 포함하지 않습니다.",
            "- 컬럼별 품질 지표는 summary.csv를 참고하세요.",
            "- 원본 데이터는 ZIP에 포함되지 않습니다.",
            "",
        ]
    )

    text_buffer = io.StringIO()
    writer = csv.writer(text_buffer)
    writer.writerow(["column", "dtype", "missing", "missing_pct", "unique"])
    for row in quality:
        writer.writerow([_csv_safe(row["column"]), row["dtype"], row["missing"], row["missing_pct"], row["unique"]])

    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": missing_cells,
        "duplicate_rows": duplicates,
        "findings": findings,
        "suggestions": suggestions,
        "quality": quality,
        "report_status": "mvp_markdown_not_sale_ready",
    }
    chart = _render_chart(df, quality)

    dest = io.BytesIO()
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("report.md", report.encode("utf-8"))
        bundle.writestr("summary.csv", ("\ufeff" + text_buffer.getvalue()).encode("utf-8"))
        bundle.writestr("summary.json", json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
        bundle.writestr(
            "README.txt",
            "BASIC MVP 초안 — 검증/판매 전 PDF, 추가 차트, QA 필요.\n원본 데이터 미포함.\n",
        )
        if chart:
            bundle.writestr("charts/01_distribution.png", chart)
    return dest.getvalue()
