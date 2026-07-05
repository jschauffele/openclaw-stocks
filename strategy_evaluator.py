from __future__ import annotations

from dataclasses import dataclass

from equity_momentum_continuation_strategy import (
    generate_equity_momentum_continuation_signal_from_closes,
)
from strategy_engine import generate_signal_from_closes


NO_SELECTED_STRATEGY_REASON = "strategy_routing_no_selected_strategy"
CLOSE_MOMENTUM_STRATEGY_ID = "close_momentum_v1"
EQUITY_MOMENTUM_CONTINUATION_STRATEGY_ID = "equity_momentum_continuation_v1"


@dataclass(frozen=True, slots=True)
class StrategyEvaluationInput:
    closes: tuple[float, ...]
    selected_strategy_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.closes, tuple):
            raise ValueError("closes must be a tuple")
        if (
            self.selected_strategy_id is not None
            and not self.selected_strategy_id.strip()
        ):
            raise ValueError("selected_strategy_id must be non-empty when present")


@dataclass(frozen=True, slots=True)
class StrategyEvaluationResult:
    signal_result: dict

    def __post_init__(self) -> None:
        if not isinstance(self.signal_result, dict):
            raise ValueError("signal_result must be a dict")


def evaluate_selected_strategy_signal(
    input_model: StrategyEvaluationInput,
) -> StrategyEvaluationResult:
    if not isinstance(input_model, StrategyEvaluationInput):
        raise ValueError("input_model must be StrategyEvaluationInput")

    if input_model.selected_strategy_id is None:
        return StrategyEvaluationResult(
            signal_result=build_no_selected_strategy_signal(input_model.closes)
        )

    if input_model.selected_strategy_id == CLOSE_MOMENTUM_STRATEGY_ID:
        return StrategyEvaluationResult(
            signal_result=generate_signal_from_closes(input_model.closes)
        )

    if input_model.selected_strategy_id == EQUITY_MOMENTUM_CONTINUATION_STRATEGY_ID:
        return StrategyEvaluationResult(
            signal_result=generate_equity_momentum_continuation_signal_from_closes(
                input_model.closes
            )
        )

    raise ValueError(f"Unknown selected_strategy_id: {input_model.selected_strategy_id}")


def build_no_selected_strategy_signal(closes: tuple[float, ...]) -> dict:
    close_values = tuple(float(close) for close in closes)
    latest_close = close_values[-1] if close_values else 0.0
    previous_close = close_values[-2] if len(close_values) >= 2 else latest_close
    prior_close = close_values[-3] if len(close_values) >= 3 else previous_close
    price_delta = latest_close - previous_close
    percent_change = (price_delta / previous_close) * 100 if previous_close else 0.0
    three_close_price_delta = latest_close - prior_close
    three_close_percent_change = (
        (three_close_price_delta / prior_close) * 100
        if prior_close and len(close_values) >= 3
        else 0.0
    )

    return {
        "signal": "hold",
        "decision": "hold",
        "reason": NO_SELECTED_STRATEGY_REASON,
        "previous_close": previous_close,
        "latest_close": latest_close,
        "price_delta": price_delta,
        "percent_change": percent_change,
        "three_close_percent_change": three_close_percent_change,
    }
