"""Conservative P6D ML resource gate; BASIC descriptive reporting is unaffected.

Limits are provisional operating limits, not assertions that larger datasets
cannot be modeled. Reject before costly CV/tuning rather than silently sample.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

@dataclass(frozen=True)
class MLWorkloadBudget:
    tier: str
    row_limit: int
    encoded_feature_limit: int
    train_matrix_cell_limit: int

POLICIES = {
    3: MLWorkloadBudget("STANDARD", 5000, 180, 600_000),
    5: MLWorkloadBudget("PREMIUM", 3000, 140, 360_000),
}


def policy_for(max_challengers: int) -> MLWorkloadBudget:
    if type(max_challengers) is not int or max_challengers not in POLICIES:
        raise ValueError("Model workload tier must be STANDARD (3) or PREMIUM (5).")
    return POLICIES[max_challengers]


def check_rows(n_rows: int, max_challengers: int) -> None:
    policy = policy_for(max_challengers)
    if n_rows > policy.row_limit:
        raise ValueError(
            f"{policy.tier} ML capacity limit: {n_rows:,} rows exceeds "
            f"{policy.row_limit:,} rows; use BASIC for diagnostics or "
            "request a separately quoted larger-data model assessment. "
            "Rows are not silently sampled."
        )


def estimate_training_matrix(train_features: pd.DataFrame, numeric: list[str],
                             categorical: list[str], max_challengers: int) -> dict:
    """Conservative train-only one-hot footprint estimate, no unknown holdout labels."""
    policy = policy_for(max_challengers)
    encoded_numeric = len(numeric)
    encoded_categorical = sum(
        max(1, int(train_features[col].nunique(dropna=True)))
        for col in categorical
    )
    encoded = encoded_numeric + encoded_categorical
    cells = int(len(train_features)) * encoded
    if encoded > policy.encoded_feature_limit or cells > policy.train_matrix_cell_limit:
        raise ValueError(
            f"{policy.tier} ML capacity limit: estimated {encoded:,} encoded "
            f"features and {cells:,} train cells exceed limits "
            f"({policy.encoded_feature_limit:,} features, "
            f"{policy.train_matrix_cell_limit:,} train cells). "
            "Remove high-cardinality identifiers, reduce scope, or request "
            "a separate large-data assessment. No silent sampling."
        )
    return {
        **asdict(policy),
        "estimated_encoded_features": encoded,
        "estimated_train_cells": cells,
        "raw_training_rows": int(len(train_features)),
        "high_cardinality_rule": "Train-only cardinalities before OneHotEncoder",
        "note": "Provisional capacity guard; not an observed throughput guarantee",
    }
