"""Synthetic-only P85 ML policy and leakage tests on original sklearn runtime."""
from __future__ import annotations

import hashlib

import pytest

from backend.app.services.ontoinsight_p70 import InputSource
from backend.app.services.ontoinsight_p85_ml import (
    approve_ml_plan, evaluate_approved_ml, review_ml_source,
)


def sample(n=120, *, constant=False, irregular_date=False, imbalance=False):
    result = ["x,segment,renewed,demand,store_bucket,event_date"]
    for i in range(n):
        label = "yes" if i % 2 == 0 else "no"
        if imbalance:
            label = "no" if i < n - 4 else "yes"
        segment = "north" if i % 3 == 0 else "south"
        date = f"2026-01-{(i % 28)+1:02d}" if irregular_date else (
            __import__("datetime").date(2026, 1, 1) + __import__("datetime").timedelta(days=i)
        ).isoformat()
        result.append(f"{i if not constant else 1},{segment},{label},{100+2*i+i%7},group_{i//10},{date}")
    return InputSource("ml", "synthetic.csv", ("\n".join(result)+"\n").encode())


def plan(*, task="classification", mode="random"):
    return {"target": "renewed" if task == "classification" else "demand",
            "task": task, "features": {"x": "numeric", "segment": "categorical"},
            "split_mode": mode,
            "group_col": "store_bucket" if mode == "group" else None,
            "time_col": "event_date" if mode == "time" else None,
            "horizon": "Approved at checkout before next-period outcome observed"}


def approved(src, policy=None):
    p = policy or plan()
    return approve_ml_plan(review_ml_source(src), p,
                           actor="synthetic-reviewer",
                           acknowledgements={k: True for k in (
                               "data_rights_confirmed", "target_and_horizon_confirmed",
                               "features_available_at_prediction_time",
                               "privacy_reviewed", "leakage_reviewed",
                           )})


def test_explicit_classification_dummy_cv_and_single_heldout():
    source = sample()
    res = evaluate_approved_ml(source, approved(source))
    assert res["model_fitted"] is True
    assert res["status"] in {"BASELINE_NOT_BEATEN", "EVALUATED_REVIEW_REQUIRED"}
    assert res["metric"] == "f1_macro"
    assert res["train_rows"] + res["heldout_rows"] == 120
    assert res["cv_folds"] == 3
    assert res["audit"]["preprocessing_inside_every_cv_fold"]
    assert res["audit"]["holdout_only_evaluated_after_cv"]
    assert res["prediction"] is None
    assert res["marketing_claim_allowed"] is False


def test_regression_uses_mae_and_dummy_comparison():
    source = sample()
    res = evaluate_approved_ml(source, approved(source, plan(task="regression")))
    assert res["model_fitted"] is True
    assert res["metric"] == "mae"
    assert res["baseline_cv_mean"] >= 0
    assert res["challenger_heldout"] >= 0


def test_group_split_heldout_has_no_group_overlap():
    source = sample()
    res = evaluate_approved_ml(source, approved(source, plan(mode="group")))
    assert res["model_fitted"] is True
    assert res["audit"]["group_overlap"] is False


def test_time_split_is_chronological():
    source = sample()
    res = evaluate_approved_ml(source, approved(source, plan(mode="time")))
    assert res["model_fitted"] is True
    assert res["audit"]["time_train_before_holdout"] is True


def test_review_only_never_fits_or_exposes_raw_rows():
    review = review_ml_source(sample())
    assert review["status"] == "REVIEW_HOLD"
    assert review["ml"] == "NOT_COMPUTED"
    assert review["raw_rows_exported"] is False
    assert "north" not in str(review)


def test_unapproved_receipt_is_rejected():
    with pytest.raises(ValueError, match="Approved ML"):
        evaluate_approved_ml(sample(), {})


def test_approval_source_change_rejected():
    source = sample()
    receipt = approved(source)
    changed = InputSource("ml", "synthetic.csv", source.content.replace(b"north", b"east"))
    with pytest.raises(ValueError, match="digest drift"):
        evaluate_approved_ml(changed, receipt)


