from __future__ import annotations

from typing import Sequence


DEFAULT_MIN_BUY_PERCENT_CHANGE_PCT = 0.25


def generate_signal_from_closes(
    closes: Sequence[float],
    min_buy_percent_change_pct: float = DEFAULT_MIN_BUY_PERCENT_CHANGE_PCT,
) -> dict:
    min_buy_percent_change_pct = float(min_buy_percent_change_pct)
    if min_buy_percent_change_pct < 0:
        raise ValueError("min_buy_percent_change_pct must be >= 0")

    close_values = [float(close) for close in closes]
    if len(close_values) < 3:
        latest_close = close_values[-1] if close_values else 0.0
        previous_close = close_values[-2] if len(close_values) >= 2 else latest_close
        price_delta = latest_close - previous_close
        percent_change = (price_delta / previous_close) * 100 if previous_close else 0.0
        return {
            "signal": "hold",
            "decision": "hold",
            "reason": "insufficient_data_for_confirmation",
            "previous_close": previous_close,
            "latest_close": latest_close,
            "price_delta": price_delta,
            "percent_change": percent_change,
            "three_close_percent_change": 0.0,
            "min_buy_percent_change_pct": min_buy_percent_change_pct,
        }

    prior_close = close_values[-3]
    previous_close = close_values[-2]
    latest_close = close_values[-1]
    price_delta = latest_close - previous_close
    percent_change = (price_delta / previous_close) * 100 if previous_close else 0.0
    three_close_price_delta = latest_close - prior_close
    three_close_percent_change = (
        (three_close_price_delta / prior_close) * 100 if prior_close else 0.0
    )

    if percent_change <= -0.5:
        signal = "sell"
        decision = "sell"
        reason = "percent_change_meets_sell_threshold"
    elif not (prior_close < previous_close < latest_close):
        signal = "hold"
        decision = "hold"
        reason = "three_close_confirmation_failed"
    elif (
        percent_change >= min_buy_percent_change_pct
        and three_close_percent_change >= 1.0
    ):
        signal = "buy"
        decision = "buy"
        reason = "percent_change_meets_buy_threshold"
    else:
        signal = "hold"
        decision = "hold"
        reason = "percent_change_below_buy_threshold"

    result = {
        "signal": signal,
        "decision": decision,
        "reason": reason,
        "previous_close": previous_close,
        "latest_close": latest_close,
        "price_delta": price_delta,
        "percent_change": percent_change,
        "three_close_percent_change": three_close_percent_change,
        "min_buy_percent_change_pct": min_buy_percent_change_pct,
    }

    if decision == "sell":
        result["action"] = "SELL"

    return result
