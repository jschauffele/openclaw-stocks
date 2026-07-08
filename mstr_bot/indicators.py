"""Pure close-through-time technical indicators for the research MSTR bot."""

from __future__ import annotations

import pandas as pd


def sma(closes: pd.Series, n: int) -> pd.Series:
    return _series(closes).rolling(window=n, min_periods=n).mean()


def ema(closes: pd.Series, n: int) -> pd.Series:
    return _series(closes).ewm(span=n, adjust=False, min_periods=n).mean()


def rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    close = _series(closes)
    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    avg_gain = _wilder_average(gains, period)
    avg_loss = _wilder_average(losses, period)
    rs = avg_gain / avg_loss
    result = 100.0 - (100.0 / (1.0 + rs))
    result = result.mask(avg_loss == 0.0, 100.0)
    return result.rename("rsi")


def macd(closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    close = _series(closes)
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": histogram,
        },
        index=close.index,
    )


def bollinger(closes: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    close = _series(closes)
    middle = sma(close, window)
    std = close.rolling(window=window, min_periods=window).std()
    return pd.DataFrame(
        {
            "bollinger_lower": middle - num_std * std,
            "bollinger_middle": middle,
            "bollinger_upper": middle + num_std * std,
        },
        index=close.index,
    )


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    high_series = _series(high)
    low_series = _series(low)
    close_series = _series(close)
    previous_close = close_series.shift(1)
    true_range = pd.concat(
        [
            high_series - low_series,
            (high_series - previous_close).abs(),
            (low_series - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return _wilder_average(true_range, period).rename("atr")


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    close_series = _series(close)
    volume_series = _series(volume)
    direction = close_series.diff().apply(lambda value: 1 if value > 0 else (-1 if value < 0 else 0))
    signed_volume = direction.fillna(0) * volume_series
    return signed_volume.cumsum().rename("obv")


def volume_spike(volume: pd.Series, window: int = 20, mult: float = 2.0) -> pd.Series:
    volume_series = _series(volume)
    trailing_average = volume_series.shift(1).rolling(window=window, min_periods=window).mean()
    return (volume_series > mult * trailing_average).fillna(False).rename("volume_spike")


def vwap_proxy(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    window: int,
) -> pd.Series:
    """Daily-bar proxy, not true intraday VWAP."""

    typical_price = (_series(high) + _series(low) + _series(close)) / 3.0
    volume_series = _series(volume)
    numerator = (typical_price * volume_series).rolling(window=window, min_periods=window).sum()
    denominator = volume_series.rolling(window=window, min_periods=window).sum()
    return (numerator / denominator).rename("vwap_proxy")


def _series(values: pd.Series) -> pd.Series:
    return pd.Series(values, copy=True).astype(float)


def _wilder_average(values: pd.Series, period: int) -> pd.Series:
    series = _series(values)
    result = pd.Series(index=series.index, dtype="float64")
    if len(series) <= period:
        return result
    initial = series.iloc[1 : period + 1].mean()
    result.iloc[period] = initial
    previous = initial
    for index in range(period + 1, len(series)):
        previous = ((previous * (period - 1)) + series.iloc[index]) / period
        result.iloc[index] = previous
    return result
