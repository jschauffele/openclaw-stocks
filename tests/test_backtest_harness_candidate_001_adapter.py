from equity_momentum_continuation_strategy import (
    MIN_CLOSES_REQUIRED,
    MIN_FIVE_CLOSE_PERCENT_CHANGE,
    MIN_POSITIVE_MOVES_REQUIRED,
)

from backtest_harness.candidate_001_adapter import candidate_001_replay_adapter


def test_candidate_001_adapter_returns_buy_for_engineered_continuation() -> None:
    start = 100.0
    required_end = start * (1.0 + MIN_FIVE_CLOSE_PERCENT_CHANGE / 100.0)
    positive_step = (required_end - start) / MIN_POSITIVE_MOVES_REQUIRED
    positive_levels = [start + positive_step * index for index in range(MIN_POSITIVE_MOVES_REQUIRED)]
    closes = tuple(
        [*positive_levels, positive_levels[-1], required_end][-MIN_CLOSES_REQUIRED:]
    )

    result = candidate_001_replay_adapter(closes)

    assert result["signal"] == "buy"


def test_candidate_001_adapter_returns_hold_for_flat_closes() -> None:
    closes = tuple(100.0 for _ in range(MIN_CLOSES_REQUIRED))

    result = candidate_001_replay_adapter(closes)

    assert result["signal"] == "hold"


def test_candidate_001_adapter_uses_strategy_short_input_hold_behavior() -> None:
    closes = tuple(100.0 + index for index in range(MIN_CLOSES_REQUIRED - 1))

    result = candidate_001_replay_adapter(closes)

    assert result["signal"] == "hold"
    assert result["reason"] == "insufficient_data_for_equity_momentum_continuation"
