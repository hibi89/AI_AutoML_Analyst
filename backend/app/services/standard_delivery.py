"""STANDARD deliverable: P3 BASIC pages + independent, CV-selected ML evaluation."""
from __future__ import annotations

from backend.app.services.font_coverage import font_usage_notice

from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile
import csv
import hashlib
import json
from xml.sax.saxutils import escape

import pandas as pd

from backend.app.services.basic_report import _csv_safe, build_basic_zip
from backend.app.services.basic_p3 import _korean_font, NANUM_FONT_CREDIT
from backend.app.services.standard_engine import run_standard


def _comparison_plot(analysis: dict) -> bytes:
    """Compact, annotated CV scorecard with clear model/baseline distinctions."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib import font_manager
    from pathlib import Path
    import os

    font_paths = [
        os.environ.get("AUTOML_KOREAN_FONT_PATH", ""),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
    ]
    font_path = next((p for p in font_paths if p and Path(p).is_file()), None)
    korean_font = font_manager.FontProperties(fname=font_path) if font_path else None
    font_options = {"fontproperties": korean_font} if korean_font else {}

    rows = [r for r in analysis["models"] if r["status"] == "success"]
    names = [r["model"].replace("_classifier", "").replace("_regressor", "")
             .replace("_", " ").title() for r in rows]
    values = [r["cv_primary"] for r in rows]
    fig, ax = plt.subplots(figsize=(8.6, 4.85), facecolor="#F5F8FC")
    try:
        ax.set_facecolor("#FFFFFF")
        left = min(0.0, min(values) - .12) if values else 0
        right = max(0.1, max(values) + .18) if values else 1
        span = right - left
        selected = analysis["selected_model"]
        palette = [
            "#AAB9C9" if r["role"] == "baseline"
            else "#147D99" if r["model"] == selected
            else "#80BAC8" for r in rows
        ]
        bars = ax.barh(range(len(rows)), values, color=palette, height=.52,
                       edgecolor="none", zorder=3)
        ax.invert_yaxis()
        ax.set_xlim(left, right)
        ax.set_yticks(range(len(names)), names, fontsize=9, color="#263D53")
        ax.tick_params(axis="y", length=0, pad=11)
        ax.tick_params(axis="x", colors="#688092", length=0, labelsize=8)
        ax.xaxis.grid(True, color="#E3EBF2", linewidth=.9, zorder=0)
        ax.axvline(0, linewidth=.8, color="#748DA2", alpha=.5)
        for edge in ax.spines.values():
            edge.set_visible(False)
        for row, bar, value in zip(rows, bars, values):
            ax.text(value + .018 * span, bar.get_y() + bar.get_height()/2,
                    f"{value:.3f}", va="center", ha="left",
                    fontsize=9, color="#17364B", fontweight="bold")
            if row["role"] == "baseline":
                bar.set_hatch("///")
        metric = analysis["primary_metric"]
        heading = "학습 데이터 교차검증 · 모델 비교" if korean_font else "Training cross-validation · model scorecard"
        fig.text(.075, .935, heading, fontsize=15, fontweight="bold",
                 color="#17364B", **font_options)
        subtitle = ("기준선(Dummy) / CV 선정 모델 / 기타 후보" if korean_font
                    else "Dummy baseline / CV-selected model / other candidates")
        fig.text(.075, .884, subtitle, fontsize=9, color="#5C7386", **font_options)
        ax.set_xlabel(f"{metric}  |  CV mean (higher = better)",
                      fontsize=9, color="#48637B", labelpad=12)
        fig.subplots_adjust(left=.32, right=.92, top=.77, bottom=.19)
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=145, facecolor=fig.get_facecolor())
        return buf.getvalue()
    finally:
        plt.close(fig)


def _append_ml_pdf(original: bytes, analysis: dict, chart_png: bytes) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
    )
    from pypdf import PdfReader, PdfWriter

    from backend.app.services.font_coverage import resolve_report_fonts, safe_pdf_markup
    required = "".join(str(value) for value in analysis.get("feature_columns", []))
    font, fallback_font = resolve_report_fonts(required)
    styles = {
        "title": ParagraphStyle("s_title", fontName=font, fontSize=19, leading=26,
                                textColor=colors.HexColor("#153d5c"), spaceAfter=18),
        "head": ParagraphStyle("s_head", fontName=font, fontSize=12, leading=19,
                               textColor=colors.HexColor("#135e8a"), spaceAfter=12),
        "body": ParagraphStyle("s_body", fontName=font, fontSize=9.8, leading=17,
                               spaceAfter=11, textColor=colors.HexColor("#253846")),
        "small": ParagraphStyle("s_small", fontName=font, fontSize=8.4, leading=13,
                                spaceAfter=7, textColor=colors.HexColor("#526778")),
    }
    def para(text, style="body"):
        return Paragraph(safe_pdf_markup(text, font, fallback_font), styles[style])
    def footer(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor("#647d8c"))
        c.setFont(font, 8)
        c.drawString(45, 31, "AI AutoML Analyst  |  STANDARD 모델 검증")
        c.drawRightString(A4[0] - 45, 31, f"ML {doc.page}")
        c.restoreState()

    main_rows = [["후보 모델", "유형", "CV 평균", "CV 표준편차", "상태"]]
    for r in analysis["models"]:
        name = r["model"].replace("_classifier", "").replace("_regressor", "")
        main_rows.append([
            name[:22], "기준선" if r["role"] == "baseline" else "비교 모델",
            f"{r['cv_primary']:.4f}" if r["cv_primary"] is not None else "-",
            f"{r['cv_std']:.4f}" if r["cv_std"] is not None else "-",
            "성공" if r["status"] == "success" else "제외",
        ])
    table = Table(main_rows, colWidths=[177, 82, 72, 81, 65], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcecf5")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbdde6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))

    metrics = analysis["selected_holdout_metrics"]
    dummy = analysis["dummy_holdout_metrics"]
    p = analysis["primary_metric"]
    # Visual methodology card: actual data partitions and non-overlapping score roles.
    method_rows = [
        ["평가 구간", "목적 및 사용 규칙"],
        ["학습 내부 CV", f"{analysis['cv_splits']}개 폴드 · 후보 선정 / Dummy 비교"],
        ["독립 holdout", f"{analysis['holdout_rows']:,}행 · 선정 모델 평가에만 사용"],
        ["최종 모델 선택", "holdout 점수 반영 없음 / CV 평균값 기준"],
    ]
    method_table = Table(method_rows, colWidths=[122, 355], hAlign="LEFT")
    method_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcecf5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f3f8fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dae5eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story = [
        para("STANDARD — 모델 학습 및 검증", "title"),
        para("검증 설계", "head"),
        para(f"목표 변수: {analysis['target_column']} / 문제 유형: {analysis['task_type']}"),
        para(f"분할 방식: {analysis['split_policy']} / 학습: {analysis['train_rows']}행 / "
             f"독립 검증: {analysis['holdout_rows']}행"),
        para(f"학습 파티션 내 교차검증 {analysis['cv_splits']}회. "
             "전처리 및 모델 적합은 교차검증 각 학습 폴드 안에서만 수행했습니다."),
        para(f"비교 모델은 최대 {analysis.get('challenger_budget', 3)}종이며 Dummy는 별도의 무기술 기준선입니다. "
             "모델 선발은 CV 평균 지표만으로 완료한 후 독립 검증 데이터에 단 한 번 평가합니다."),
        para("분류: 가중 F1 / 회귀: R²를 주요 선발 지표로 사용했습니다.", "small"),
        Spacer(1, 16),
        para("방법상 한계", "head"),
        para("무작위 분할은 반복 개인·미래 기록의 독립성을 보장하지 않습니다. "
             "그룹/시점에 따른 편향이나 목표 정보 누수는 추가 검토해야 합니다."),
        Spacer(1, 15),
        para("검증 데이터 구성", "head"),
        para(f"전체 모델 비교 대상으로 사용된 행: {analysis['train_rows']:,}개 / "
             f"최종 독립 평가 전까지 제외한 행: {analysis['holdout_rows']:,}개"),
        para(f"데이터 분할 정책: {analysis['split_policy']} / "
             f"CV 분할 횟수: {analysis['cv_splits']} / "
             f"기준 지표: {analysis['primary_metric']}"),
        Spacer(1, 8), method_table, Spacer(1, 9),
        para("모형 학습·전처리는 각 학습 부분집합에서만 적합합니다. "
             "동일한 모델 계열이라도 추출 시점·반복 관측에 따라 오차가 달라질 수 있습니다.", "small"),
    ]
    successes = sum(row["status"] == "success" for row in analysis["models"])
    compared = len(analysis["models"])
    # Measured train-CV scores; not independent holdout claims.
    cv_audit = [
        ["CV 검증 스냅샷", "학습 구간 관측치"],
        ["실행 결과", f"{successes}/{compared} 모델 CV 성공 (Dummy 포함)"],
        ["선정 모델 CV", f"{analysis['selected_model']} · {analysis['selected_cv_score']:.4f} ({p})"],
        ["Dummy 기준선 CV", f"{analysis['dummy_model']} · {analysis['dummy_cv_score']:.4f} ({p})"],
    ]
    cv_audit_table = Table(cv_audit, colWidths=[130, 347], hAlign="LEFT")
    cv_audit_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), font),
        ("FONTSIZE", (0,0), (-1,-1), 8.4),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DCECF5")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F4F8FA")]),
        ("LINEBELOW", (0,0), (-1,-2), .3, colors.HexColor("#D6E4EB")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.extend([
        Spacer(1, 9), para("실제 학습 구간 CV 진단", "head"), cv_audit_table,
        para("CV 점수는 모델을 고른 학습 구간의 평가입니다. "
             "독립 holdout 결과와 동일하지 않으며 과적합 가능성을 검토해야 합니다.", "small"),
        PageBreak(),
        para("모델 비교 결과", "title"),
        para(f"주요 지표: {p} — 값이 클수록 좋음", "small"),
        table,
        Spacer(1, 20),
    ])
    image = Image(BytesIO(chart_png))
    image.drawWidth, image.drawHeight = 464, 261
    story.extend([
        image,
        para("막대는 학습 파티션 CV 평균입니다. Dummy 기준선과 비교 모델은 "
             "동일한 학습/검증 폴드로 평가했습니다.", "small"),
        PageBreak(),
        para("독립 검증 및 해석", "title"),
        para(f"CV로 선택한 모델: {analysis['selected_model']}"),
        para(f"독립 검증 {p}: 선택 모델 {metrics[p]:.4f} / Dummy {dummy[p]:.4f}"),
        para(f"선택 모델 − Dummy 차이: {metrics[p] - dummy[p]:+.4f} ({p}, 동일 분리 데이터)"),
        para("차이가 양수여도 통계적 유의성이나 미래 일반화가 자동으로 입증되지는 않습니다.", "small"),
        para(f"CV 기준 Dummy 초과: {'예' if analysis['cv_beats_dummy'] else '아니오'} / "
             f"독립 검증 Dummy 초과: {'예' if analysis['holdout_beats_dummy'] else '아니오'}"),
        para("독립 검증 지표 상세", "head"),
    ])
    for metric in metrics:
        story.append(para(f"{metric}: 선택 모델 {metrics[metric]:.4f}, Dummy {dummy[metric]:.4f}"))
    importance = analysis.get("training_feature_importance", [])
    if importance:
        story.extend([Spacer(1, 12), para("모델별 변수 기여도 참고", "head")])
        method_names = {
            "tree_impurity": "트리 불순도 기반",
            "absolute_coefficient": "전처리 후 계수 절댓값 합",
        }
        method = method_names.get(importance[0]["method"], "모델 내부 순위")
        story.append(para(
            f"{method} 순위입니다. 학습된 선정 모델 내부의 중요도이며, "
            "범주 값은 원본 컬럼 단위로 합산해 익명화했습니다. "
            "값의 단위·크기는 다른 모델과 비교하거나 인과관계로 해석할 수 없습니다.",
            "small",
        ))
        rows = [["원본 변수명", "모델 내부 기여도"]]
        for item in importance[:6]:
            rows.append([para(str(item["feature"]), "small"),
                         f"{item['importance']:.5g}"])
        tbl = Table(rows, colWidths=[322, 155], repeatRows=1, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), font),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dcecf5")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.white, colors.HexColor("#f3f8fa")]),
            ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#d6e5ed")),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(tbl)
    story.extend([Spacer(1, 8), para("유의사항", "head")])
    for w in analysis["warnings"][:6]:
        story.append(para("• " + w, "small"))
    story.append(para("본 결과는 기술적 탐색·비교를 위한 것으로 계약상 예측 정확도 또는 미래 성과를 보장하지 않습니다.", "small"))

    extra = BytesIO()
    doc = SimpleDocTemplate(extra, pagesize=A4, leftMargin=46, rightMargin=46,
                            topMargin=50, bottomMargin=55,
                            title="STANDARD ML evaluation",
                            author="AI AutoML Analyst")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(original)))
    writer.append(PdfReader(BytesIO(extra.getvalue())))
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def build_standard_zip(
    df: pd.DataFrame,
    target_column: str,
    task_type: str | None = None,
    split_policy: str = "random",
    group_column: str | None = None,
    time_column: str | None = None,
    cv: int = 3,
) -> bytes:
    analysis = run_standard(
        df, target_column, task_type, split_policy,
        group_column, time_column, cv,
    )
    source_zip = build_basic_zip(df, report_tier="STANDARD")
    with ZipFile(BytesIO(source_zip)) as z:
        parts = {name: z.read(name) for name in z.namelist()
                 if name not in {"manifest.json", "report.pdf", "README.txt"}}
        base_pdf = z.read("report.pdf")
    chart = _comparison_plot(analysis)
    parts["charts/06_ml_comparison.png"] = chart
    parts["report.pdf"] = _append_ml_pdf(base_pdf, analysis, chart)
    public = {k: v for k, v in analysis.items()
              if k not in {"train_original_indices", "holdout_original_indices",
                           "train_group_values", "holdout_group_values"}}
    parts["standard_summary.json"] = json.dumps(
        public, ensure_ascii=False, indent=2, allow_nan=False
    ).encode("utf-8")
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["model", "role", "status", "cv_primary", "cv_std", "error"])
    for row in analysis["models"]:
        writer.writerow([
            _csv_safe(row["model"]), row["role"], row["status"],
            row["cv_primary"] if row["cv_primary"] is not None else "",
            row["cv_std"] if row["cv_std"] is not None else "", row["error"] or "",
        ])
    parts["model_scores.csv"] = ("\ufeff" + buffer.getvalue()).encode("utf-8")
    parts["README.txt"] = (
        "AI AutoML Analyst STANDARD\n"
        "report.pdf: BASIC 품질 진단 + STANDARD 모델 평가 결과.\n"
        "model_scores.csv: 학습 데이터 내부 CV 평균/편차.\n"
        "standard_summary.json: 선정 모델과 holdout 평가, 누수 경고.\n"
        "Dummy 기준선은 3종 비교 모델에 포함되지 않습니다.\n"
        "독립 검증 결과로 모델을 다시 고르지 않았습니다.\n"
        "고객의 원본 CSV 또는 개별 관측 레코드는 포함하지 않습니다.\n"
        + font_usage_notice("".join(str(col) for col in df.columns), pdf_bytes=parts["report.pdf"])
    ).encode("utf-8")
    manifest = {
        "format": "standard-v1", "tier": "STANDARD",
        "no_raw_dataset": True,
        "files": [
            {"path": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            for name, payload in sorted(parts.items())
        ],
    }
    parts["manifest.json"] = json.dumps(
        manifest, ensure_ascii=False, indent=2
    ).encode("utf-8")
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as z:
        for name, payload in parts.items():
            z.writestr(name, payload)
    return output.getvalue()
