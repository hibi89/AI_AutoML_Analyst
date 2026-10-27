"""Aggregate-only ML validation tables; no row-level labels/predictions."""
from __future__ import annotations

import csv
import math
from io import StringIO
from backend.app.services.basic_report import _csv_safe

_HIGHER = frozenset({"accuracy", "balanced_accuracy", "f1_weighted", "r2"})
_LOWER = frozenset({"mae", "rmse"})


def _csv_bytes(rows: list[list[object]]) -> bytes:
    out = StringIO(newline="")
    csv.writer(out).writerows(rows)
    return ("\ufeff" + out.getvalue()).encode("utf-8")


def holdout_scores_csv(analysis: dict) -> bytes:
    """Show selected vs Dummy on the same untouched holdout, NOT CV selection."""
    selected = analysis["selected_holdout_metrics"]
    dummy = analysis["dummy_holdout_metrics"]
    primary = analysis["primary_metric"]
    if set(selected) != set(dummy) or primary not in selected:
        raise ValueError("Holdout metrics do not match the Dummy baseline.")
    rows: list[list[object]] = [[
        "metric", "direction", "selected_model", "selected_holdout",
        "dummy_model", "dummy_holdout", "selected_minus_dummy",
        "selected_better_on_metric", "primary_holdout_beats_dummy",
        "selection_basis",
    ]]
    for metric, selected_value in selected.items():
        if metric not in _HIGHER | _LOWER:
            raise ValueError("Unsupported holdout metric.")
        value = float(selected_value)
        baseline = float(dummy[metric])
        if not math.isfinite(value) or not math.isfinite(baseline):
            raise ValueError("Holdout metrics must be finite.")
        direction = "higher_is_better" if metric in _HIGHER else "lower_is_better"
        better = value > baseline if metric in _HIGHER else value < baseline
        rows.append([
            _csv_safe(metric), direction,
            _csv_safe(analysis["selected_model"]), value,
            _csv_safe(analysis["dummy_model"]), baseline, value - baseline,
            "yes" if better else "no",
            "yes" if analysis["holdout_beats_dummy"] else "no",
            "selected_by_training_cv_only",
        ])
    return _csv_bytes(rows)


def feature_importance_csv(analysis: dict) -> bytes | None:
    """Optional model-internal relative importance, not a causal explanation."""
    items = analysis.get("training_feature_importance") or []
    if not items:
        return None
    rows: list[list[object]] = [[
        "feature", "importance", "method", "selected_model", "interpretation",
    ]]
    for item in items:
        value = float(item["importance"])
        if not math.isfinite(value) or value < 0:
            raise ValueError("Importance must be finite and non-negative.")
        rows.append([
            _csv_safe(item["feature"]), value, _csv_safe(item["method"]),
            _csv_safe(analysis["selected_model"]), "model_internal_not_causal",
        ])
    return _csv_bytes(rows)
