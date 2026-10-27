"""P6E25: forward CV must never split rows with identical timestamps.

Synthetic-only regressions. Standard/Premium share run_standard; no customer
records or new ML libraries are required.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import TimeSeriesSplit

from backend.app.services import standard_engine
from backend.app.services.standard_engine import _chronological_timestamp_cv, run_standard


def test_original_row_based_split_did_leak_identical_timestamps():
    dates = pd.Series(pd.date_range("2026-01-01", periods=30).repeat(3)).reset_index(drop=True)
    unsafe = list(TimeSeriesSplit(n_splits=3).split(dates))
    assert any(dates.iloc[a[-1]] == dates.iloc[b[0]] for a, b in unsafe)
    corrected = _chronological_timestamp_cv(dates, 3)
    assert len(corrected) == 3
    for train_indices, valid_indices in corrected:
        assert len(train_indices) > 0 and len(valid_indices) > 0
        assert dates.iloc[train_indices].max() < dates.iloc[valid_indices].min()
        assert set(dates.iloc[train_indices]).isdisjoint(set(dates.iloc[valid_indices]))
        assert np.array_equal(train_indices, np.arange(train_indices[0], train_indices[-1] + 1))
        assert np.array_equal(valid_indices, np.arange(valid_indices[0], valid_indices[-1] + 1))


def test_chronological_cv_rejects_unsorted_or_insufficient_unique_times():
    with pytest.raises(ValueError, match="sorted"):
        _chronological_timestamp_cv(
            pd.Series(pd.to_datetime(["2026-01-02", "2026-01-01", "2026-01-03"])), 2
        )
    with pytest.raises(ValueError, match="at least 3"):
        _chronological_timestamp_cv(
            pd.Series(pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-02"])), 2
        )


def test_real_standard_training_respects_timestamp_groups_through_cv(monkeypatch):
    n = 120
    records = pd.DataFrame({
        "event_date": pd.date_range("2026-01-01", periods=n // 3).repeat(3).strftime("%Y-%m-%d"),
        "visits": [i % 11 + 2 for i in range(n)],
        "segment": ["A", "B", "C"] * (n // 3),
        "target": [float(2.3 * (i % 11) + (i // 3) * .11 + 5) for i in range(n)],
    })
    seen = []
    original = standard_engine.cross_validate

    def capture(*args, **kwargs):
        if not seen:
            seen.extend(kwargs["cv"])
        return original(*args, **kwargs)

    monkeypatch.setattr(standard_engine, "cross_validate", capture)
    output = run_standard(
        records, "target", "regression", split_policy="time",
        time_column="event_date", cv=3,
    )
    assert output["cv_splits"] == 3
    assert seen
    times = pd.to_datetime(records["event_date"]).iloc[
        output["train_original_indices"]
    ].reset_index(drop=True)
    for train_indices, validation_indices in seen:
        assert times.iloc[train_indices].max() < times.iloc[validation_indices].min()
    assert any("동일 시각" in message for message in output["warnings"])
    assert max(times) < pd.to_datetime(records["event_date"]).iloc[
        output["holdout_original_indices"]
    ].min()
