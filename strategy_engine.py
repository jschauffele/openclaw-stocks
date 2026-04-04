from __future__ import annotations

from typing import Sequence


def generate_signal_from_closes(closes: Sequence[float]) -> dict:
    if len(closes) < 2:
        raise ValueError("Need at least 2 closing prices to generate a signal")

    previous_close = float(closes[-2])
    latest_close = float(closes[-1])
    price_delta = latest_close - previous_close
    percent_change = (price_delta / previous_close) * 100 if previous_close else 0.0

    if latest_close > previous_close:
        signal = "buy"
        decision = "buy"
        reason = "latest_close_above_previous_close"
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
    }
