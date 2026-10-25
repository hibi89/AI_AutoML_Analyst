"""P6D budget regressions: costly ML must fail BEFORE CV and without sampling."""
from io import BytesIO
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.basic_report import validate_basic_frame
from backend.app.services.ml_workload_policy import (
    check_rows, estimate_training_matrix, policy_for,
)
from backend.app.services.standard_engine import run_standard


@pytest.mark.parametrize("n,tier,limit", [
    (5001, 3, 5000), (3001, 5, 3000),
    (20000, 3, 5000), (20000, 5, 3000),
])
def test_ml_rows_explicitly_rejected_without_training(n, tier, limit, monkeypatch):
    import backend.app.services.standard_engine as engine
    called=[]
    monkeypatch.setattr(engine, "detect_task", lambda *args, **kw: called.append(True))
    frame=pd.DataFrame({"a":np.arange(n), "target":np.arange(n)%2})
    with pytest.raises(ValueError, match=f"{limit:,} rows"):
        run_standard(frame, "target", "classification", max_challengers=tier)
    assert not called, "row budget must precede any task semantics/model CV"
    assert len(frame)==n, "source must not be silently sampled or overwritten"


def test_basic_still_accepts_large_data_for_diagnostics():
    frame=pd.DataFrame({"a":np.arange(20000), "b":np.arange(20000)%3})
    validate_basic_frame(frame)


def test_high_cardinality_encoded_matrix_refused_before_fit():
    n=150
    rng=np.arange(n)
    data={f"category_{i}":pd.Series([f"segment_{v%45}" for v in rng])
          for i in range(8)}
    data["target"]=rng%2
    df=pd.DataFrame(data)
    with pytest.raises(ValueError, match="estimated.*encoded"):
        run_standard(df, "target", "classification", max_challengers=3)


def test_budget_estimates_training_categories_and_is_deterministic():
    features=pd.DataFrame({
        "value":[float(x) for x in range(160)],
        "segment":[f"S{x%5}" for x in range(160)],
    })
    result=estimate_training_matrix(features, ["value"], ["segment"], 3)
    assert result["estimated_encoded_features"]==6
    assert result["estimated_train_cells"]==960
    assert result["row_limit"]==5000
    assert policy_for(5).row_limit==3000
    with pytest.raises(ValueError, match="must be"):
        policy_for(True)


@pytest.mark.parametrize("route", ["standard", "premium"])
def test_http_ml_guard_returns_400_not_500(route):
    n=5002 if route=="standard" else 3002
    df=pd.DataFrame({"value":np.arange(n), "target":np.arange(n)%2})
    r=TestClient(app).post(
        f"/api/{route}-report",
        data={"target_column":"target","task_type":"classification"},
        files={"file":("synthetic.csv",BytesIO(df.to_csv(index=False).encode()),"text/csv")},
    )
    assert r.status_code==400, r.text
    assert "ML capacity limit" in r.text
