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


def _load_input(path: Path, schema: dict, csv_encoding: str = "auto") -> pd.DataFrame:
    if not path.is_file() or path.stat().st_size > MAX_CSV_BYTES:
        raise ValueError("Input CSV missing or exceeds 30 MiB.")
    supported = {"auto", "utf-8-sig", "utf-8", "cp949", "cp932"}
    if csv_encoding not in supported:
        raise ValueError("Unsupported prediction CSV encoding selection.")
    encodings = (("utf-8-sig", "utf-8", "cp949")
                 if csv_encoding == "auto" else (csv_encoding,))
    # The trusted schema is already known: reject a mismatching original
    # header before pandas allocates columns or attempts to parse row data.
    # This also prevents pandas' duplicate-header suffixing from matching the
    # apparent names of a valid training schema.
    expected = schema["raw_feature_columns"]
    raw = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as source:
                reader = csv.reader(source, strict=True)
                header = next(reader, None)
                if header is not None:
                    # An extra CSV field can become a silent implicit pandas
                    # index; this would feed shifted values to the model.
                    # Preserve short rows as missing trailing cells for imputation.
                    for row_number, row in enumerate(reader, start=1):
                        if len(row) > len(header):
                            raise ValueError(
                                "Prediction CSV data row has more fields than header."
                            )
                        if row_number > MAX_ROWS:
                            break
        except UnicodeError:
            continue
        except csv.Error as exc:
            raise ValueError("Invalid CSV header structure.") from exc
        if header is None or not all(name.strip() for name in header):
            raise ValueError("Input CSV headers must be nonempty.")
        if len(header) != len(set(header)):
            raise ValueError("Duplicate input column names are not supported.")
        if header != expected:
            raise ValueError(
                "Input header mismatch. Use the exact ordered columns in sample_input.csv."
            )
        try:
            # nrows includes one overflow row: distinguish exactly MAX_ROWS
            # from too many rows without materializing the entire input.
            # The training schema identifies numeric and boolean features.
            # Every other raw feature was textual (including date text), so
            # force string parsing: otherwise a new CSV containing only '001'
            # is inferred as integer 1 even when the fitted OneHotEncoder
            # learned the *string* category '001'. This silently changes model
            # input meaning without changing its required header.
            numeric_or_boolean = (
                set(schema["numeric_raw_columns"])
                | set(schema["boolean_raw_columns"])
            )
            text_types = {
                name: str for name in expected if name not in numeric_or_boolean
            }
            raw = pd.read_csv(
                path, encoding=encoding, nrows=MAX_ROWS + 1,
                dtype=text_types,
            )
            break
        except UnicodeError:
            continue
        except pd.errors.ParserError as exc:
            raise ValueError("Invalid prediction CSV structure.") from exc
    if raw is None:
        raise ValueError("Use UTF-8, CP949 or explicitly selected CP932 CSV encoding.")
    if not 1 <= len(raw) <= MAX_ROWS:
        raise ValueError("Input requires 1–20,000 rows.")
    if raw.columns.duplicated().any():
        raise ValueError("Duplicate input column names are not supported.")
    for name in schema["numeric_raw_columns"]:
        if not pd.api.types.is_numeric_dtype(raw[name]):
            raise ValueError(f"Numeric column has invalid dtype: {name}")
        # Match the training input safety boundary: NaN may be imputed, but
        # +/-Infinity is not a finite measurement or a missing value.
        if raw[name].isin([float("inf"), float("-inf")]).any():
            raise ValueError(
                f"Numeric input contains infinite values in column: {name}. "
                "Replace +/-Infinity with a finite value or blank cell."
            )
    for name in schema["boolean_raw_columns"]:
        values = raw[name]
        if pd.api.types.is_bool_dtype(values):
            continue
        # pandas returns object for a True/False CSV column as soon as any
        # row has a blank cell, even though the trained numeric imputer can
        # handle that missing value after boolean -> float conversion.
        # A wholly blank column is likewise a supported missing input.
        if values.isna().all():
            continue
        nonmissing = values.dropna()
        if not (
            pd.api.types.is_object_dtype(values)
            and nonmissing.map(lambda item: isinstance(item, (bool, np.bool_))).all()
        ):
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


def predict_csv(folder: Path, input_csv: Path, output_csv: Path, csv_encoding: str = "auto") -> int:
    model, schema = _model_and_schema(folder)
    raw = _load_input(input_csv, schema, csv_encoding=csv_encoding)
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
    cli.add_argument("--csv-encoding", choices=("auto", "utf-8-sig", "utf-8", "cp949", "cp932"), default="auto")
    args = cli.parse_args()
    try:
        count = predict_csv(args.model_dir, args.input, args.output, csv_encoding=args.csv_encoding)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Predicted {count} rows. Saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