def test_approval_plan_change_rejected():
    source = sample()
    receipt = approved(source)
    receipt["plan"]["horizon"] = "after outcome"
    with pytest.raises(ValueError, match="digest drift"):
        evaluate_approved_ml(source, receipt)


def test_no_privacy_attestation_rejected():
    source = sample()
    ack = {k: True for k in ("data_rights_confirmed", "target_and_horizon_confirmed",
                              "features_available_at_prediction_time", "privacy_reviewed", "leakage_reviewed")}
    ack["privacy_reviewed"] = False
    with pytest.raises(ValueError, match="attestations"):
        approve_ml_plan(review_ml_source(source), plan(), actor="reviewer", acknowledgements=ack)


def test_future_feature_name_rejected():
    source = sample()
    p = plan()
    p["features"] = {"post_outcome": "numeric"}
    with pytest.raises(ValueError, match="suspicious"):
        approved(source, p)


def test_feature_same_as_target_rejected():
    source = sample()
    p = plan()
    p["features"] = {"renewed": "categorical"}
    with pytest.raises(ValueError, match="suspicious"):
        approved(source, p)


def test_missing_horizon_rejected():
    source = sample()
    p = plan()
    p["horizon"] = ""
    with pytest.raises(ValueError, match="horizon"):
        approved(source, p)


def test_random_split_forbids_undeclared_group_column():
    source = sample()
    p = plan()
    p["group_col"] = "store_bucket"
    with pytest.raises(ValueError, match="Random split"):
        approved(source, p)


def test_group_key_as_feature_rejected():
    source = sample()
    p = plan(mode="group")
    p["features"]["store_bucket"] = "categorical"
    with pytest.raises(ValueError, match="Group split"):
        approved(source, p)


def test_time_date_as_feature_rejected():
    source = sample()
    p = plan(mode="time")
    p["features"]["event_date"] = "categorical"
    with pytest.raises(ValueError, match="Time split"):
        approved(source, p)


def test_insufficient_rows_abstain_without_fit():
    source = sample(n=48)
    res = evaluate_approved_ml(source, approved(source))
    assert res["status"] == "ML_NOT_SUITABLE"
    assert res["reason"] == "INSUFFICIENT_ROWS"
    assert res["model_fitted"] is False


def test_small_imbalanced_class_abstain():
    source = sample(imbalance=True)
    res = evaluate_approved_ml(source, approved(source))
    assert res["status"] == "ML_NOT_SUITABLE"
    assert res["reason"] == "SMALL_OR_IMBALANCED_CLASSES"


def test_constant_feature_abstain():
    source = sample(constant=True)
    res = evaluate_approved_ml(source, approved(source))
    assert res["status"] == "ML_NOT_SUITABLE"
    assert res["reason"] == "CONSTANT_FEATURE"


def test_overlapping_time_boundary_abstain():
    source = sample(irregular_date=True)
    res = evaluate_approved_ml(source, approved(source, plan(mode="time")))
    assert res["status"] == "ML_NOT_SUITABLE"
    assert res["reason"] in {"OVERLAPPING_TIME_BOUNDARY", "CLASS_SUPPORT_IN_CV"}


def test_unapproved_sensitive_column_excluded_even_if_not_feature():
    source = sample()
    rows = source.content.decode().replace(",event_date", ",event_date,email").replace("\n", ",sample@example.invalid\n", 1)
    with pytest.raises(ValueError, match="Identifier"):
        review_ml_source(InputSource("ml", "synthetic.csv", rows.encode()))


def test_extra_numeric_code_guarded_as_id_column():
    source = sample()
    modified = source.content.replace(b"x,segment", b"order_id,segment")
    with pytest.raises(ValueError, match="Identifier"):
        review_ml_source(InputSource("ml", "synthetic.csv", modified))


def test_model_evidence_never_leaks_synthetic_row_values():
    source = sample()
    res = evaluate_approved_ml(source, approved(source))
    assert "north" not in str(res)
    assert "group_0" not in str(res)
    assert "2026-01-01" not in str(res)
