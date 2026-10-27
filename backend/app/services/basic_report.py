"""Local, synthetic-safe BASIC MVP diagnostics and ZIP packaging.

P1 schema/validation helpers reused by the P3 local PDF and chart delivery.
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
    # Extremely long/control-character headers can corrupt charts or PDF layout.
    if any(len(name) > 160 or any(ord(ch) < 32 for ch in name) for name in df.columns):
        raise ValueError("Column headers must be at most 160 characters and contain no control characters.")


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


def build_basic_zip(df: pd.DataFrame, *, report_tier: str = "BASIC") -> bytes:
    """Compatibility entry point; now exports the P3 PDF/chart/manifest delivery."""
    from backend.app.services.basic_p3 import build_basic_delivery
    return build_basic_delivery(df, report_tier=report_tier)
