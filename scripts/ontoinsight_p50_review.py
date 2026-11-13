"""Local one-CSV ONTOINSIGHT semantic review. Never exports raw rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.services.ontoinsight_p50 import inspect_csv
from backend.app.services.basic_report import MAX_UPLOAD_BYTES


def main() -> int:
    parser = argparse.ArgumentParser(description="Local P50 CSV schema review (no KPI/ML until approved)")
    parser.add_argument("csv", type=Path, help="Authorized CSV file path (read-only)")
    parser.add_argument("--encoding", default="auto", choices=["auto", "utf-8", "utf-8-sig", "cp949", "euc-kr", "cp932", "latin1"])
    parser.add_argument("--output", required=True, type=Path, help="Fresh JSON report path (never overwritten)")
    args = parser.parse_args()
    path = args.csv
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".csv":
        parser.error("A regular, non-symlink CSV file is required.")
    if not 0 < path.stat().st_size <= MAX_UPLOAD_BYTES:
        parser.error("CSV size is outside supported bounds.")
    target = args.output
    if target.exists() or target.is_symlink() or not target.parent.is_dir():
        parser.error("Output must be a new path in an existing local directory.")
    report = inspect_csv(path.read_bytes(), path.name, encoding=args.encoding)
    # Atomic creation; never overwrite an owner's preexisting output.
    with target.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("REVIEW_HOLD: metadata-only report written; no business KPI or ML was approved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
