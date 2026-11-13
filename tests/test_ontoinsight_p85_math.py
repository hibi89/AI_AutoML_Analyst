"""Precision and final heldout trace for the P85 core 30 gate."""
from __future__ import annotations

from backend.app.services.ontoinsight_p70 import InputSource, approve_mapping, review_sources, run_approved
from backend.app.services.ontoinsight_p85_ml import evaluate_approved_ml
from test_ontoinsight_p85_ml import sample, approved


def test_core22_decimal_nonbinary_exact_money():
    src = [
        InputSource("orders", "orders.csv",
                    b"order_id,gross,channel\n001,0.10,web\n002,0.20,web\n"),
        InputSource("refunds", "refunds.csv", b"order_id,amount\n001,0.00\n")
    ]
    receipt = approve_mapping(
        review_sources(src),
        {"orders": {"order_id": "order_id", "sales": "gross", "channel": "channel"},
         "refunds": {"order_id": "order_id", "refund": "amount"}},
        {"currency": "KRW", "tax_basis": "included", "sales_basis": "gross_paid",
         "refund_basis": "positive_refund_events", "time_basis": "no_period_reporting"},
        actor="synthetic",
        acknowledgements={k: True for k in (
            "data_use_authorized", "business_meaning_confirmed", "privacy_reviewed",
            "gross_sales_basis_confirmed", "refund_event_basis_confirmed", "tax_policy_confirmed")})
    result = run_approved(src, receipt)
    assert result["metrics"]["gross_sales"] == "0.30"
    assert result["metrics"]["net_sales"] == "0.30"
    assert result["metrics"]["aov_net"] == "0.15"
    assert all(result["audit"].values())


def test_core34_cv_heldout_separation_has_no_exported_prediction_rows():
    source = sample()
    result = evaluate_approved_ml(source, approved(source))
    assert result["model_fitted"]
    assert result["cv_folds"] == 3
    assert result["train_rows"] == 96
    assert result["heldout_rows"] == 24
    assert result["audit"]["preprocessing_inside_every_cv_fold"]
    assert result["audit"]["holdout_only_evaluated_after_cv"]
    assert result["prediction"] is None
    assert "customer_ids" not in result
