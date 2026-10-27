"""Generate a visibly labeled, synthetic-only BASIC preview for CI review.

Never commit the generated ZIP/PDF/PNGs. GitHub Actions stores the preview
temporarily as an artifact for inspection, not as customer data.
"""
from __future__ import annotations

import json
import subprocess
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
from pypdf import PdfReader

from backend.app.services.basic_report import build_basic_zip
from backend.app.services.standard_delivery import build_standard_zip
from backend.app.services.premium_delivery import build_premium_zip



def _check_ml_review_pdf(tier: str, report: bytes, metadata: dict) -> None:
    """Regression gate for sparse appendix spill and dropped no-skill caveat."""
    page_texts = [page.extract_text() or "" for page in PdfReader(BytesIO(report)).pages]
    ml_pages = [
        text for text in page_texts
        if f"AI AutoML Analyst  |  {tier} 모델 검증" in text
    ]
    if len(ml_pages) != 3:
        raise AssertionError(f"{tier}: expected exactly three ML PDF pages, got {len(ml_pages)}")
    if not metadata["holdout_beats_dummy"] and not any(
        "예측 성능 우위가 입증되지 않았습니다." in text for text in ml_pages
    ):
        raise AssertionError(f"{tier}: missing independent-holdout no-skill warning")


def main() -> None:
    n = 150
    frame = pd.DataFrame({
        "날짜": pd.date_range("2026-01-01", periods=n, freq="D").strftime("%Y-%m-%d"),
        "지역": ["A", "B", "C"] * 50,
        "방문수": [20 + (i % 23) * 3 for i in range(n)],
        "매출": [150 + (i % 23) * 8 + (i % 4) for i in range(n)],
        "원가": [90 + (i % 23) * 4 + (i % 7) for i in range(n)],
    })
    frame.loc[10:25, "지역"] = None
    frame.loc[4:13, "매출"] = float("nan")
    folder = Path("ci-preview")
    folder.mkdir(exist_ok=True)
    payload = build_basic_zip(frame)
    (folder / "basic_synthetic_demo.zip").write_bytes(payload)

    with ZipFile(BytesIO(payload)) as z:
        pdf = z.read("report.pdf")
        charts = [n for n in z.namelist() if n.startswith("charts/")]
        print(f"Generated synthetic demo: ZIP={len(payload)} bytes PDF={len(pdf)} bytes charts={len(charts)}")
        (folder / "report.pdf").write_bytes(pdf)

    subprocess.run(
        ["pdftoppm", "-f", "1", "-l", "8", "-scale-to", "1100",
         "-png", str(folder / "report.pdf"), str(folder / "page")],
        check=True, timeout=120,
    )
    print("Rendered page previews:", len(list(folder.glob("page-*.png"))))

    # Reuse the same synthetic dataset with a synthetic binary outcome for STANDARD.
    standard_data = frame.copy()
    standard_data["구매"] = [i % 2 for i in range(n)]
    standard_dir = folder / "standard"
    standard_dir.mkdir(exist_ok=True)
    standard_zip = build_standard_zip(
        standard_data, target_column="구매",
        task_type="classification", split_policy="random", cv=3,
    )
    (standard_dir / "standard_synthetic_demo.zip").write_bytes(standard_zip)
    with ZipFile(BytesIO(standard_zip)) as output:
        standard_pdf = output.read("report.pdf")
        _check_ml_review_pdf("STANDARD", standard_pdf, json.loads(output.read("standard_summary.json")))
        (standard_dir / "report.pdf").write_bytes(standard_pdf)
        print("Generated STANDARD synthetic ZIP bytes:", len(standard_zip))
        print("Generated STANDARD PDF bytes:", len(standard_pdf))
    subprocess.run(
        ["pdftoppm", "-scale-to", "1100", "-png",
         str(standard_dir / "report.pdf"), str(standard_dir / "page")],
        check=True, timeout=120,
    )
    print("Rendered STANDARD page previews:", len(list(standard_dir.glob("page-*.png"))))

    premium_dir = folder / "premium"
    premium_dir.mkdir(exist_ok=True)
    premium_zip = build_premium_zip(
        standard_data, target_column="구매",
        task_type="classification", split_policy="random", cv=3,
    )
    (premium_dir / "premium_synthetic_demo.zip").write_bytes(premium_zip)
    with ZipFile(BytesIO(premium_zip)) as delivered:
        premium_pdf = delivered.read("report.pdf")
        _check_ml_review_pdf("PREMIUM", premium_pdf, json.loads(delivered.read("premium_summary.json")))
        (premium_dir / "report.pdf").write_bytes(premium_pdf)
        print("Generated PREMIUM synthetic ZIP bytes:", len(premium_zip))
        print("Generated PREMIUM PDF bytes:", len(premium_pdf))
    subprocess.run(
        ["pdftoppm", "-scale-to", "1100", "-png",
         str(premium_dir / "report.pdf"), str(premium_dir / "page")],
        check=True, timeout=120,
    )
    print("Rendered PREMIUM page previews:", len(list(premium_dir.glob("page-*.png"))))


if __name__ == "__main__":
    main()
