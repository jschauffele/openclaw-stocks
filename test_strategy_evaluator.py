from __future__ import annotations

import sys

import pytest

from strategy_engine import generate_signal_from_closes
from strategy_evaluator import (
    StrategyEvaluationInput,
    evaluate_selected_strategy_signal,
)


def teardown_module(_module) -> None:
    sys.modules.pop("strategy_engine", None)
    sys.modules.pop("strategy_evaluator", None)


def test_selected_close_momentum_delegates_to_close_momentum_signal() -> None:
    closes = (100.0, 100.5, 101.0)

    result = evaluate_selected_strategy_signal(
        StrategyEvaluationInput(
            closes=closes,
            selected_strategy_id="close_momentum_v1",
        )
    )

    assert result.signal_result == generate_signal_from_closes(closes)


def test_no_selected_strategy_returns_deterministic_hold_signal() -> None:
    result = evaluate_selected_strategy_signal(
        StrategyEvaluationInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            selected_strategy_id=None,
        )
    )

    assert result.signal_result.keys() == {
        "signal",
        "decision",
        "reason",
        "previous_close",
        "latest_close",
        "price_delta",
        "percent_change",
        "three_close_percent_change",
    }
    assert result.signal_result == {
        "signal": "hold",
        "decision": "hold",
        "reason": "strategy_routing_no_selected_strategy",
        "previous_close": 100.8,
        "latest_close": 101.2,
        "price_delta": pytest.approx(0.4),
        "percent_change": pytest.approx(0.396825396825),
        "three_close_percent_change": pytest.approx(0.796812749004),
    }


def test_unknown_selected_strategy_id_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown selected_strategy_id"):
        evaluate_selected_strategy_signal(
            StrategyEvaluationInput(
                closes=(100.0, 100.5, 101.0),
                selected_strategy_id="unknown_strategy",
            )
        )
