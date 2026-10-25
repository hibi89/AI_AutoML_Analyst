"""P6 sale-chart policy: prefer informative date trends and avoid filler."""
import pandas as pd

from backend.app.services.basic_report import _quality_rows
from backend.app.services.chart_design import create_charts


def make_data(with_date: bool) -> pd.DataFrame:
    n = 150
    data = pd.DataFrame({
        "revenue": [i % 17 * 3.0 + (i % 4) for i in range(n)],
        "expenses": [10.0 + (i % 17) * 2 for i in range(n)],
        "segment": ["private-A", "private-B", "private-C"] * 50,
    })
    data.loc[0:20, "segment"] = None
    if with_date:
        data["date"] = pd.date_range("2026-01-01", periods=n).strftime("%Y-%m-%d")
    return data


def test_valid_calendar_prioritizes_trend_not_redundant_box():
    df = make_data(True)
    plots = create_charts(df, _quality_rows(df))
    names = [a for a, _, _ in plots]
    assert len(plots) == 5
    assert any(name.endswith("_trend.png") for name in names)
    assert not any(name.endswith("_box.png") for name in names)
    assert all(raw.startswith(b"\\x89PNG".decode("unicode_escape").encode("latin1"))
               for _, raw, _ in plots)


def test_without_date_box_is_valid_fifth_chart():
    df = make_data(False)
    plots = create_charts(df, _quality_rows(df))
    assert len(plots) == 5
    assert any(name.endswith("_box.png") for name, _, _ in plots)


def test_sparse_data_avoids_unjustified_graphs():
    df = pd.DataFrame({"category": ["A", "B", "C"],
                       "other": ["same", "same", "same"]})
    assert create_charts(df, _quality_rows(df)) == []



def test_overlong_or_control_character_headers_rejected_before_render():
    import pytest
    from backend.app.services.basic_report import validate_basic_frame

    with pytest.raises(ValueError, match="at most 160"):
        validate_basic_frame(pd.DataFrame({"가" * 161: [1, 2, 3]}))
    with pytest.raises(ValueError, match="control characters"):
        validate_basic_frame(pd.DataFrame({"name\ninvalid": [1, 2, 3]}))
