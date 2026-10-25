"""BASIC delivery: meaningful aggregate charts, Korean PDF, safe ZIP manifest.

No raw data rows, values of private categorical labels, or customer files are
persisted here. Only aggregate statistics and chart images are exported.
"""
from __future__ import annotations

import csv
from datetime import datetime
from io import BytesIO, StringIO
import json
import math
import os
from pathlib import Path
import re
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from backend.app.services.basic_report import (
    _csv_safe, _quality_rows, validate_basic_frame,
)


def _number(value: object) -> str:
    return f"{float(value):,.2f}"


def _numeric(df: pd.DataFrame) -> list[str]:
    return [
        str(col) for col in df.select_dtypes(include="number").columns
        if df[col].nunique(dropna=True) >= 2
    ]


def _display_name(col: object) -> str:
    return str(col).replace("\n", " ")[:48]


def _date_column(df: pd.DataFrame) -> tuple[str, pd.Series] | None:
    for col in df.columns:
        name = str(col).lower()
        if not any(h in name for h in ("date", "time", "날짜", "일자")):
            continue
        sample = df[col].dropna().astype(str)
        if sample.empty:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        if parsed.notna().sum() >= max(8, int(0.8 * len(sample))):
            return str(col), parsed
    return None


def _build_metrics(df: pd.DataFrame, quality: list[dict]) -> list[dict]:
    n = len(df)
    missing = int(df.isna().sum().sum())
    dupes = int(df.duplicated().sum())
    metrics = [
        {"name": "전체 행", "value": f"{n:,}", "basis": "원본 관측 행 수"},
        {"name": "전체 열", "value": str(len(df.columns)), "basis": "컬럼 수"},
        {"name": "누락 셀", "value": f"{missing:,}", "basis": "null 기준"},
        {"name": "누락 비율", "value": f"{100 * missing / (n * len(df.columns)):.2f}%", "basis": "전체 셀 중 누락"},
        {"name": "중복 행", "value": f"{dupes:,}", "basis": "전체 컬럼 완전 일치"},
        {"name": "수치형 열", "value": str(len(df.select_dtypes(include="number").columns)), "basis": "pandas dtype"},
        {"name": "상수/전부 누락 열", "value": str(sum(q["unique"] <= 1 for q in quality)), "basis": "고유값 1개 이하"},
    ]
    nums = _numeric(df)
    if nums:
        first = nums[0]
        vals = pd.to_numeric(df[first], errors="coerce").dropna()
        if len(vals):
            metrics.append({"name": "대표 수치형 중앙값", "value": _number(vals.median()), "basis": f"'{_display_name(first)}' 열"})
    if len(nums) >= 2:
        metrics.append({"name": "분석 가능한 수치형 열", "value": str(len(nums)), "basis": "고유값 두 개 이상"})
    return metrics[:10]


def _insights(df: pd.DataFrame, quality: list[dict]) -> tuple[list[str], list[str]]:
    missing = sum(q["missing"] for q in quality)
    duplicates = int(df.duplicated().sum())
    findings = [
        f"전체 {len(df):,}행과 {len(df.columns)}개 열을 대상으로 진단했습니다.",
        f"결측 셀은 {missing:,}개이며, 전체 셀 중 {100 * missing / (len(df) * len(df.columns)):.2f}%입니다.",
        f"모든 열이 동일한 중복 행은 {duplicates:,}개입니다.",
    ]
    numeric_cols = _numeric(df)
    if numeric_cols:
        x = pd.to_numeric(df[numeric_cols[0]], errors="coerce").dropna()
        if len(x):
            findings.append(
                f"수치형 '{_display_name(numeric_cols[0])}'의 중앙값은 {_number(x.median())}입니다."
            )
    missing_cols = [q for q in quality if q["missing"]]
    if missing_cols:
        most = max(missing_cols, key=lambda x: x["missing_pct"])
        findings.append(
            f"결측 비율이 가장 높은 열은 '{_display_name(most['column'])}'로 {most['missing_pct']:.2f}%입니다."
        )
    elif any(q["unique"] <= 1 for q in quality):
        findings.append("고유값이 한 가지 이하인 열이 있어 활용 가능성을 검토해야 합니다.")
    suggestions = []
    if missing:
        suggestions.append("결측이 수집/입력 과정에서 생긴 것인지 확인한 뒤 대체 또는 제외 기준을 정하세요.")
    if duplicates:
        suggestions.append("동일 행이 실제 중복 기록인지 반복 측정인지 원본 정의를 확인하세요.")
    suggestions.append("예측 목표, 관측 시점, 학습에 사용할 설명변수를 먼저 정의한 후 모델 실험을 진행하세요.")
    return findings[:5], suggestions[:3]


