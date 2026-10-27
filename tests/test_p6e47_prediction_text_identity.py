"""P6E47: categorical text must retain literal identity in repeat prediction.

All input is synthetic. A trained string category '001' must not be silently
interpreted as integer 1 merely because a new prediction batch has numeric-
looking categories only. No sklearn pipeline archive is loaded in these tests.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

from backend.app.services.premium_predict import _load_input, _prepare


SCHEMA = {
    "raw_feature_columns": ["shop_code", "event_date", "amount", "flag"],
    "numeric_raw_columns": ["amount"],
    "boolean_raw_columns": ["flag"],
    "datetime_features": ["event_date"],
    "prepared_feature_columns": [
        "shop_code", "event_date__year", "event_date__month",
        "event_date__day", "event_date__dayofweek", "event_date__hour",
        "amount", "flag",
    ],
}


def test_numeric_looking_category_preserves_leading_zero_exact_identity(tmp_path):
    # The training text column had categories ['001', 'A']. On a purely
    # numeric-looking inference batch pandas otherwise infers int [1, 2].
    source = tmp_path / "new.csv"
    source.write_text(
        "shop_code,event_date,amount,flag\n"
        "001,20260101,10,True\n"
        "002,20260102,20,False\n", encoding="utf-8",
    )
    raw = _load_input(source, SCHEMA, "utf-8")
    assert raw["shop_code"].tolist() == ["001", "002"]
    assert raw["shop_code"].dtype == object
    assert raw["event_date"].tolist() == ["20260101", "20260102"]
    assert raw["amount"].tolist() == [10, 20]
    assert raw["flag"].tolist() == [True, False]
    prepared = _prepare(raw, SCHEMA)
    assert prepared["shop_code"].tolist() == ["001", "002"]
    assert prepared["event_date__year"].tolist() == [2026, 2026]
    assert prepared["event_date__day"].tolist() == [1, 2]
    # The fitted encoder must recognize the *string* '001', not unknown int 1.
    encoder = OneHotEncoder(handle_unknown="ignore")
    encoder.fit(np.array([["001"], ["A"]], dtype=object))
    encoded = encoder.transform(prepared[["shop_code"]]).toarray()
    assert encoded[0].sum() == 1
    assert encoded[0, 0] == 1
    assert encoded[1].sum() == 0  # unseen '002' remains unknown


def test_mixed_string_categories_and_missing_are_preserved(tmp_path):
    source = tmp_path / "new.csv"
    source.write_text(
        "shop_code,event_date,amount,flag\n"
        "001,20260101,1,True\n"
        "A,20260102,2,\n"
        ",20260103,3,False\n", encoding="utf-8",
    )
    raw = _load_input(source, SCHEMA)
    assert raw["shop_code"].iloc[:2].tolist() == ["001", "A"]
    assert pd.isna(raw["shop_code"].iloc[2])
    prepared = _prepare(raw, SCHEMA)
    assert prepared["flag"].tolist()[0] == 1.0
    assert pd.isna(prepared["flag"].iloc[1])
    assert prepared["flag"].tolist()[2] == 0.0
    assert prepared["amount"].tolist() == [1, 2, 3]


def test_legacy_schema_without_new_fields_works_unchanged(tmp_path):
    # No schema file format migration is necessary: fields already shipped in
    # model_schema.json suffice to identify text vs numeric/boolean raw inputs.
    schema = {
        "raw_feature_columns": ["region", "amount"],
        "numeric_raw_columns": ["amount"],
        "boolean_raw_columns": [],
        "datetime_features": [],
        "prepared_feature_columns": ["region", "amount"],
    }
    source = tmp_path / "older.csv"
    source.write_text("region,amount\n00012,1\n00013,2\n", encoding="utf-8")
    raw = _load_input(source, schema)
    assert raw["region"].tolist() == ["00012", "00013"]
    assert raw["amount"].tolist() == [1, 2]
    assert _prepare(raw, schema)["region"].tolist() == ["00012", "00013"]
