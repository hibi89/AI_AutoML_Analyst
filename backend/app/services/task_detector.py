"""Task semantics and target feasibility checks used by the AutoML runner.

Numeric codes and low-cardinality numbers are ambiguous: callers must state
whether they want classification or regression rather than silently guessing.
"""
from __future__ import annotations

import pandas as pd


def detect_task(
    df: pd.DataFrame,
    target_column: str,
    requested_task_type: str | None = None,
) -> dict:
    if target_column not in df.columns:
        raise ValueError(f"target_column '{target_column}' not found in dataframe.")

    y = df[target_column].dropna()
    unique_count = int(y.nunique(dropna=True))
    if unique_count < 2:
        raise ValueError("Target must contain at least two distinct non-null values.")
    if len(y) < 4:
        raise ValueError("At least 4 non-null target rows are required for reliable CV.")

    requested = (requested_task_type or "").strip().lower()
    if requested in ("", "auto", "none"):
        requested = ""
    elif requested not in ("classification", "regression"):
        raise ValueError("task_type must be 'classification', 'regression', or 'auto'.")

    is_bool = pd.api.types.is_bool_dtype(y)
    is_numeric = pd.api.types.is_numeric_dtype(y) and not is_bool

    if requested:
        task_type = requested
        if requested == "regression" and not is_numeric:
            raise ValueError("Regression requires a numeric target (not boolean/text).")
    elif is_bool:
        task_type = "classification"
    elif is_numeric and unique_count <= 20:
        raise ValueError(
            "Ambiguous numeric target with <=20 unique values. "
            "Choose task_type='classification' or 'regression' explicitly."
        )
    elif is_numeric:
        task_type = "regression"
    else:
        task_type = "classification"

    distribution = {}
    if task_type == "classification":
        counts = y.value_counts(dropna=False)
        if int(counts.min()) < 2:
            raise ValueError(
                "Classification requires at least 2 rows per class for stratified CV; "
                "rare class detected. Collect more examples or revise target."
            )
        distribution = {
            str(label): round(float(count / len(y)), 4)
            for label, count in counts.items()
        }
        subtype = (
            "binary_classification" if unique_count == 2
            else "multiclass_classification"
        )
    else:
        subtype = "regression"

    return {
        "target": target_column,
        "unique_count": unique_count,
        "task_type": task_type,
        "subtype": subtype,
        "class_distribution": distribution,
        "non_null_target_rows": len(y),
        "task_type_source": "explicit" if requested else "inferred_unambiguous",
    }
