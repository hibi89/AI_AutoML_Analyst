"""ONTOINSIGHT P85 optional local ML: explicit target, leakage-safe splits.

No customer row/model is exported. The only output is aggregate evaluation
metadata. A local attestation is NOT an authenticated/legal customer signature.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any
import math
import re

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import f1_score, mean_absolute_error
from sklearn.model_selection import (GroupKFold, GroupShuffleSplit, KFold,
                                     StratifiedKFold, TimeSeriesSplit,
                                     train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.app.services.ontoinsight_p70 import InputSource, _raw_csv_rows, _stable_hash
from backend.app.services.tabular_input import read_uploaded_table
from backend.app.services.basic_report import MAX_UPLOAD_BYTES

CONTRACT = "ontoinsight.ml.p85.v1"
_ACK = frozenset({"data_rights_confirmed", "target_and_horizon_confirmed",
                  "features_available_at_prediction_time", "privacy_reviewed",
                  "leakage_reviewed"})
_FORBIDDEN = re.compile(r"(^id$|(^|_)id$|(^|_)(email|phone|mobile|address|ssn|customer|order|user|"
                        r"future|after|post|leak|label|target|outcome|result|prediction|"
                        r"환불후|미래|고객|식별|주민등록|전화|이메일)($|_))", re.I)


def _abstain(reason: str, **details: Any) -> dict[str, Any]:
    return {"contract": CONTRACT, "status": "ML_NOT_SUITABLE",
            "reason": reason, "model_fitted": False, "prediction": None,
            "heldout_score": None, "details": details}


def _frame(source: InputSource) -> tuple[pd.DataFrame, str]:
    if source.source_id != "ml" or not source.filename.lower().endswith(".csv"):
        raise ValueError("P85 accepts one additional explicitly reviewed ML CSV only.")
    if not isinstance(source.content, bytes) or not 0 < len(source.content) <= MAX_UPLOAD_BYTES:
        raise ValueError("Invalid or oversized ML source.")
    imported = read_uploaded_table(source.content, source.filename, csv_encoding=source.encoding)
    columns, rows = _raw_csv_rows(source.content, source.encoding)
    if list(imported.columns) != columns or len(imported) != len(rows):
        raise ValueError("ML CSV parsed row/schema integrity failure.")
    if any(_FORBIDDEN.search(col) for col in columns):
        # The file itself must not contain personal identifiers or post-outcome columns:
        # an operator cannot accidentally include them by merely not selecting them.
        raise ValueError("Identifier, sensitive or future column in ML source.")
    # Preserve textual categories and numeric-looking labels exactly; feature conversion
    # occurs later only for explicitly approved numeric variables.
    return pd.DataFrame(rows, columns=columns), sha256(source.content).hexdigest()


def review_ml_source(source: InputSource) -> dict[str, Any]:
    frame, digest = _frame(source)
    return {"contract": CONTRACT, "source_sha256": digest, "rows": len(frame),
            "columns": list(frame.columns), "schema_digest": _stable_hash(list(frame.columns)),
            "status": "REVIEW_HOLD", "target_approved": False,
            "ml": "NOT_COMPUTED", "raw_rows_exported": False}


def approve_ml_plan(review: dict[str, Any], plan: dict[str, Any],
                    *, actor: str, acknowledgements: dict[str, bool]) -> dict[str, Any]:
    if not isinstance(review, dict) or review.get("contract") != CONTRACT or review.get("status") != "REVIEW_HOLD":
        raise ValueError("Valid ML source review required.")
    if review.get("schema_digest") != _stable_hash(review.get("columns")):
        raise ValueError("ML reviewed schema digest was changed.")
    fields = frozenset({"target", "task", "features", "split_mode",
                        "group_col", "time_col", "horizon"})
    if not isinstance(plan, dict) or set(plan) != fields:
        raise ValueError("Explicit ML target, types, split and horizon required.")
    target, features = plan["target"], plan["features"]
    if not isinstance(target, str) or target not in review["columns"] or _FORBIDDEN.search(target):
        raise ValueError("Invalid or prohibited target column.")
    if not isinstance(features, dict) or not 1 <= len(features) <= 10 or any(
        not isinstance(col, str) or col not in review["columns"] or col == target or _FORBIDDEN.search(col)
        or dtype not in {"numeric", "categorical"} for col, dtype in features.items()
    ):
        raise ValueError("Invalid/unavailable or suspicious ML feature.")
    if plan["task"] not in {"classification", "regression"}:
        raise ValueError("Explicit task required.")
    mode = plan["split_mode"]
    if mode not in {"random", "group", "time"}:
        raise ValueError("Unsupported ML split policy.")
    group, date = plan["group_col"], plan["time_col"]
    if ((mode == "group") != (isinstance(group, str) and group in review["columns"]) or
        (mode == "time") != (isinstance(date, str) and date in review["columns"])):
        raise ValueError("Split requires exactly its own group/time evidence.")
    if mode == "group" and (date is not None or group in features or group == target):
        raise ValueError("Group split must not reuse group as feature.")
    if mode == "time" and (group is not None or date in features or date == target):
        raise ValueError("Time split must not reuse date as feature.")
    if mode == "random" and (group is not None or date is not None):
        raise ValueError("Random split cannot omit known group/time leakage.")
    if not isinstance(plan["horizon"], str) or not 3 <= len(plan["horizon"].strip()) <= 120:
        raise ValueError("Prediction horizon/point-in-time must be declared.")
    if not isinstance(actor, str) or not 1 <= len(actor.strip()) <= 60:
        raise ValueError("Local attestor reference required.")
    if not isinstance(acknowledgements, dict) or set(acknowledgements) != _ACK or any(x is not True for x in acknowledgements.values()):
        raise ValueError("All scope/ML/privacy/target attestations are required.")
    signed_fields = {"contract": CONTRACT, "source_sha256": review["source_sha256"],
                     "schema_digest": review["schema_digest"], "plan": plan,
                     "actor_ref": actor.strip(), "acknowledgements": acknowledgements}
    return {**signed_fields, "state": "APPROVED_LOCAL_ATTESTATION",
            "plan_digest": _stable_hash(signed_fields), "identity_verified": False}


def _pipeline(features: dict[str, str], classification: bool) -> Pipeline:
    nums = [k for k, v in features.items() if v == "numeric"]
    cats = [k for k, v in features.items() if v == "categorical"]
    transforms = []
    if nums:
        transforms.append(("numeric", Pipeline([
            ("fill", SimpleImputer(strategy="median")),
            ("scale", StandardScaler())]), nums))
    if cats:
        transforms.append(("categorical", Pipeline([
            ("fill", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore"))]), cats))
    transform = ColumnTransformer(transforms, remainder="drop")
    model = LogisticRegression(max_iter=300, solver="liblinear", random_state=17) if classification else Ridge(alpha=1.0)
    return Pipeline([("prepare", transform), ("model", model)])


def _validate_table(frame: pd.DataFrame, plan: dict) -> tuple[pd.DataFrame, pd.Series] | str:
    target = plan["target"]
    if len(frame) < 80:
        return "INSUFFICIENT_ROWS"
    if frame[target].isna().any() or frame[target].astype(str).str.strip().eq("").any():
        return "MISSING_TARGET"
    selected = {}
    for col, dtype in plan["features"].items():
        values = frame[col].replace("", np.nan)
        if dtype == "numeric":
            # No locale inference or unbounded numbers.
            values = pd.to_numeric(values, errors="coerce")
            if values.isna().mean() > 0.3 or not np.isfinite(values.dropna().to_numpy(dtype=float)).all():
                return "UNSAFE_NUMERIC_FEATURE"
        elif values.nunique(dropna=True) > 25 or values.dropna().map(lambda s: len(str(s)) > 100).any():
            return "HIGH_CARDINALITY_OR_UNSAFE_CATEGORY"
        if values.notna().sum() < len(frame) * .6:
            return "EXCESSIVE_FEATURE_MISSINGNESS"
        selected[col] = values
    X = pd.DataFrame(selected)
    if plan["task"] == "classification":
        y = frame[target].astype(str)
        counts = y.value_counts()
        if not 2 <= len(counts) <= 8 or counts.min() < 10:
            return "SMALL_OR_IMBALANCED_CLASSES"
    else:
        y = pd.to_numeric(frame[target], errors="coerce")
        if y.isna().any() or not np.isfinite(y.to_numpy(dtype=float)).all() or y.nunique() < 10:
            return "INVALID_REGRESSION_TARGET"
    for col in X:
        if X[col].astype(str).tolist() == y.astype(str).tolist():
            return "DIRECT_TARGET_LEAKAGE"
        if X[col].nunique(dropna=True) < 2:
            return "CONSTANT_FEATURE"
    return X, y


def evaluate_approved_ml(source: InputSource, receipt: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one bounded challenger vs dummy, using train-only CV and single holdout."""
    frame, digest = _frame(source)
    if not isinstance(receipt, dict) or receipt.get("state") != "APPROVED_LOCAL_ATTESTATION":
        raise ValueError("Approved ML plan receipt required.")
    fields = {k: receipt.get(k) for k in ("contract", "source_sha256", "schema_digest",
                                         "plan", "actor_ref", "acknowledgements")}
    if (receipt.get("plan_digest") != _stable_hash(fields) or
        fields["source_sha256"] != digest or fields["schema_digest"] != _stable_hash(list(frame.columns))):
        raise ValueError("ML input or approval digest drift.")
    # Revalidate every declared field; receipt creation alone is not trustworthy.
    review = review_ml_source(source)
    approve_ml_plan(review, fields["plan"], actor=fields["actor_ref"],
                    acknowledgements=fields["acknowledgements"])
    plan = fields["plan"]
    prepared = _validate_table(frame, plan)
    if isinstance(prepared, str):
        return _abstain(prepared, rows=len(frame))
    X, y = prepared
    mode = plan["split_mode"]
    idx = np.arange(len(X))
    classification = plan["task"] == "classification"
    groups = None
    if mode == "time":
        dt = pd.to_datetime(frame[plan["time_col"]], errors="coerce", utc=True, format="ISO8601")
        if dt.isna().any() or dt.nunique() < 8:
            return _abstain("INVALID_OR_INSUFFICIENT_TIME")
        idx = np.argsort(dt.to_numpy(), kind="stable")
        cut = int(len(idx) * .8)
        train_ids, test_ids = idx[:cut], idx[cut:]
        if dt.iloc[train_ids].max() >= dt.iloc[test_ids].min():
            return _abstain("OVERLAPPING_TIME_BOUNDARY")
        cv = TimeSeriesSplit(n_splits=3)
    elif mode == "group":
        groups = frame[plan["group_col"]].astype(str)
        if groups.isna().any() or groups.eq("").any() or groups.nunique() < 10:
            return _abstain("INSUFFICIENT_GROUPS")
        splitter = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=17)
        train_ids, test_ids = next(splitter.split(X, y, groups))
        cv = GroupKFold(n_splits=3)
    else:
        train_ids, test_ids = train_test_split(idx, test_size=.2, random_state=17,
                                              stratify=y if classification else None)
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=17) if classification else KFold(n_splits=3, shuffle=True, random_state=17)
    X_train, X_test = X.iloc[train_ids], X.iloc[test_ids]
    y_train, y_test = y.iloc[train_ids], y.iloc[test_ids]
    if (classification and (y_train.nunique() != y.nunique() or y_test.nunique() != y.nunique()
                           or y_train.value_counts().min() < 3)):
        return _abstain("CLASS_SUPPORT_AT_HOLDOUT")
    train_groups = groups.iloc[train_ids] if groups is not None else None
    baseline = DummyClassifier(strategy="most_frequent") if classification else DummyRegressor(strategy="median")
    challenger = _pipeline(plan["features"], classification)
    # Fold-local fit. Never fit any imputer, encoder, scaler or model on heldout data.
    try:
        cv_pairs = list(cv.split(X_train, y_train, train_groups) if groups is not None else cv.split(X_train, y_train))
        if len(cv_pairs) != 3:
            return _abstain("INVALID_CV_SPLITS")
        b_scores, m_scores = [], []
        for subtrain, subvalid in cv_pairs:
            xfit, yfit = X_train.iloc[subtrain], y_train.iloc[subtrain]
            xval, yval = X_train.iloc[subvalid], y_train.iloc[subvalid]
            if classification and (yfit.nunique() < 2 or yval.nunique() < 2):
                return _abstain("CLASS_SUPPORT_IN_CV")
            baseline.fit(xfit, yfit)
            challenger.fit(xfit, yfit)
            bp, mp = baseline.predict(xval), challenger.predict(xval)
            metric = (lambda actual, predicted: float(f1_score(actual, predicted, average="macro", zero_division=0))) if classification else (lambda actual, predicted: float(mean_absolute_error(actual, predicted)))
            b_scores.append(metric(yval, bp))
            m_scores.append(metric(yval, mp))
        baseline.fit(X_train, y_train)
        challenger.fit(X_train, y_train)
        # One explicit, final heldout assessment per candidate: no refit after seeing it.
        bp, mp = baseline.predict(X_test), challenger.predict(X_test)
        bh, mh = metric(y_test, bp), metric(y_test, mp)
    except (ValueError, TypeError, FloatingPointError) as exc:
        return _abstain("ML_CV_OR_FIT_UNSUITABLE", error_type=type(exc).__name__)
    improves_cv = (np.mean(m_scores) > np.mean(b_scores)) if classification else (np.mean(m_scores) < np.mean(b_scores))
    improves_holdout = (mh > bh) if classification else (mh < bh)
    return {
        "contract": CONTRACT, "status": "EVALUATED_REVIEW_REQUIRED" if improves_cv and improves_holdout else "BASELINE_NOT_BEATEN",
        "prediction": None, "model_fitted": True, "marketing_claim_allowed": False,
        "source_sha256": digest, "plan_digest": receipt["plan_digest"],
        "task": plan["task"], "split_mode": mode, "metric": "f1_macro" if classification else "mae",
        "rows": len(frame), "train_rows": len(train_ids), "heldout_rows": len(test_ids),
        "cv_folds": len(cv_pairs), "baseline_cv_mean": round(float(np.mean(b_scores)), 6),
        "challenger_cv_mean": round(float(np.mean(m_scores)), 6),
        "baseline_heldout": round(float(bh), 6), "challenger_heldout": round(float(mh), 6),
        "cv_challenger_improved": bool(improves_cv), "heldout_challenger_improved": bool(improves_holdout),
        "audit": {
            "holdout_only_evaluated_after_cv": True,
            "preprocessing_inside_every_cv_fold": True,
            "group_overlap": bool(set(groups.iloc[train_ids]) & set(groups.iloc[test_ids])) if groups is not None else None,
            "time_train_before_holdout": bool(pd.to_datetime(frame[plan["time_col"]], utc=True, format="ISO8601").iloc[train_ids].max()
                                             < pd.to_datetime(frame[plan["time_col"]], utc=True, format="ISO8601").iloc[test_ids].min()) if mode == "time" else None,
            "seed": 17,
        },
        "limitations": ["synthetic or locally reviewed only", "not a prospective/causal guarantee",
                        "actual buyer authorization is separate", "no deployed model"],
    }
