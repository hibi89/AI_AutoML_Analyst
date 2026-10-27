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
from backend.app.services.ml_feasibility import inspect_ml_feasibility


# ReportLab may embed a subset of the owner's installed NanumGothic font.
# This attribution travels inside the customer report ZIP; font binaries do not.
NANUM_FONT_CREDIT = (
    "한글 PDF 글꼴: NAVER 나눔고딕(NanumGothic) / "
    "Copyright (c) 2010 NAVER Corporation / SIL Open Font License 1.1\n"
    "라이선스: https://help.naver.com/service/30016/contents/18088\n"
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


def _numeric_profiles(df: pd.DataFrame) -> list[dict]:
    """Aggregate-only observed quartiles, never individual records or category values."""
    rows = []
    for name in _numeric(df)[:4]:
        values = pd.to_numeric(df[name], errors="coerce")
        values = values.replace([float("inf"), float("-inf")], float("nan")).dropna()
        if len(values) < 4:
            continue
        rows.append({
            "column": _display_name(name),
            "observed": int(len(values)),
            "q1": round(float(values.quantile(.25)), 2),
            "median": round(float(values.median()), 2),
            "q3": round(float(values.quantile(.75)), 2),
        })
    return rows


def _make_charts(df: pd.DataFrame, quality: list[dict]) -> list[tuple[str, bytes, str]]:
    """Use the P6 branded chart designer across BASIC / STANDARD / PREMIUM."""
    from backend.app.services.chart_design import create_charts
    return create_charts(df, quality)


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
        canvas.setFillColor(colors.HexColor("#087f8c"))
        canvas.rect(44, h-33, 45, 3, stroke=0, fill=1)
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#6c8492"))
        canvas.drawString(44, 31, "AI AutoML Analyst  |  BASIC 데이터 진단 보고서")
        canvas.drawRightString(w-44, 31, f"{doc.page}")
        canvas.restoreState()

    story = [
        Spacer(1, 16),
        paragraph("AI AUTOML ANALYST   /   DATA INTELLIGENCE", "small"),
        paragraph("데이터 진단 및 핵심 인사이트", "title"),
        paragraph("BASIC  /  EXPLORATORY DATA REPORT", "small"),
        paragraph("이 보고서는 제공된 표형 데이터의 품질 및 관측 분포를 요약합니다. "
                  "ML 모델 학습이나 미래 예측, 인과관계 판단은 포함하지 않습니다.", "small"),
        Spacer(1, 14),
        heading("핵심 지표"),
    ]
    # Compact KPI scorecards make the first page useful at a glance.
    metrics = summary["metrics"]
    rows_kpi = []
    for i in range(0, len(metrics), 2):
        pair = metrics[i:i+2]
        cells = []
        for metric in pair:
            label = paragraph(metric["name"] + "  ·  " + metric["basis"], "small")
            value_style = ParagraphStyle(
                f"kpi_value_{i}_{len(cells)}",
                parent=styles["section"], fontSize=19, leading=27,
                textColor=colors.HexColor("#173e58"), spaceAfter=1,
            )
            value = Paragraph(escape(str(metric["value"])), value_style)
            cells.append([label, value])
        while len(cells) < 2:
            cells.append("")
        rows_kpi.append(cells)
    kpi_table = Table(rows_kpi, colWidths=[237, 237], hAlign="LEFT")
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F0F6F8")),
        ("BOX", (0,0), (-1,-1), .5, colors.HexColor("#D5E7EA")),
        ("INNERGRID", (0,0), (-1,-1), 4, colors.white),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 14),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(kpi_table)
    story.extend([Spacer(1, 17), heading("주요 발견")])
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
    story.append(Spacer(1, 18))
    story.append(heading("분석 해석의 전제"))
    story.append(paragraph("관측 가능한 값만 정리했으며 누락, 극단값, 중복 기록을 오류로 단정하지 않습니다. "
                           "자료의 수집 과정과 숫자 단위는 의뢰인이 확인해야 합니다.", "small"))
    story.append(paragraph("데이터의 여러 열을 함께 살펴볼 경우에도 관측 상관관계가 원인이나 "
                           "미래 변화에 대한 근거는 아닙니다.", "small"))
    story.append(paragraph(f"선별된 그래프 {len(charts)}개는 다음 페이지에 수록되며, "
                           "원본 데이터 행 및 실제 범주 이름은 이미지에 포함하지 않습니다.", "small"))

    chart_labels = {
        "distribution": "수치형 분포", "missing": "결측 현황",
        "correlation": "수치형 변수 관계", "categories": "범주별 빈도",
        "box": "값의 변동 범위", "trend": "월별 관측 추이",
    }
    # Two charts per page reduce excessive whitespace without cramming figures.
    for page_start in range(0, len(charts), 2):
        story.extend([PageBreak(), heading("데이터 시각화")])
        for chart_index in range(page_start, min(page_start + 2, len(charts))):
            filename, png, note = charts[chart_index]
            slug = filename.rsplit("/", 1)[-1].replace(".png", "").split("_", 1)[-1]
            label = chart_labels.get(slug, "데이터 요약")
            story.append(paragraph(f"{chart_index + 1:02d}  {label}", "small"))
            img = Image(BytesIO(png))
            # The source chart is 8 x 4.5 inches; preserve its aspect ratio.
            img.drawWidth, img.drawHeight = 455, 254
            story.extend([img, Spacer(1, 7), paragraph(note, "small"),
                          Spacer(1, 10)])
        # On a last single-chart page, add independently observed numeric
        # summaries; do not invent a filler plot or restate category values.
        profiles = summary.get("numeric_profiles", [])
        if page_start + 1 == len(charts) and profiles:
            story.extend([Spacer(1, 7), heading("관측 수치의 사분위 요약")])
            profile_rows = [[
                paragraph("수치형 열", "small"), paragraph("유효행", "small"),
                paragraph("Q1", "small"), paragraph("중앙값", "small"),
                paragraph("Q3", "small"),
            ]]
            for p in profiles:
                profile_rows.append([
                    paragraph(str(p["column"])[:28], "small"),
                    f'{p["observed"]:,}', f'{p["q1"]:,.2f}',
                    f'{p["median"]:,.2f}', f'{p["q3"]:,.2f}',
                ])
            profiles_table = Table(
                profile_rows, colWidths=[166, 60, 84, 84, 84],
                repeatRows=1, hAlign="LEFT",
            )
            profiles_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCECF5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#F4F8FA")]),
                ("BOX", (0, 0), (-1, -1), .4, colors.HexColor("#D6E4EB")),
                ("LINEBELOW", (0, 0), (-1, -2), .3, colors.HexColor("#D6E4EB")),
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(profiles_table)
            story.append(paragraph(
                "유효한 수치만 사용한 관측 사분위수입니다. 원본 단위와 표본 정의를 확인하세요.",
                "small",
            ))

    story.extend([PageBreak(), heading("발견과 다음 행동")])
    for line in summary["findings"]:
        story.append(paragraph("• " + line))
    story.extend([Spacer(1, 14), heading("확인 권고")])
    for line in summary["suggestions"]:
        story.append(paragraph("• " + line))
    story.extend([Spacer(1, 14), heading("ML 적용 가능성")])
    story.append(paragraph("분류/회귀의 목적 변수와 관측 시점, 미래 정보 누수 여부를 먼저 정의해야 합니다. "
                           "이 BASIC 보고서에는 모델 적합, 정확도 비교, 자동 목표 확정이 포함되지 않습니다."))
    feasibility = summary["ml_feasibility"]
    if feasibility["candidates"]:
        hints = " / ".join(
            f"{str(item['column'])[:20]} ({item['inspection_type']})"
            for item in feasibility["candidates"]
        )
        story.append(paragraph(
            "업무 목표 확인용 열 후보: " + hints
            + ". 입력 열 이름과 고유값·결측만 검토했습니다. 실제 목표 선정은 의뢰인이 해야 합니다.",
            "small",
        ))
    else:
        story.append(paragraph(
            "목표열을 검토할 충분한 근거가 없습니다. 의뢰인의 업무 목적과 정답 열 정의가 필요합니다.",
            "small",
        ))
    if feasibility["constraints"]:
        story.append(paragraph("진단 제약: " + feasibility["constraints"][0], "small"))
    profiles = summary.get("numeric_profiles", [])
    if profiles:
        # Quantitative candidates are only inspection aids, never automatic ML
        # target recommendations, task-type inference, or feasibility promises.
        story.extend([Spacer(1, 9), heading("목표열 검토 전 확인할 수치형 현황")])
        quality_by_name = {_display_name(q["column"]): q for q in summary["quality"]}
        audit_rows = [[paragraph("수치형 열", "small"), paragraph("유효 행", "small"),
                       paragraph("고유값", "small"), paragraph("결측률", "small")]]
        for p in profiles:
            q = quality_by_name.get(p["column"], {})
            audit_rows.append([
                paragraph(str(p["column"])[:24], "small"),
                f'{p["observed"]:,}',
                str(q.get("unique", "-")),
                f'{q.get("missing_pct", 0):.1f}%',
            ])
        audit = Table(audit_rows, colWidths=[224, 84, 84, 84], hAlign="LEFT")
        audit.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCECF5")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F4F8FA")]),
            ("BOX", (0, 0), (-1, -1), .3, colors.HexColor("#D6E4EB")),
            ("LINEBELOW", (0, 0), (-1, -2), .3, colors.HexColor("#D6E4EB")),
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(audit)
        story.append(paragraph("위 열 목록은 관측 요약일 뿐 ML 목표 변수나 분석 목적을 추천하지 않습니다.", "small"))
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
        "numeric_profiles": _numeric_profiles(df),
        "ml_feasibility": inspect_ml_feasibility(df),
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
                       "누락/중복은 오류로 단정할 수 없습니다.\n"
                       + NANUM_FONT_CREDIT).encode("utf-8"),
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
