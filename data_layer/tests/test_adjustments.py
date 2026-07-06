import pandas as pd

from data_layer.adjustments import reconstruct_adj_close, selftest


def test_synthetic_split_dividend_selftest_passes():
    ok, report = selftest()
    assert ok
    assert "computed_adjClose" in report.columns


def test_reconstruct_adj_close_matches_reference_case():
    dates = pd.bdate_range("2024-01-01", periods=8)
    df = pd.DataFrame(
        {
            "date": dates,
            "close": [100.0, 102.0, 51.0, 51.5, 52.0, 51.5, 52.5, 53.0],
            "splitFactor": [1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "divCash": [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        }
    )
    calc = reconstruct_adj_close(df)
    dividend_factor = (52.0 - 1.0) / 52.0
    assert abs(calc.iloc[-1] - 53.0) < 1e-9
    assert abs(calc.iloc[1] - (102.0 * dividend_factor / 2.0)) < 1e-9
    assert abs(calc.iloc[4] - (52.0 * dividend_factor)) < 1e-9

