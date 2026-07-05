from __future__ import annotations

import pytest

from equity_momentum_continuation_strategy import (
    generate_equity_momentum_continuation_signal_from_closes,
)


EXPECTED_SIGNAL_KEYS = {
    "signal",
    "decision",
    "reason",
    "previous_close",
    "latest_close",
    "price_delta",
    "percent_change",
    "three_close_percent_change",
}


def test_candidate_returns_hold_with_fewer_than_five_closes() -> None:
    result = generate_equity_momentum_continuation_signal_from_closes(
        (100.0, 100.5, 101.0, 101.5)
    )

    assert set(result) == EXPECTED_SIGNAL_KEYS
    assert result["signal"] == "hold"
    assert result["decision"] == "hold"
    assert result["reason"] == "insufficient_data_for_equity_momentum_continuation"


def test_candidate_returns_buy_when_continuation_conditions_pass() -> None:
    result = generate_equity_momentum_continuation_signal_from_closes(
        (100.0, 100.5, 100.2, 101.0, 101.2)
    )

    assert set(result) == EXPECTED_SIGNAL_KEYS
    assert result == {
        "signal": "buy",
        "decision": "buy",
        "reason": "equity_momentum_continuation_conditions_met",
        "previous_close": 101.0,
        "latest_close": 101.2,
        "price_delta": pytest.approx(0.2),
        "percent_change": pytest.approx(0.19801980198),
        "three_close_percent_change": pytest.approx(0.998003992016),
    }


def test_candidate_returns_hold_when_fewer_than_three_recent_moves_are_positive() -> None:
    result = generate_equity_momentum_continuation_signal_from_closes(
        (100.0, 101.0, 100.5, 100.4, 101.2)
    )

    assert set(result) == EXPECTED_SIGNAL_KEYS
    assert result["signal"] == "hold"
    assert result["decision"] == "hold"
    assert result["reason"] == "positive_move_count_below_threshold"


def test_candidate_returns_hold_when_five_close_percent_change_is_below_threshold() -> None:
    result = generate_equity_momentum_continuation_signal_from_closes(
        (100.0, 100.3, 100.1, 100.5, 100.8)
    )

    assert set(result) == EXPECTED_SIGNAL_KEYS
    assert result["signal"] == "hold"
    assert result["decision"] == "hold"
    assert result["reason"] == "five_close_percent_change_below_threshold"


def test_candidate_never_returns_sell() -> None:
    close_sequences = (
        (),
        (100.0,),
        (100.0, 99.0),
        (100.0, 100.5, 101.0, 101.5),
        (100.0, 101.0, 100.5, 100.4, 101.2),
        (100.0, 100.3, 100.1, 100.5, 100.8),
        (100.0, 100.5, 100.2, 101.0, 101.2),
        (100.0, 101.0, 102.0, 103.0, 99.0),
    )

    for closes in close_sequences:
        result = generate_equity_momentum_continuation_signal_from_closes(closes)

        assert set(result) == EXPECTED_SIGNAL_KEYS
        assert result["signal"] != "sell"
        assert result["decision"] != "sell"
