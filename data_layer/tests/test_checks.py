import pandas as pd

from data_layer.checks import check_dividends, check_split_continuity, reconcile_vendor_adjclose
from data_layer.adjustments import reconstruct_adj_close


def test_reconcile_passes_with_synthetic_vendor_adjusted_close():
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2024-01-01", periods=8),
            "close": [100.0, 102.0, 51.0, 51.5, 52.0, 51.5, 52.5, 53.0],
            "splitFactor": [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "divCash": [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        }
    )
    df["adjClose"] = reconstruct_adj_close(df)
    result = reconcile_vendor_adjclose(df)
    assert result.passed
    assert result.metrics["rows_within_0_5pct"] == 100.0


def test_split_continuity_25pct_escalation():
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2024-01-01", periods=3),
            "close": [100.0, 50.0, 51.0],
            "adjClose": [100.0, 140.0, 141.0],
            "splitFactor": [1.0, 2.0, 1.0],
            "divCash": [0.0, 0.0, 0.0],
        }
    )
    result = check_split_continuity(df)
    assert result.passed
    assert result.messages == ["large_split_date_move_observed"]


def test_dividend_over_10pct_flags_review():
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2024-01-01", periods=2),
            "close": [100.0, 50.0],
            "divCash": [0.0, 6.0],
        }
    )
    result = check_dividends(df)
    assert result.passed
    assert result.messages == ["large_dividend_event_observed"]
    assert result.metrics["flagged_events"][0]["implied_yield"] == 0.12
