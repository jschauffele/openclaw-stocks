import pytest
import pandas as pd

from mstr_bot.runner import run_signal_rule


def _toy_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-01", periods=12)
    closes = [100.0 + index for index in range(len(dates))]
    return pd.DataFrame(
        {
            "date": dates,
            "open": closes,
            "high": [value + 1.0 for value in closes],
            "low": [value - 1.0 for value in closes],
            "close": closes,
            "adj_close": closes,
            "volume": [1_000_000 for _ in closes],
        }
    )


def test_runner_known_toy_rule_produces_hand_computed_trade_log() -> None:
    result = run_signal_rule(
        _toy_frame(),
        {
            "entry": "close == 103",
            "exit": "bars_held >= 2",
        },
    )

    assert result["trades"] == [
        {
            "entry_signal_date": "2026-01-06",
            "entry_date": "2026-01-07",
            "entry_price": 104.0,
            "direction": "long",
            "exit_signal_date": "2026-01-08",
            "exit_date": "2026-01-09",
            "exit_price": 106.0,
            "bars_held": 2,
            "return": pytest.approx((106.0 / 104.0) - 1.0),
        }
    ]
    assert result["summary"]["trade_count"] == 1
    assert result["summary"]["win_rate"] == 1.0


def test_runner_entry_fill_at_next_open_not_same_bar() -> None:
    result = run_signal_rule(
        _toy_frame(),
        {
            "entry": "close == 103",
            "exit": "bars_held >= 1",
        },
    )

    trade = result["trades"][0]
    assert trade["entry_signal_date"] == "2026-01-06"
    assert trade["entry_date"] == "2026-01-07"
    assert trade["entry_price"] == 104.0
    assert trade["entry_price"] != 103.0


def test_runner_short_direction_profits_on_falling_toy_series() -> None:
    dates = pd.bdate_range("2026-01-01", periods=8)
    closes = [100.0 - index for index in range(len(dates))]
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": closes,
            "high": [value + 1.0 for value in closes],
            "low": [value - 1.0 for value in closes],
            "close": closes,
            "adj_close": closes,
            "volume": [1_000_000 for _ in closes],
        }
    )

    result = run_signal_rule(
        frame,
        {
            "direction": "short",
            "entry": "close == 97",
            "exit": "bars_held >= 2",
        },
    )

    assert result["trades"] == [
        {
            "entry_signal_date": "2026-01-06",
            "entry_date": "2026-01-07",
            "entry_price": 96.0,
            "direction": "short",
            "exit_signal_date": "2026-01-08",
            "exit_date": "2026-01-09",
            "exit_price": 94.0,
            "bars_held": 2,
            "return": pytest.approx((96.0 / 94.0) - 1.0),
        }
    ]
    assert result["summary"]["win_rate"] == 1.0
