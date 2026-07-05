from __future__ import annotations

from typing import Sequence


MIN_CLOSES_REQUIRED = 5
MIN_POSITIVE_MOVES_REQUIRED = 3
MIN_FIVE_CLOSE_PERCENT_CHANGE = 1.0


def generate_equity_momentum_continuation_signal_from_closes(
    closes: Sequence[float],
) -> dict:
    close_values = tuple(float(close) for close in closes)
    previous_close, latest_close, price_delta, percent_change = _latest_change(
        close_values
    )
    three_close_percent_change = _three_close_percent_change(close_values)

    signal = "hold"
    reason = "insufficient_data_for_equity_momentum_continuation"

    if len(close_values) >= MIN_CLOSES_REQUIRED:
        recent_closes = close_values[-MIN_CLOSES_REQUIRED:]
        recent_moves = tuple(
            current_close - prior_close
            for prior_close, current_close in zip(recent_closes, recent_closes[1:])
        )
        positive_move_count = sum(1 for move in recent_moves if move > 0)
        five_close_percent_change = (
            ((recent_closes[-1] - recent_closes[0]) / recent_closes[0]) * 100
            if recent_closes[0]
            else 0.0
        )

        if latest_close <= previous_close:
            reason = "latest_close_not_above_previous_close"
        elif positive_move_count < MIN_POSITIVE_MOVES_REQUIRED:
            reason = "positive_move_count_below_threshold"
        elif five_close_percent_change < MIN_FIVE_CLOSE_PERCENT_CHANGE:
            reason = "five_close_percent_change_below_threshold"
        else:
            signal = "buy"
            reason = "equity_momentum_continuation_conditions_met"

    return {
        "signal": signal,
        "decision": signal,
        "reason": reason,
        "previous_close": previous_close,
        "latest_close": latest_close,
        "price_delta": price_delta,
        "percent_change": percent_change,
        "three_close_percent_change": three_close_percent_change,
    }


def _latest_change(close_values: tuple[float, ...]) -> tuple[float, float, float, float]:
    latest_close = close_values[-1] if close_values else 0.0
    previous_close = close_values[-2] if len(close_values) >= 2 else latest_close
    price_delta = latest_close - previous_close
    percent_change = (price_delta / previous_close) * 100 if previous_close else 0.0
    return previous_close, latest_close, price_delta, percent_change


def _three_close_percent_change(close_values: tuple[float, ...]) -> float:
    if len(close_values) < 3:
        return 0.0

    prior_close = close_values[-3]
    latest_close = close_values[-1]
    return ((latest_close - prior_close) / prior_close) * 100 if prior_close else 0.0
