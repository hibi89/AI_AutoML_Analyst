"""P5 local PREMIUM model fit -> serialized bundle -> repeated prediction tests."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.app.main import app
from backend.app.services.premium_predict import predict_csv


def synthetic():
    n = 96
    return pd.DataFrame({
        "visits": [i % 17 + 1 for i in range(n)],
        "revenue": [float(5 + i % 17 * 2) for i in range(n)],
        "region": ["A", "B", "C"] * (n // 3),
        "target": [i % 2 for i in range(n)],
    })


@pytest.fixture(scope="module")
def bundle():
    df = synthetic()
    res = TestClient(app).post(
        "/api/premium-report",
        data={"target_column": "target", "task_type": "classification", "cv": "3"},
        files={"file": ("synthetic.csv", BytesIO(df.to_csv(index=False).encode()), "text/csv")},
    )
    assert res.status_code == 200, res.text
    return res.content


def test_premium_ui_local_guard():
    client = TestClient(app)
    assert client.get("/premium-mvp").status_code == 200
    assert client.get("/premium-mvp", headers={"host": "evil.example"}).status_code == 403


def test_premium_full_zip_and_five_challengers(bundle):
    with ZipFile(BytesIO(bundle)) as z:
        filenames = set(z.namelist())
        assert {"report.pdf", "model_pipeline.skops", "model_schema.json",
                "premium_summary.json", "model_scores.csv", "predict.py",
                "predict.cmd", "sample_input.csv", "sample_predictions.csv",
                "requirements-premium.txt", "manifest.json"} <= filenames
        info = json.loads(z.read("premium_summary.json"))
        assert info["tier"] == "PREMIUM"
        assert info["challenger_budget"] == 5
        assert len(info["models"]) == 6
        assert len([m for m in info["models"] if m["role"] == "baseline"]) == 1
        assert len([m for m in info["models"] if m["role"] == "challenger"]) == 5
        assert info["holdout_used_in_selection"] is False
        assert len(PdfReader(BytesIO(z.read("report.pdf"))).pages) >= 10
        schema = json.loads(z.read("model_schema.json"))
        assert schema["raw_feature_columns"] == ["visits", "revenue", "region"]
        assert b"\x80\x04" not in z.read("model_pipeline.skops")[:2]
        assert z.read("sample_input.csv").decode("utf-8-sig").strip() == "visits,revenue,region"
        assert z.read("sample_predictions.csv") == b"prediction\r\n"
        import hashlib
        entries = json.loads(z.read("manifest.json"))["files"]
        assert all(hashlib.sha256(z.read(e["path"])).hexdigest() == e["sha256"] for e in entries)


def test_premium_prediction_and_schema_checks(bundle, tmp_path):
    with ZipFile(BytesIO(bundle)) as z:
        for name in ("model_pipeline.skops", "model_schema.json"):
            (tmp_path / name).write_bytes(z.read(name))
    raw = synthetic().drop(columns=["target"]).iloc[:6]
    incoming = tmp_path / "new_data.csv"
    outgoing = tmp_path / "predictions.csv"
    raw.to_csv(incoming, index=False)
    count = predict_csv(tmp_path, incoming, outgoing)
    assert count == 6
    pred = pd.read_csv(outgoing)
    assert len(pred) == count
    assert list(pred.columns) == ["prediction"]
    with pytest.raises(ValueError, match="Output path exists"):
        predict_csv(tmp_path, incoming, outgoing)

    wrong = tmp_path / "wrong.csv"
    raw[["region", "revenue", "visits"]].to_csv(wrong, index=False)
    with pytest.raises(ValueError, match="header mismatch"):
        predict_csv(tmp_path, wrong, tmp_path / "wrong_out.csv")

    model_path = tmp_path / "model_pipeline.skops"
    model_path.write_bytes(model_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        predict_csv(tmp_path, incoming, tmp_path / "after_tampering.csv")


def test_premium_input_requires_target_semantics():
    df = synthetic()
    res = TestClient(app).post(
        "/api/premium-report",
        data={"target_column": "target", "task_type": "auto"},
        files={"file": ("synthetic.csv", BytesIO(df.to_csv(index=False).encode()), "text/csv")},
    )
    assert res.status_code == 400
    assert "Ambiguous numeric" in res.text