def _make_charts(df: pd.DataFrame, quality: list[dict]) -> list[tuple[str, bytes, str]]:
    """Create at most 5 schema-justified charts; never pad to a fixed count."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import numpy as np

    artifacts: list[tuple[str, bytes, str]] = []

    def capture(slug: str, title: str, note: str, drawing) -> None:
        if len(artifacts) >= 5:
            return
        fig, ax = plt.subplots(figsize=(8.0, 4.5))
        try:
            drawing(ax)
            ax.set_title(title, fontsize=13, pad=12)
            fig.tight_layout(pad=1.5)
            buffer = BytesIO()
            fig.savefig(buffer, format="png", dpi=130)
            artifacts.append((f"charts/{len(artifacts)+1:02d}_{slug}.png", buffer.getvalue(), note))
        finally:
            plt.close(fig)

    numeric = _numeric(df)
    if numeric:
        col = numeric[0]
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) >= 8:
            capture("distribution", "Numeric distribution", f"'{_display_name(col)}' 열의 관측 분포입니다.",
                    lambda ax: (ax.hist(vals, bins=min(20, max(5, int(math.sqrt(len(vals))))),
                                        edgecolor="white"), ax.set_xlabel("Observed value"),
                                ax.set_ylabel("Count")))

    missing = [q for q in quality if q["missing"]]
    if missing:
        worst = sorted(missing, key=lambda q: -q["missing_pct"])[:12]
        capture("missing", "Missing values by column",
                "누락이 있는 상위 열의 결측률 비교입니다. 원본 데이터 값은 노출하지 않습니다.",
                lambda ax: (ax.barh([f"Column {i+1}" for i in range(len(worst))],
                                     [q["missing_pct"] for q in worst]),
                            ax.set_xlabel("Missing (%)")))

    if len(numeric) >= 2:
        # Correlation requires at least 8 complete paired rows and variability.
        corr_df = df[numeric[:8]].apply(pd.to_numeric, errors="coerce")
        pairs = corr_df.dropna()
        if len(pairs) >= 8 and pairs.shape[1] >= 2:
            matrix = pairs.corr()
            if bool(matrix.notna().all().all()):
                def draw_corr(ax):
                    im = ax.imshow(matrix.to_numpy(), vmin=-1, vmax=1, cmap="coolwarm")
                    labels = [f"N{i+1}" for i in range(len(matrix))]
                    ax.set_xticks(range(len(labels)), labels)
                    ax.set_yticks(range(len(labels)), labels)
                    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                capture("correlation", "Numeric correlation (Pearson)",
                        "완전 관측된 수치열의 상관계수입니다. 상관관계는 인과관계를 뜻하지 않습니다.",
                        draw_corr)

    cat_cols = [
        col for col in df.select_dtypes(include=["object", "category", "string", "bool"]).columns
        if len(df) >= 8
        and 2 <= df[col].nunique(dropna=True) <= 15
        and col != (_date_column(df) or (None,))[0]
    ]
    if cat_cols:
        col = cat_cols[0]
        counts = df[col].value_counts().head(6)
        if len(counts) >= 2:
            capture("categories", "Category frequency (anonymized)",
                    f"'{_display_name(col)}' 열의 상위 범주 빈도입니다. 범주 이름은 익명화했습니다.",
                    lambda ax: (ax.bar([f"Group {i+1}" for i in range(len(counts))], counts.to_numpy()),
                                ax.set_ylabel("Row count")))

    if numeric:
        col = numeric[0]
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) >= 8:
            capture("box", "Numeric spread / outliers",
                    f"'{_display_name(col)}' 열의 사분위범위 및 외곽 관측입니다. 이상치는 오류로 단정할 수 없습니다.",
                    lambda ax: (ax.boxplot(vals.to_numpy()),
                                ax.set_xticks([1], ["Numeric N1"]), ax.set_ylabel("Observed value")))

    # Valid dates contribute a trend chart when previous categories did not fill cap.
    if len(artifacts) < 5 and numeric:
        date = _date_column(df)
        if date:
            _, dates = date
            series = pd.Series(pd.to_numeric(df[numeric[0]], errors="coerce").to_numpy(), index=dates)
            series = series[series.index.notna()].dropna()
            if len(series) >= 8 and series.index.normalize().nunique() >= 3:
                trends = series.resample("MS").mean().dropna()
                if len(trends) >= 3:
                    capture("trend", "Monthly numeric mean", "월별 평균이며 원인이나 미래 추세를 예측하지 않습니다.",
                            lambda ax: (ax.plot(range(len(trends)), trends.to_numpy(), marker="o"),
                                        ax.set_xticks(range(len(trends)), [x.strftime("%Y-%m") for x in trends.index],
                                                      rotation=25), ax.set_ylabel("Mean")))
    return artifacts


def _korean_font() -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    env = os.environ.get("AUTOML_KOREAN_FONT_PATH", "")
    paths = [
        Path(env) if env else None,
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
        Path("/usr/local/share/fonts/NanumGothic.ttf"),
        Path("C:/Windows/Fonts/NanumGothic.ttf"),
        Path.home() / "AppData/Local/Microsoft/Windows/Fonts/NanumGothic.ttf",
    ]
    font_file = next((p for p in paths if p is not None and p.is_file()), None)
    if font_file is None:
        raise RuntimeError(
            "Korean PDF font missing: install NanumGothic (fonts-nanum) or set "
            "AUTOML_KOREAN_FONT_PATH to a licensed NanumGothic TTF."
        )
    font_key = "AutoMLNanumGothic"
    if font_key not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_key, str(font_file)))
    return font_key


def _pdf(summary: dict, charts: list[tuple[str, bytes, str]]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, PageBreak, KeepTogether,
    )

    font = _korean_font()
    out = BytesIO()
    styles = {
        "title": ParagraphStyle("title", fontName=font, fontSize=26, leading=34,
                                textColor=colors.HexColor("#173e58"), spaceAfter=20),
        "section": ParagraphStyle("section", fontName=font, fontSize=16, leading=24,
                                  textColor=colors.HexColor("#145f91"), spaceAfter=16),
        "body": ParagraphStyle("body", fontName=font, fontSize=10.4, leading=18,
                               textColor=colors.HexColor("#233648"), spaceAfter=9),
        "small": ParagraphStyle("small", fontName=font, fontSize=9, leading=15,
                                textColor=colors.HexColor("#607789"), spaceAfter=8),
    }

    def paragraph(text: str, style="body"):
        return Paragraph(escape(str(text)), styles[style])

    def heading(title: str):
        return paragraph(title, "section")

    def footer(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setStrokeColor(colors.HexColor("#d4e3eb"))
        canvas.line(44, 45, w-44, 45)
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#6c8492"))
        canvas.drawString(44, 31, "AI AutoML Analyst  |  BASIC 데이터 진단 보고서")
        canvas.drawRightString(w-44, 31, f"{doc.page}")
        canvas.restoreState()

    story = [
        Spacer(1, 28),
        paragraph("AI AutoML Analyst", "small"),
        paragraph("데이터 진단 및 핵심 인사이트", "title"),
        paragraph("BASIC | 탐색적 데이터 분석"),
        paragraph("이 보고서는 제공된 표형 데이터의 품질 및 관측 분포를 요약합니다. "
                  "ML 모델 학습이나 미래 예측, 인과관계 판단은 포함하지 않습니다.", "small"),
        Spacer(1, 14),
        heading("핵심 지표"),
    ]
    for m in summary["metrics"]:
        story.append(paragraph(f"• {m['name']}: {m['value']} ({m['basis']})"))
    story.extend([Spacer(1, 15), heading("주요 발견")])
    for line in summary["findings"][:3]:
        story.append(paragraph("• " + line))

    story.extend([PageBreak(), heading("데이터 품질 진단")])
    story.append(paragraph(f"전체 행 {summary['rows']:,}개 · 전체 열 {summary['columns']}개 · "
                           f"중복 행 {summary['duplicate_rows']:,}개"))
    rows = [["열 이름", "유형", "결측", "결측률", "고유값"]]
    for q in summary["quality"][:18]:
        rows.append([_display_name(q["column"])[:22], str(q["dtype"])[:13],
                     str(q["missing"]), f"{q['missing_pct']:.1f}%", str(q["unique"])])
    table = Table(rows, colWidths=[160, 105, 55, 68, 55], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), font),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dcecf5")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f4f8fa")]),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#dae5eb")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(table)
    if len(summary["quality"]) > 18:
        story.append(paragraph("전체 열의 품질 진단은 summary.csv에 포함됩니다.", "small"))
    story.append(Spacer(1, 20))
    story.append(paragraph("수치형의 극단값·결측·중복은 데이터 오류가 아닐 수도 있습니다. "
                           "원본 수집/측정 단위를 반드시 확인하세요.", "small"))

    for index, (filename, png, note) in enumerate(charts, start=1):
        story.extend([PageBreak(), paragraph(f"시각화 {index:02d}", "small"),
                      heading(filename.rsplit("/",1)[-1].replace(".png","").replace("_"," ").title())])
        img = Image(BytesIO(png))
        # Chart has 8x4.5 aspect; fit well within A4 without stretching.
        img.drawWidth, img.drawHeight = 490, 275
        story.extend([Spacer(1, 22), img, Spacer(1, 25), paragraph(note),
                      paragraph("차트는 요약된 분포입니다. 통계적 관계만으로 원인을 확정할 수 없습니다.", "small")])

    story.extend([PageBreak(), heading("발견과 다음 행동")])
    for line in summary["findings"]:
        story.append(paragraph("• " + line))
    story.extend([Spacer(1, 14), heading("확인 권고")])
    for line in summary["suggestions"]:
        story.append(paragraph("• " + line))
    story.extend([Spacer(1, 14), heading("ML 적용 가능성")])
    story.append(paragraph("분류/회귀의 목적 변수와 관측 시점, 미래 정보 누수 여부를 먼저 정의해야 합니다. "
                           "이 BASIC 보고서에는 모델 적합, 정확도 비교, 자동 목표 확정이 포함되지 않습니다."))
    story.extend([Spacer(1, 10),
                  paragraph("방법: 데이터프레임의 관측 행 수, 결측률, 고유값, 중복행, 기술통계 및 "
                            "지원되는 차트를 생성했습니다. 범주 값과 개별 행은 ZIP에 넣지 않습니다.", "small"),
                  paragraph("주의: 데이터 정합성, 대표성, 편향, 수집 맥락은 자동 진단만으로 확인할 수 없습니다.", "small")])
    document = SimpleDocTemplate(out, pagesize=A4, leftMargin=44, rightMargin=44,
                                 topMargin=48, bottomMargin=60, title="AI AutoML Analyst BASIC",
                                 author="AI AutoML Analyst")
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()


def build_basic_delivery(df: pd.DataFrame) -> bytes:
    validate_basic_frame(df)
    quality = _quality_rows(df)
    findings, suggestions = _insights(df, quality)
    metrics = _build_metrics(df, quality)
    charts = _make_charts(df, quality)
    summary = {
        "version": "basic-p3-v1",
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "findings": findings,
        "suggestions": suggestions,
        "metrics": metrics,
        "quality": quality,
        "chart_count": len(charts),
        "chart_captions": {name: note for name, _, note in charts},
        "disclaimer": "Descriptive only, no ML fit, no causal claim.",
    }
    pdf = _pdf(summary, charts)
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["column", "dtype", "missing", "missing_pct", "unique"])
    for q in quality:
        writer.writerow([_csv_safe(q["column"]), q["dtype"],
                         q["missing"], q["missing_pct"], q["unique"]])
    parts = {
        "report.pdf": pdf,
        "summary.csv": ("\ufeff" + buf.getvalue()).encode("utf-8"),
        "summary.json": json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"),
        "README.txt": ("AI AutoML Analyst BASIC\n이 파일은 기술통계 및 시각화 결과입니다.\n"
                       "인과분석/ML 학습/정확도 보장이 아닙니다.\n"
                       "누락/중복은 오류로 단정할 수 없습니다.\n").encode("utf-8"),
    }
    parts.update({name: content for name, content, _ in charts})
    import hashlib
    manifest = {
        "format": "basic-v1",
        "files": [{"path": k, "bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()}
                  for k, v in sorted(parts.items())],
        "no_raw_dataset": True,
    }
    parts["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    out = BytesIO()
    with ZipFile(out, "w", compression=ZIP_DEFLATED) as z:
        for name, content in parts.items():
            z.writestr(name, content)
    return out.getvalue()
