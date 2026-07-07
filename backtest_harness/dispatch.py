"""No-lookahead signal dispatch for Phase 1B."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pandas as pd

from backtest_harness.failures import BacktestHarnessError, HarnessFailureCode


ALLOWED_SIGNALS = frozenset({"buy", "hold"})


def replay_signal_dispatch(
    derived_frame: pd.DataFrame,
    *,
    decision_dates: tuple[object, ...],
    strategy: Callable[[tuple[float, ...]], Mapping[str, Any]],
    evaluator_id: str,
) -> tuple[dict[str, Any], ...]:
    if not callable(strategy):
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SIGNAL, "strategy must be callable")
    if not str(evaluator_id).strip():
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SIGNAL, "evaluator_id must be non-empty")
    required = {"date", "ticker", "computed_adjClose"}
    missing = sorted(required.difference(derived_frame.columns))
    if missing:
        raise BacktestHarnessError(HarnessFailureCode.SCHEMA_MISMATCH, f"missing dispatch columns: {missing}")

    frame = derived_frame.loc[:, ["date", "ticker", "computed_adjClose"]].copy(deep=True)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.normalize()
    if frame["date"].isna().any():
        raise BacktestHarnessError(HarnessFailureCode.UNPARSEABLE_DATE, "dispatch frame contains unparseable date")
    frame["ticker"] = frame["ticker"].astype(str).str.strip().str.upper()
    frame["computed_adjClose"] = pd.to_numeric(frame["computed_adjClose"], errors="coerce")
    if frame["computed_adjClose"].isna().any():
        raise BacktestHarnessError(HarnessFailureCode.INVALID_PRICE, "dispatch frame contains invalid close")
    frame = frame.sort_values(["ticker", "date"], kind="mergesort").reset_index(drop=True)
    dates = tuple(pd.Timestamp(date).normalize() for date in pd.to_datetime(list(decision_dates), errors="coerce"))
    if any(pd.isna(date) for date in dates):
        raise BacktestHarnessError(HarnessFailureCode.UNPARSEABLE_DATE, "decision_dates contains unparseable date")

    records: list[dict[str, Any]] = []
    for ticker in sorted(frame["ticker"].unique()):
        ticker_frame = frame[frame["ticker"] == ticker].copy(deep=True)
        for decision_date in dates:
            visible = ticker_frame[ticker_frame["date"] <= decision_date].copy(deep=True)
            if visible.empty:
                continue
            inputs_end_date = visible["date"].max()
            if inputs_end_date > decision_date:
                raise BacktestHarnessError(HarnessFailureCode.LOOKAHEAD_DETECTED, "visible input extends past decision date")
            closes = tuple(float(value) for value in visible["computed_adjClose"].tolist())
            signal_result = strategy(closes)
            signal = _validate_signal(signal_result)
            records.append(
                {
                    "date": decision_date.date().isoformat(),
                    "ticker": ticker,
                    "signal": signal,
                    "inputs_end_date": inputs_end_date.date().isoformat(),
                    "evaluator_id": str(evaluator_id),
                }
            )
    return tuple(records)


def _validate_signal(signal_result: Mapping[str, Any]) -> str:
    if not isinstance(signal_result, Mapping):
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SIGNAL, "strategy must return a mapping")
    signal = str(signal_result.get("signal", "")).strip().lower()
    if signal not in ALLOWED_SIGNALS:
        raise BacktestHarnessError(HarnessFailureCode.INVALID_SIGNAL, f"invalid signal: {signal}")
    return signal
