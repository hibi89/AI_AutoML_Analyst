"""Generate a visibly labeled, synthetic-only BASIC preview for CI review.

Never commit the generated ZIP/PDF/PNGs. GitHub Actions stores the preview
temporarily as an artifact for inspection, not as customer data.
"""
from __future__ import annotations

import subprocess
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from backend.app.services.basic_report import build_basic_zip
from backend.app.services.standard_delivery import build_standard_zip


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
        (standard_dir / "report.pdf").write_bytes(standard_pdf)
        print("Generated STANDARD synthetic ZIP bytes:", len(standard_zip))
        print("Generated STANDARD PDF bytes:", len(standard_pdf))
    subprocess.run(
        ["pdftoppm", "-scale-to", "1100", "-png",
         str(standard_dir / "report.pdf"), str(standard_dir / "page")],
        check=True, timeout=120,
    )
    print("Rendered STANDARD page previews:", len(list(standard_dir.glob("page-*.png"))))


if __name__ == "__main__":
    main()
