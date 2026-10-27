"""Trusted locally generated PREMIUM model inference.

Requires the owner-provided bundle extracted locally. This program does NOT
download files or deserialize pickle/joblib. Never run it against a third-party
archive, even if a digest matches: SHA-256 detects corruption, not authorship.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import hashlib
import json
import sys

import pandas as pd
import numpy as np
import sklearn
import skops
import skops.io as sio


MAX_CSV_BYTES = 30 * 1024 * 1024
MAX_ROWS = 20000


def _version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(p) for p in text.split(".") if p.isdigit())


def _model_and_schema(folder: Path):
    model_file = folder / "model_pipeline.skops"
    schema_file = folder / "model_schema.json"
    if not model_file.is_file() or not schema_file.is_file():
        raise ValueError("Model and schema files must be in the extracted PREMIUM folder.")
    if model_file.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("Model file too large.")
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    model = model_file.read_bytes()
    if schema.get("format") != "automl-premium-v1":
        raise ValueError("Unsupported model schema format.")
    if hashlib.sha256(model).hexdigest() != schema.get("model_sha256"):
        raise ValueError("Model checksum mismatch. Stop: obtain an original trusted bundle.")
    versions = schema["versions"]
    if (versions.get("sklearn") != sklearn.__version__
            or versions.get("skops") != skops.__version__
            or versions.get("pandas") != pd.__version__
            or versions.get("numpy") != np.__version__):
        raise ValueError("Dependency versions differ. Install exact requirements-premium.txt first.")
    if schema.get("python_minor") != f"{sys.version_info.major}.{sys.version_info.minor}":
        raise ValueError("Python minor version differs from the model producer.")
    # Reject all unapproved object types. Do not auto-trust the archive's own list.
    unknown = sio.get_untrusted_types(data=model)
    allowed_types = {"numpy.dtype"}  # Audited built-in type only; no archive-defined trust lists.
    forbidden = set(unknown) - allowed_types
    if forbidden:
        raise ValueError(
            "Model references unapproved types and will not be loaded: "
            + ", ".join(sorted(forbidden)[:5])
        )
    return sio.loads(model, trusted=sorted(allowed_types & set(unknown))), schema


def _load_input(path: Path, schema: dict) -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size > MAX_CSV_BYTES:
        raise ValueError("Input CSV missing or exceeds 30 MiB.")
    raw = None
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            # pandas silently renames duplicate source CSV headers: a,a -> a,a.1.
            # That can accidentally match a genuinely dotted training schema.
            # Enforce the ORIGINAL header, not pandas' normalized column names.
            with path.open("r", encoding=encoding, newline="") as source:
                header = next(csv.reader(source, strict=True), None)
        except UnicodeError:
            continue
        except csv.Error as exc:
            raise ValueError("Invalid CSV header structure.") from exc
        if header is not None:
            if len(header) != len(set(header)):
                raise ValueError("Duplicate input column names are not supported.")
            if not all(name.strip() for name in header):
                raise ValueError("Input CSV headers must be nonempty.")
        try:
            raw = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeError:
            continue
    if raw is None:
        raise ValueError("Use UTF-8 or CP949 CSV encoding.")
    if not 1 <= len(raw) <= MAX_ROWS:
        raise ValueError("Input requires 1–20,000 rows.")
    expected = schema["raw_feature_columns"]
    if list(raw.columns) != expected:
        raise ValueError(
            "Input header mismatch. Use the exact ordered columns in sample_input.csv."
        )
    if raw.columns.duplicated().any():
        raise ValueError("Duplicate input column names are not supported.")
    for name in schema["numeric_raw_columns"]:
        if not pd.api.types.is_numeric_dtype(raw[name]):
            raise ValueError(f"Numeric column has invalid dtype: {name}")
    for name in schema["boolean_raw_columns"]:
        if not pd.api.types.is_bool_dtype(raw[name]):
            raise ValueError(f"Boolean column has invalid dtype: {name}")
    return raw


def _prepare(raw: pd.DataFrame, schema: dict) -> pd.DataFrame:
    data = raw.copy()
    for name in schema["datetime_features"]:
        parsed = pd.to_datetime(data[name], errors="coerce")
        if (data[name].notna() & parsed.isna()).any():
            raise ValueError(f"Invalid datetime values in column: {name}")
        data[f"{name}__year"] = parsed.dt.year
        data[f"{name}__month"] = parsed.dt.month
        data[f"{name}__day"] = parsed.dt.day
        data[f"{name}__dayofweek"] = parsed.dt.dayofweek
        data[f"{name}__hour"] = parsed.dt.hour
        data = data.drop(columns=[name])
    for name in schema["boolean_raw_columns"]:
        data[name] = data[name].astype(float)
    return data.reindex(columns=schema["prepared_feature_columns"])


def predict_csv(folder: Path, input_csv: Path, output_csv: Path) -> int:
    model, schema = _model_and_schema(folder)
    raw = _load_input(input_csv, schema)
    X = _prepare(raw, schema)
    prediction = model.predict(X)
    values = [str(v) if isinstance(v, str) else v for v in prediction]
    output_csv = Path(output_csv)
    if output_csv.resolve() == input_csv.resolve():
        raise ValueError("Refusing to overwrite input CSV.")
    if output_csv.exists():
        raise ValueError("Output path exists. Choose a new name to avoid overwriting.")
    with output_csv.open("x", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["prediction"])
        for value in values:
            text = str(value)
            if text.lstrip().startswith(("=", "+", "-", "@")) and not _is_safe_number(text):
                text = "'" + text
            writer.writerow([text])
    return len(values)


def _is_safe_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def main() -> int:
    # Windows consoles/pipes may use a legacy code page that cannot represent
    # Korean customer paths. A successful CSV write must not fail while
    # reporting the output path. Keep the actual CSV encoding unchanged.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="backslashreplace")
    cli = argparse.ArgumentParser(description="PREMIUM trusted local CSV repeat prediction")
    cli.add_argument("--input", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--model-dir", default=Path(__file__).resolve().parent, type=Path)
    args = cli.parse_args()
    try:
        count = predict_csv(args.model_dir, args.input, args.output)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Predicted {count} rows. Saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
