"""P6 client-facing graph design. Aggregate-only, Korean typography, no raw labels."""
from __future__ import annotations

from io import BytesIO
import math
import os
from pathlib import Path

import pandas as pd


NAVY = "#18364C"
TEAL = "#087F8C"
MINT = "#D8F0EC"
GOLD = "#D69B46"
PALE = "#F3F7FA"
GREY = "#647B8A"


def font_family() -> str:
    from matplotlib import font_manager
    locations = [
        os.environ.get("AUTOML_KOREAN_FONT_PATH", ""),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/local/share/fonts/NanumGothic.ttf",
        "C:/Windows/Fonts/NanumGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
    ]
    for path in locations:
        if path and Path(path).is_file():
            font_manager.fontManager.addfont(path)
            return font_manager.FontProperties(fname=path).get_name()
    raise RuntimeError("Korean graph font unavailable; install NanumGothic or set AUTOML_KOREAN_FONT_PATH.")


def create_charts(df: pd.DataFrame, quality: list[dict]) -> list[tuple[str, bytes, str]]:
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    from matplotlib import pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    font = font_family()
    numeric = [
        str(col) for col in df.select_dtypes(include="number").columns
        if df[col].nunique(dropna=True) > 1
    ]
    charts: list[tuple[str, bytes, str]] = []

    def shortened(value, length=18):
        s = str(value).replace("\n", " ")
        return s if len(s) <= length else s[:length-1] + "…"

    def render(slug: str, title: str, subtitle: str, caption: str, painter):
        if len(charts) >= 5:
            return
        with plt.rc_context({"font.family": font, "axes.unicode_minus": False}):
            fig, ax = plt.subplots(figsize=(8.6, 4.8), facecolor="white")
            try:
                ax.set_facecolor("white")
                for spine in ax.spines.values():
                    spine.set_visible(False)
                ax.set_axisbelow(True)
                ax.tick_params(axis="both", colors=GREY, labelsize=9, length=0, pad=8)
                ax.grid(axis="y", color="#E6EDF1", linewidth=.8)
                ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
                fig.text(.07, .955, "AI  /  DATA INTELLIGENCE", fontsize=8, color=TEAL, fontweight="bold")
                fig.text(.07, .886, title, fontsize=16, color=NAVY, fontweight="bold")
                fig.text(.07, .830, subtitle, fontsize=9, color=GREY)
                painter(fig, ax)
                fig.subplots_adjust(left=.13, right=.94, top=.74, bottom=.17)
                fig.text(.07, .045, "기술통계  ·  관측값 요약  |  인과관계·미래 성과를 보장하지 않음",
                         fontsize=8, color=GREY)
                buffer = BytesIO()
                fig.savefig(buffer, format="png", dpi=155, facecolor="white")
                charts.append((f"charts/{len(charts)+1:02d}_{slug}.png", buffer.getvalue(), caption))
            finally:
                plt.close(fig)

    if numeric:
        col = numeric[0]
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(values) >= 8:
            bins = min(22, max(6, round(math.sqrt(len(values)))))
            def distribution(fig, ax):
                ax.hist(values, bins=bins, color=TEAL, edgecolor="white", linewidth=1.2)
                median = float(values.median())
                ax.axvline(median, color=GOLD, lw=2, ls="--", label=f"중앙값 {median:,.1f}")
                ax.legend(loc="upper right", frameon=False, fontsize=9)
                ax.set_ylabel("관측 건수 (건)", color=NAVY, fontsize=9)
                ax.set_xlabel(f"{shortened(col, 26)} (원본 단위)", color=NAVY, fontsize=9)
            render("distribution", f"{shortened(col, 22)} · 수치형 분포",
                   f"유효 관측 {len(values):,}건  /  중앙값 {values.median():,.2f}",
                   f"'{shortened(col)}' 열의 히스토그램입니다. 원본 단위를 확인하세요.", distribution)

    missing = sorted((q for q in quality if q["missing"]), key=lambda q:-q["missing_pct"])[:10]
    if missing:
        def missingness(fig, ax):
            labels = [shortened(q["column"], 17) for q in missing][::-1]
            pct = [q["missing_pct"] for q in missing][::-1]
            ax.grid(axis="x", color="#E6EDF1")
            ax.grid(axis="y", visible=False)
            bars = ax.barh(labels, pct, color=[GOLD if v >= 20 else TEAL for v in pct], height=.57)
            ax.set_xlim(0, max(10, max(pct)*1.28))
            ax.set_xlabel("결측률 (%)", color=NAVY, fontsize=9)
            for bar,v in zip(bars,pct):
                ax.text(v + max(pct)*.02, bar.get_y()+bar.get_height()/2,
                        f"{v:.1f}%", va="center", color=NAVY, fontsize=9)
            fig.subplots_adjust(left=.24, right=.92, top=.74, bottom=.17)
        render("missing", "데이터 품질 · 결측 비율",
               f"결측이 관측된 열 {len(missing)}개 · 비율이 높은 열부터 비교",
               "열별 관측 결측률입니다. 결측 자체가 오류임을 뜻하지 않습니다.", missingness)

    if len(numeric) >= 2:
        complete = df[numeric[:7]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(complete) >= 8:
            corr = complete.corr()
            if bool(corr.notna().all().all()):
                def correlation(fig, ax):
                    ax.grid(False)
                    im = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
                    labels=[shortened(c, 12) for c in corr.columns]
                    ax.set_xticks(range(len(labels)), labels, fontsize=8, rotation=18, ha="right")
                    ax.set_yticks(range(len(labels)), labels, fontsize=8)
                    if len(labels) <= 5:
                        for i in range(len(labels)):
                            for j in range(len(labels)):
                                v=float(corr.iloc[i,j])
                                ax.text(j,i,f"{v:+.2f}",ha="center",va="center",
                                        color="white" if abs(v)>.65 else NAVY,fontsize=8)
                    fig.colorbar(im, ax=ax, fraction=.046, pad=.025).set_label("상관계수", fontsize=8)
                    fig.subplots_adjust(left=.23, right=.90, top=.74, bottom=.20)
                render("correlation", "수치형 변수 간 상관관계",
                       f"공통 유효 관측 {len(complete):,}건  /  Pearson 상관계수",
                       "완전 관측 행에서 계산한 Pearson 상관계수입니다. 인과관계를 뜻하지 않습니다.", correlation)

    # Category values intentionally withheld to avoid exposing private labels.
    date_columns = [str(c) for c in df.columns if any(h in str(c).lower()
                    for h in ("date","time","날짜","일자"))]
    categories = [
        col for col in df.select_dtypes(include=["object","category","string","bool"]).columns
        if len(df)>=8 and 2<=df[col].nunique(dropna=True)<=15 and str(col) not in date_columns
    ]
    if categories:
        col=categories[0]
        counts=df[col].value_counts().head(6)
        if len(counts)>=2:
            def catplot(fig,ax):
                xs=np.arange(len(counts))
                bars=ax.bar(xs,counts.to_numpy(),width=.56,color=TEAL)
                ax.set_xticks(xs,[f"범주 {i+1}" for i in range(len(xs))],fontsize=9)
                ax.set_ylabel("관측 건수 (건)",color=NAVY,fontsize=9)
                for bar,val in zip(bars,counts):
                    ax.annotate(f"{int(val):,}",(bar.get_x()+bar.get_width()/2,bar.get_height()),
                                xytext=(0,6),textcoords="offset points",ha="center",fontsize=9,color=NAVY)
                ax.set_ylim(0,max(counts)*1.2)
            render("categories",f"{shortened(col,22)} · 범주별 빈도",
                   f"상위 {len(counts)}개 범주  /  개별 범주명은 개인정보 보호를 위해 비표시",
                   f"'{shortened(col)}'의 상위 범주 순위별 건수입니다. 범주명은 원본 데이터 보호를 위해 표시하지 않습니다.",catplot)

    if numeric:
        col=numeric[0]
        vals=pd.to_numeric(df[col],errors="coerce").dropna()
        if len(vals)>=8:
            def boxplot(fig,ax):
                ax.grid(axis="y",color="#E6EDF1")
                ax.boxplot(vals.to_numpy(),patch_artist=True,widths=.35,
                           boxprops={"facecolor":MINT,"edgecolor":TEAL,"linewidth":1.5},
                           medianprops={"color":GOLD,"linewidth":2},
                           whiskerprops={"color":TEAL},
                           capprops={"color":TEAL},
                           flierprops={"marker":"o","markersize":3,"markerfacecolor":GREY,"alpha":.55})
                ax.set_xticks([1],[shortened(col,25)],fontsize=9)
                ax.set_ylabel("관측값 (원본 단위)",fontsize=9,color=NAVY)
            render("box","사분위 범위와 관측값 분산",
                   f"{shortened(col,22)}  /  Q1 {vals.quantile(.25):,.1f} · 중앙값 {vals.median():,.1f} · Q3 {vals.quantile(.75):,.1f}",
                   "상자그림은 분산을 요약합니다. 이상 관측이 반드시 오류는 아닙니다.",boxplot)

    if len(charts)<5 and numeric and date_columns:
        for date_col in date_columns:
            dates=pd.to_datetime(df[date_col],errors="coerce")
            valid=dates.notna() & df[numeric[0]].notna()
            if valid.sum()<12 or dates[valid].dt.normalize().nunique()<3:
                continue
            grouped=pd.Series(pd.to_numeric(df.loc[valid,numeric[0]],errors="coerce").to_numpy(),
                              index=pd.DatetimeIndex(dates[valid])).resample("MS").mean().dropna()
            if len(grouped)<3:
                continue
            def trend(fig,ax):
                xs=range(len(grouped))
                ax.plot(xs,grouped.to_numpy(),color=TEAL,lw=2.6,marker="o",markersize=5)
                ax.fill_between(xs,grouped.to_numpy(),min(grouped)*.9,color=MINT,alpha=.4)
                ax.set_xticks(list(xs),[v.strftime("%Y-%m") for v in grouped.index],rotation=18)
                ax.set_ylabel("월별 평균 (원본 단위)",fontsize=9,color=NAVY)
            render("trend","기간별 수치형 변화",
                   f"{shortened(numeric[0],20)} 월별 관측 평균  /  {len(grouped)}개월",
                   "관측 기간 평균 변화로 미래 변화나 인과관계를 보장하지 않습니다.",trend)
            break
    return charts
