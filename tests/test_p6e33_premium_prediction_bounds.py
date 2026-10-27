"""P6E33: bounded PREMIUM repeat-prediction CSV parsing.

The client-side prediction utility must not read arbitrary extra rows before
checking its declared 20,000-row delivery limit. Synthetic inputs only.
"""
from __future__ import annotations

import pandas as pd
import pytest

from backend.app.services import premium_predict


def _schema(*columns: str) -> dict:
    return {
        "raw_feature_columns": list(columns),
        "numeric_raw_columns": [columns[0]],
        "boolean_raw_columns": [],
    }


def test_prediction_csv_exact_max_rows_succeeds(tmp_path):
    path = tmp_path / "max_allowed.csv"
    path.write_text(
        "feature,label\n" + "1,A\n" * premium_predict.MAX_ROWS,
        encoding="utf-8",
    )
    result = premium_predict._load_input(path, _schema("feature", "label"), "utf-8")
    assert len(result) == premium_predict.MAX_ROWS
    assert list(result.columns) == ["feature", "label"]


def test_overflow_rejected_using_one_extra_row_not_full_file(tmp_path, monkeypatch):
    path = tmp_path / "over_limit.csv"
    path.write_text(
        "feature,label\n" + "1,A\n" * (premium_predict.MAX_ROWS + 5),
        encoding="utf-8",
    )
    original = pd.read_csv
    limits = []

    def bounded_read(*args, **kwargs):
        limits.append(kwargs.get("nrows"))
        return original(*args, **kwargs)

    monkeypatch.setattr(premium_predict.pd, "read_csv", bounded_read)
    with pytest.raises(ValueError, match="1–20,000 rows"):
        premium_predict._load_input(path, _schema("feature", "label"), "utf-8")
    assert limits == [premium_predict.MAX_ROWS + 1]


def test_bad_original_header_rejected_before_dataframe_parse(tmp_path, monkeypatch):
    path = tmp_path / "not_the_schema.csv"
    path.write_text("unexpected,label\n1,A\n", encoding="utf-8")

    def forbidden_read(*args, **kwargs):
        raise AssertionError("mismatched original header reached pandas")

    monkeypatch.setattr(premium_predict.pd, "read_csv", forbidden_read)
    with pytest.raises(ValueError, match="Input header mismatch"):
        premium_predict._load_input(path, _schema("feature", "label"), "utf-8")


def test_valid_cp932_exact_schema_stays_supported(tmp_path):
    path = tmp_path / "japanese.csv"
    path.write_bytes("売上,購入\n100,yes\n200,no\n".encode("cp932"))
    result = premium_predict._load_input(path, _schema("売上", "購入"), "cp932")
    assert result["売上"].tolist() == [100, 200]
    assert list(result.columns) == ["売上", "購入"]


def test_file_size_limit_rejects_before_read(tmp_path, monkeypatch):
    path = tmp_path / "limit.csv"
    path.write_text("feature,label\n1,A\n", encoding="utf-8")
    monkeypatch.setattr(premium_predict, "MAX_CSV_BYTES", path.stat().st_size - 1)
    with pytest.raises(ValueError, match="exceeds 30 MiB"):
        premium_predict._load_input(path, _schema("feature", "label"), "utf-8")
