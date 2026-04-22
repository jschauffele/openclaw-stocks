from __future__ import annotations

from typing import Sequence


DEFAULT_MIN_BUY_PERCENT_CHANGE_PCT = 0.25


def generate_signal_from_closes(
    closes: Sequence[float],
    min_buy_percent_change_pct: float = DEFAULT_MIN_BUY_PERCENT_CHANGE_PCT,
) -> dict:
    if len(closes) < 2:
        raise ValueError("Need at least 2 closing prices to generate a signal")

    min_buy_percent_change_pct = float(min_buy_percent_change_pct)
    if min_buy_percent_change_pct < 0:
        raise ValueError("min_buy_percent_change_pct must be >= 0")

    previous_close = float(closes[-2])
    latest_close = float(closes[-1])
    price_delta = latest_close - previous_close
    percent_change = (price_delta / previous_close) * 100 if previous_close else 0.0

    if percent_change >= min_buy_percent_change_pct:
        signal = "buy"
        decision = "buy"
        reason = "percent_change_meets_buy_threshold"
    elif latest_close > previous_close:
        signal = "hold"
        decision = "hold"
        reason = "percent_change_below_buy_threshold"
    else:
        signal = "hold"
        decision = "hold"
        reason = "latest_close_not_above_previous_close"

    return {
        "signal": signal,
        "decision": decision,
        "reason": reason,
        "previous_close": previous_close,
        "latest_close": latest_close,
        "price_delta": price_delta,
        "percent_change": percent_change,
        "min_buy_percent_change_pct": min_buy_percent_change_pct,
    }
