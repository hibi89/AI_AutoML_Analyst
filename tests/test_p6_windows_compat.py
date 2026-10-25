"""Windows-friendly PREMIUM pipeline reload tests; no GUI/font/PDF dependency."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import sklearn
import skops
import skops.io as sio
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.app.services.premium_predict import predict_csv


@pytest.fixture()
def trusted_bundle(tmp_path: Path) -> tuple[Path, Path]:
    sample = pd.DataFrame({"a": [1., 2., 3., 4., 5., 6., 7., 8.],
                           "b": [11., 12., 13., 14., 15., 16., 17., 18.]})
    target = pd.Series([0, 0, 0, 0, 1, 1, 1, 1])
    pipe = Pipeline([
        ("preprocess", StandardScaler()),
        ("model", LogisticRegression(max_iter=200, random_state=42)),
    ]).fit(sample, target)
    model_bytes = sio.dumps(pipe)
    unknown = sio.get_untrusted_types(data=model_bytes)
    assert set(unknown) <= {"numpy.dtype"}, unknown
    schema = {
        "format": "automl-premium-v1",
        "model_sha256": sha256(model_bytes).hexdigest(),
        "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
        "versions": {
            "sklearn": sklearn.__version__,
            "skops": skops.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "raw_feature_columns": ["a", "b"],
        "numeric_raw_columns": ["a", "b"],
        "boolean_raw_columns": [],
        "datetime_features": [],
        "prepared_feature_columns": ["a", "b"],
    }
    (tmp_path / "model_pipeline.skops").write_bytes(model_bytes)
    (tmp_path / "model_schema.json").write_text(json.dumps(schema), encoding="utf-8")
    source = tmp_path / "new.csv"
    sample.iloc[:3].to_csv(source, index=False)
    return tmp_path, source


def test_safe_model_load_and_predict_cross_platform(trusted_bundle):
    folder, source = trusted_bundle
    result = folder / "result.csv"
    assert predict_csv(folder, source, result) == 3
    frame = pd.read_csv(result)
    assert frame.shape == (3, 1)
    assert list(frame.columns) == ["prediction"]


def test_output_collision_and_input_header_rejected(trusted_bundle):
    folder, source = trusted_bundle
    with pytest.raises(ValueError, match="overwrite input"):
        predict_csv(folder, source, source)
    bad = folder / "reordered.csv"
    pd.read_csv(source)[["b", "a"]].to_csv(bad, index=False)
    with pytest.raises(ValueError, match="header mismatch"):
        predict_csv(folder, bad, folder / "reordered_predictions.csv")


def test_modified_model_rejected(trusted_bundle):
    folder, source = trusted_bundle
    model_path = folder / "model_pipeline.skops"
    model_path.write_bytes(model_path.read_bytes() + b"appended")
    with pytest.raises(ValueError, match="checksum mismatch"):
        predict_csv(folder, source, folder / "result.csv")


def test_dependency_version_mismatch_rejected(trusted_bundle):
    folder, source = trusted_bundle
    schema = folder / "model_schema.json"
    data = json.loads(schema.read_text(encoding="utf-8"))
    data["versions"]["numpy"] = "0.0-fake"
    schema.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Dependency versions differ"):
        predict_csv(folder, source, folder / "result.csv")
