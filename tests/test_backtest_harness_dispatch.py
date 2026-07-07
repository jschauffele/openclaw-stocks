import pandas as pd
import pytest

from backtest_harness.dispatch import replay_signal_dispatch
from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode
from backtest_harness.serialization import stable_sha256


def _frame(extra_future_close: float = 105.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2026-01-01", "2026-01-02", "2026-01-05", "2026-01-06"]
            ),
            "ticker": ["AAPL", "AAPL", "AAPL", "AAPL"],
            "computed_adjClose": [100.0, 101.0, 102.0, extra_future_close],
        }
    )


def test_dispatch_passes_only_closes_through_decision_date() -> None:
    observed_inputs = []

    def strategy(closes: tuple[float, ...]) -> dict:
        observed_inputs.append(closes)
        return {"signal": "buy" if closes[-1] > closes[0] else "hold"}

    records = replay_signal_dispatch(
        _frame(),
        decision_dates=(pd.Timestamp("2026-01-05"),),
        strategy=strategy,
        evaluator_id="toy_strategy",
    )

    assert observed_inputs == [(100.0, 101.0, 102.0)]
    assert records == (
        {
            "date": "2026-01-05",
            "ticker": "AAPL",
            "signal": "buy",
            "inputs_end_date": "2026-01-05",
            "evaluator_id": "toy_strategy",
        },
    )


def test_dispatch_future_row_mutation_does_not_change_prior_signal() -> None:
    def strategy(closes: tuple[float, ...]) -> dict:
        return {"signal": "buy" if closes[-1] == 102.0 else "hold"}

    first = replay_signal_dispatch(
        _frame(extra_future_close=105.0),
        decision_dates=(pd.Timestamp("2026-01-05"),),
        strategy=strategy,
        evaluator_id="toy_strategy",
    )
    second = replay_signal_dispatch(
        _frame(extra_future_close=999.0),
        decision_dates=(pd.Timestamp("2026-01-05"),),
        strategy=strategy,
        evaluator_id="toy_strategy",
    )

    assert first == second


def test_dispatch_future_row_removal_does_not_change_prior_signal() -> None:
    def strategy(closes: tuple[float, ...]) -> dict:
        return {"signal": "buy" if closes == (100.0, 101.0, 102.0) else "hold"}

    full = _frame()
    truncated_future = full[full["date"] <= pd.Timestamp("2026-01-05")]

    assert replay_signal_dispatch(
        full,
        decision_dates=(pd.Timestamp("2026-01-05"),),
        strategy=strategy,
        evaluator_id="toy_strategy",
    ) == replay_signal_dispatch(
        truncated_future,
        decision_dates=(pd.Timestamp("2026-01-05"),),
        strategy=strategy,
        evaluator_id="toy_strategy",
    )


def test_dispatch_uses_copy_not_view() -> None:
    def mutating_strategy(closes: tuple[float, ...]) -> dict:
        assert isinstance(closes, tuple)
        with pytest.raises(TypeError):
            closes[0] = 0.0  # type: ignore[index]
        return {"signal": "hold"}

    records = replay_signal_dispatch(
        _frame(),
        decision_dates=(pd.Timestamp("2026-01-05"),),
        strategy=mutating_strategy,
        evaluator_id="mutating_strategy",
    )

    assert records[0]["signal"] == "hold"


def test_dispatch_rejects_invalid_signal() -> None:
    def bad_strategy(closes: tuple[float, ...]) -> dict:
        return {"signal": "sell"}

    with pytest.raises(BacktestHarnessError) as excinfo:
        replay_signal_dispatch(
            _frame(),
            decision_dates=(pd.Timestamp("2026-01-05"),),
            strategy=bad_strategy,
            evaluator_id="bad_strategy",
        )

    assert excinfo.value.code == HarnessFailureCode.INVALID_SIGNAL


def test_dispatch_rejects_leaky_non_mapping_fixture() -> None:
    def leaky_strategy(closes: tuple[float, ...]) -> list[str]:
        return ["buy"]

    with pytest.raises(BacktestHarnessError) as excinfo:
        replay_signal_dispatch(
            _frame(),
            decision_dates=(pd.Timestamp("2026-01-05"),),
            strategy=leaky_strategy,
            evaluator_id="leaky_strategy",
        )

    assert excinfo.value.code == HarnessFailureCode.INVALID_SIGNAL


def test_dispatch_records_are_deterministically_serializable() -> None:
    def strategy(closes: tuple[float, ...]) -> dict:
        return {"signal": "hold"}

    records = replay_signal_dispatch(
        _frame(),
        decision_dates=(pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-05")),
        strategy=strategy,
        evaluator_id="deterministic_strategy",
    )

    assert stable_sha256(records) == stable_sha256(tuple(records))
