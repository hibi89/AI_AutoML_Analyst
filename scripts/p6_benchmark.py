"""Synthetic bounded-input P6 performance smoke; never saves customer data."""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import resource
import time
from io import BytesIO
from zipfile import ZipFile

import numpy as np
import pandas as pd

from backend.app.services.basic_report import build_basic_zip, MAX_ROWS, MAX_COLUMNS


def run() -> dict:
    assert MAX_ROWS == 20000 and MAX_COLUMNS == 50
    rng = np.random.default_rng(24680)
    records = {}
    for i in range(35):
        records[f"measurement_{i:02d}"] = rng.normal(
            loc=(i + 1) * 4, scale=(i % 5) + 1.0, size=MAX_ROWS
        )
    for i in range(15):
        records[f"segment_{i:02d}"] = rng.choice(["A", "B", "C"], size=MAX_ROWS)
    data = pd.DataFrame(records)
    data.loc[10:109, "measurement_00"] = np.nan
    start = time.perf_counter()
    zip_content = build_basic_zip(data)
    elapsed = time.perf_counter() - start
    with ZipFile(BytesIO(zip_content)) as archive:
        summary = json.loads(archive.read("summary.json"))
        chart_files = [n for n in archive.namelist() if n.startswith("charts/")]
        assert archive.testzip() is None
    assert summary["rows"] == MAX_ROWS
    assert summary["columns"] == MAX_COLUMNS
    assert 2 <= len(chart_files) <= 5
    # ru_maxrss is reported in KiB on Linux and bytes on macOS.
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "test": "synthetic BASIC maximum row/column caps",
        "rows": MAX_ROWS, "columns": MAX_COLUMNS,
        "seconds": round(elapsed, 2),
        "zip_bytes": len(zip_content),
        "charts": len(chart_files),
        "maxrss_kib_linux": rss if platform.system() == "Linux" else None,
        "python": platform.python_version(),
        "dataset_is_synthetic": True,
        "scope": "BASIC descriptive report only; not PREMIUM training or browser",
    }


if __name__ == "__main__":
    output = run()
    folder = Path("ci-benchmarks")
    folder.mkdir(exist_ok=True)
    (folder / "p6_basic_20000x50.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    print("P6 benchmark:", json.dumps(output, ensure_ascii=False))
