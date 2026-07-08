import pandas as pd

from mstr_bot import indicators


def _ohlcv_frame(rows: int = 60) -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-01", periods=rows)
    closes = pd.Series([100.0 + index + ((index % 3) * 0.25) for index in range(rows)])
    return pd.DataFrame(
        {
            "date": dates,
            "open": closes + 0.1,
            "high": closes + 1.0,
            "low": closes - 1.0,
            "close": closes,
            "adj_close": closes,
            "volume": [1_000_000 + index * 1000 for index in range(rows)],
        }
    )


def test_indicators_are_deterministic_for_identical_input() -> None:
    frame = _ohlcv_frame()

    first = pd.DataFrame(
        {
            "rsi": indicators.rsi(frame["close"]),
            "atr": indicators.atr(frame["high"], frame["low"], frame["close"]),
            "obv": indicators.obv(frame["close"], frame["volume"]),
            "volume_spike": indicators.volume_spike(frame["volume"]),
            "sma": indicators.sma(frame["close"], 20),
            "ema": indicators.ema(frame["close"], 20),
            "vwap_proxy": indicators.vwap_proxy(frame["high"], frame["low"], frame["close"], frame["volume"], 20),
        }
    )
    second = pd.DataFrame(
        {
            "rsi": indicators.rsi(frame["close"]),
            "atr": indicators.atr(frame["high"], frame["low"], frame["close"]),
            "obv": indicators.obv(frame["close"], frame["volume"]),
            "volume_spike": indicators.volume_spike(frame["volume"]),
            "sma": indicators.sma(frame["close"], 20),
            "ema": indicators.ema(frame["close"], 20),
            "vwap_proxy": indicators.vwap_proxy(frame["high"], frame["low"], frame["close"], frame["volume"], 20),
        }
    )

    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(indicators.macd(frame["close"]), indicators.macd(frame["close"]))
    pd.testing.assert_frame_equal(indicators.bollinger(frame["close"]), indicators.bollinger(frame["close"]))


def test_indicator_no_lookahead_future_mutation_and_removal_canary() -> None:
    frame = _ohlcv_frame(80)
    decision_index = 40
    baseline = indicators.rsi(frame["close"]).iloc[decision_index]

    mutated = frame.copy()
    mutated.loc[decision_index + 1 :, "close"] = 9999.0
    removed = frame.iloc[: decision_index + 1].copy()

    assert indicators.rsi(mutated["close"]).iloc[decision_index] == baseline
    assert indicators.rsi(removed["close"]).iloc[decision_index] == baseline
