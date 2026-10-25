"""Create a Windows-friendly, customer-data-free three-tier release review pack.

No Poppler or browser is needed. All output is synthetic and stored under a
fresh, gitignored qa-preview/ directory; existing review files aren't replaced.
Generated model bundles may contain category metadata, so *never* publish
qa-preview contents. The JSON summary only includes counts and SHA-256 hashes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import platform
import sys
from zipfile import ZipFile

import pandas as pd
from pypdf import PdfReader

from backend.app.services.basic_report import build_basic_zip
from backend.app.services.standard_delivery import build_standard_zip
from backend.app.services.premium_delivery import build_premium_zip
from backend.app.services.premium_predict import predict_csv
from scripts.p6e6_delivery_policy import verify_shipping_zip


def synthetic_frame() -> pd.DataFrame:
    n = 150
    frame = pd.DataFrame({
        "날짜": pd.date_range("2026-01-01", periods=n, freq="D").strftime("%Y-%m-%d"),
        "지역": ["SYN_A", "SYN_B", "SYN_C"] * 50,
        "방문수": [20 + (i % 23) * 3 for i in range(n)],
        "매출": [150 + (i % 23) * 8 + (i % 4) for i in range(n)],
        "원가": [90 + (i % 23) * 4 + (i % 7) for i in range(n)],
    })
    frame.loc[10:25, "지역"] = None
    frame.loc[4:13, "매출"] = float("nan")
    return frame


def _fresh_run_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    base = "p6e5-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for suffix in range(1000):
        candidate = root / (base if suffix == 0 else f"{base}-{suffix}")
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError("Cannot allocate a fresh QA run directory.")


def _inspect(payload: bytes, tier: str, run_dir: Path, min_pages: int, max_pages: int) -> dict:
    shipping = verify_shipping_zip(payload, tier)
    folder = run_dir / tier.lower()
    folder.mkdir()
    (folder / f"{tier.lower()}_synthetic.zip").write_bytes(payload)
    with ZipFile(BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f"{tier}: corrupt ZIP")
        manifest = json.loads(archive.read("manifest.json"))
        members = archive.namelist()
        if len(members) != len(set(members)):
            raise RuntimeError(f"{tier}: duplicate ZIP members")
        for entry in manifest["files"]:
            name = entry["path"]
            if name not in members:
                raise RuntimeError(f"{tier}: missing manifest file")
            content = archive.read(name)
            expected = entry["sha256"]
            if sha256(content).hexdigest() != expected:
                raise RuntimeError(f"{tier}: manifest hash mismatch")
            claimed_size = entry.get("size", entry.get("bytes"))
            if claimed_size is not None and len(content) != claimed_size:
                raise RuntimeError(f"{tier}: manifest size mismatch")
        pdf = archive.read("report.pdf")
        page_count = len(PdfReader(BytesIO(pdf)).pages)
        if not min_pages <= page_count <= max_pages:
            raise RuntimeError(f"{tier}: unexpected PDF page count {page_count}")
        (folder / "report.pdf").write_bytes(pdf)
        result = {
            "tier": tier, "pdf_pages": page_count,
            "zip_sha256": sha256(payload).hexdigest(),
            "pdf_sha256": sha256(pdf).hexdigest(),
            "zip_member_count": len(members), "manifest_hashes": "PASS",
            "shipping_policy": shipping,
        }
        if tier == "PREMIUM":
            wanted = ("model_pipeline.skops", "model_schema.json", "predict.py",
                      "predict.cmd", "requirements-premium.txt", "sample_input.csv")
            extracted = folder / "trusted_demo"
            extracted.mkdir()
            for name in wanted:
                if name not in members:
                    raise RuntimeError(f"PREMIUM: missing {name}")
                # Only fixed, explicitly expected flat filenames; never extract
                # arbitrary archive paths from external sources.
                (extracted / name).write_bytes(archive.read(name))
            result["trusted_demo_subdirectory"] = "premium/trusted_demo"
        return result


def create_review_pack(root: Path = Path("qa-preview"), summary: Path | None = None) -> dict:
    directory = _fresh_run_dir(root)
    basic = synthetic_frame()
    ml = basic.copy()
    ml["구매"] = [i % 2 for i in range(len(ml))]
    basic.to_csv(directory / "basic_input.csv", index=False, encoding="utf-8-sig")
    ml.to_csv(directory / "ml_input.csv", index=False, encoding="utf-8-sig")
    outputs = [
        _inspect(build_basic_zip(basic), "BASIC", directory, 6, 8),
        _inspect(build_standard_zip(ml, target_column="구매",
                                    task_type="classification", cv=3),
                 "STANDARD", directory, 8, 12),
        _inspect(build_premium_zip(ml, target_column="구매",
                                   task_type="classification", cv=3),
                 "PREMIUM", directory, 10, 15),
    ]
    trusted = directory / "premium" / "trusted_demo"
    schema = json.loads((trusted / "model_schema.json").read_text(encoding="utf-8"))
    required = schema["raw_feature_columns"]
    predictions_input = trusted / "new_data.csv"
    ml.loc[:2, required].to_csv(predictions_input, index=False, encoding="utf-8-sig")
    n_pred = predict_csv(trusted, predictions_input, trusted / "python_predictions.csv")
    if n_pred != 3:
        raise RuntimeError("PREMIUM local prediction count mismatch")
    outputs[-1]["python_prediction_rows"] = n_pred
    if sys.platform == "win32":
        # On a real Windows machine, exercise the exact delivered batch file,
        # not just predict_csv() from Python. The parent QA launcher adds its
        # isolated venv to PATH; Python version/schema checks still apply.
        import subprocess

        cmd_output = trusted / "cmd_predictions.csv"
        completed = subprocess.run(
            ["cmd.exe", "/d", "/c", str(trusted / "predict.cmd"),
             str(predictions_input), str(cmd_output)],
            cwd=trusted, capture_output=True, text=True, timeout=90,
        )
        if completed.returncode != 0:
            # Deliberately avoid reflecting any row or path from stderr.
            raise RuntimeError("Windows predict.cmd synthetic replay failed.")
        observed = pd.read_csv(cmd_output)
        if len(observed) != n_pred or list(observed.columns) != ["prediction"]:
            raise RuntimeError("Windows predict.cmd produced incorrect synthetic output.")
        outputs[-1]["windows_cmd_replay"] = "PASS"
    else:
        outputs[-1]["windows_cmd_replay"] = "NOT_RUN_NON_WINDOWS"

    evidence = {
        "format": "p6e5-owner-review-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "python": ".".join(map(str, sys.version_info[:3])),
        "os_family": platform.system(),
        "input_rows": len(basic),
        "data_classification": "SYNTHETIC_ONLY",
        "results": outputs,
        "browser_manual_approval": "NOT_RUN",
        "physical_windows_user_approval": "NOT_RUN",
        "design_owner_approval": "NOT_GIVEN",
        "license_legal_approval": "NOT_CERTIFIED",
        "sale_gate": "NO_GO",
        "contains_customer_rows": False,
        "never_upload_model_or_demo_zip_to_public_repo": True,
    }
    serialized = json.dumps(evidence, ensure_ascii=False, indent=2)
    (directory / "P6E5_REVIEW_EVIDENCE.json").write_text(serialized, encoding="utf-8")
    if summary is not None:
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(serialized, encoding="utf-8")
    print("Synthetic QA review pack:", directory)
    print("Browser input files: basic_input.csv, ml_input.csv")
    print("Open tier report PDFs from basic/, standard/, premium/")
    print("PREMIUM trusted_demo contains predict.cmd, new_data.csv and model files.")
    print("To verify cmd.exe on Windows in trusted_demo: predict.cmd new_data.csv cmd_predictions.csv")
    print("IMPORTANT: no generated model/ZIP may be committed or sent to a public repository.")
    for result in outputs:
        print(result["tier"], "PDF pages", result["pdf_pages"], "manifest", result["manifest_hashes"])
    print("Release owner approval remains NOT RUN.")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("qa-preview"))
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    create_review_pack(root=args.output_root, summary=args.summary)


if __name__ == "__main__":
    main()
