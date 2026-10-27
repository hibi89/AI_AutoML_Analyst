"""P6E46: exact-schema PREMIUM boolean values may be missing, but not forged.

Training may have an entirely boolean feature. pandas then infers a new-data
CSV containing True/False and one blank as object, rather than bool. Preserve
trained imputation behavior without accepting 0/1 or unrelated strings.
Synthetic fixtures only: no customer data, serialized models or paid APIs.
"""
from __future__ import annotations

import csv

import numpy as np
import pandas as pd
import pytest

from backend.app.services import premium_predict


SCHEMA = {
    "raw_feature_columns": ["flag", "amount"],
    "numeric_raw_columns": ["amount"],
    "boolean_raw_columns": ["flag"],
    "datetime_features": [],
    "prepared_feature_columns": ["flag", "amount"],
}


@pytest.mark.parametrize("flag_column", [
    ["True", "", "False"],
    ["True", "False", "True"],
    ["", "", ""],
])
def test_valid_boolean_inputs_with_optional_missing_values(tmp_path, flag_column):
    source = tmp_path / "new.csv"
    source.write_text(
        "flag,amount\n"
        + "".join(f"{flag},{i + 1}\n" for i, flag in enumerate(flag_column)),
        encoding="utf-8",
    )
    loaded = premium_predict._load_input(source, SCHEMA, "utf-8")
    ready = premium_predict._prepare(loaded, SCHEMA)
    assert len(loaded) == len(flag_column)
    assert list(ready.columns) == ["flag", "amount"]
    assert ready["flag"].isna().sum() == flag_column.count("")
    assert ready["flag"].dropna().tolist() == [
        float(flag == "True") for flag in flag_column if flag != ""
    ]
    assert pd.api.types.is_float_dtype(ready["flag"])


@pytest.mark.parametrize("invalid", [
    "yes", "no", "1", "0", "True-ish", "Infinity", "-Infinity",
])
def test_bad_boolean_literals_still_fail_closed(tmp_path, invalid):
    source = tmp_path / "bad.csv"
    source.write_text(
        f"flag,amount\nTrue,1\n{invalid},2\nFalse,3\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Boolean column has invalid dtype"):
        premium_predict._load_input(source, SCHEMA, "utf-8")


def test_actual_predict_csv_keeps_row_alignment_and_does_not_overwrite(tmp_path, monkeypatch):
    source = tmp_path / "new.csv"
    output = tmp_path / "out.csv"
    source.write_text("flag,amount\nTrue,1\n,2\nFalse,3\n", encoding="utf-8")

    class InspectModel:
        def predict(self, frame):
            assert frame["flag"].tolist()[0] == 1.0
            assert np.isnan(frame["flag"].iloc[1])
            assert frame["flag"].iloc[2] == 0.0
            assert frame["amount"].tolist() == [1, 2, 3]
            return np.array([1, 0, 1])

    monkeypatch.setattr(
        premium_predict, "_model_and_schema",
        lambda folder: (InspectModel(), SCHEMA),
    )
    assert premium_predict.predict_csv(tmp_path, source, output, "utf-8") == 3
    with output.open("r", encoding="utf-8-sig", newline="") as stream:
        assert list(csv.reader(stream)) == [
            ["prediction"], ["1"], ["0"], ["1"],
        ]
    with pytest.raises(ValueError, match="Output path exists"):
        premium_predict.predict_csv(tmp_path, source, output, "utf-8")
