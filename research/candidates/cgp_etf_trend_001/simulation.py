from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Mapping, Sequence

from model import (
    CANDIDATE_ID,
    DEFAULT_COST_BPS,
    DEFAULT_START,
    PRIMARY_LOOKBACKS,
    UNIVERSE,
    VOL_LOOKBACK,
    Bar,
    RebalanceRecord,
    compute_target_weights,
    safe_float,
    validate_bars,
)


def month_end_indices(dates: Sequence[date]) -> list[int]:
    return [
        i for i, d in enumerate(dates)
        if i == len(dates) - 1 or dates[i + 1].month != d.month
    ]


def _lookup(bars_by_symbol: Mapping[str, Sequence[Bar]]) -> dict[str, dict[date, Bar]]:
    return {
        symbol: {bar.trading_date: bar for bar in bars_by_symbol[symbol]}
        for symbol in UNIVERSE
    }


def _portfolio_value(
    shares: Mapping[str, float], cash: float, prices: Mapping[str, float]
) -> tuple[float, dict[str, float]]:
    values = {symbol: shares[symbol] * prices[symbol] for symbol in UNIVERSE}
    total = cash + sum(values.values())
    if total <= 0:
        raise ValueError("portfolio value is non-positive")
    return total, {symbol: values[symbol] / total for symbol in UNIVERSE}


def run_backtest(
    bars_by_symbol: Mapping[str, Sequence[Bar]],
    start: date = DEFAULT_START,
    end: date | None = None,
    cost_bps: float = DEFAULT_COST_BPS,
    execution_delay_days: int = 1,
    lookbacks: Sequence[int] = PRIMARY_LOOKBACKS,
) -> dict:
    if execution_delay_days < 1:
        raise ValueError("execution_delay_days must be >= 1")
    cost_rate = safe_float(cost_bps, "cost_bps") / 10_000.0
    if cost_rate < 0:
        raise ValueError("cost_bps must be non-negative")

    common_dates = validate_bars(bars_by_symbol, start)
    end = end or common_dates[-1]
    dates = [d for d in common_dates if d <= end]
    index_by_date = {d: i for i, d in enumerate(dates)}
    lookup = _lookup(bars_by_symbol)

    execution_plan: dict[date, date] = {}
    for signal_idx in month_end_indices(dates):
        execution_idx = signal_idx + execution_delay_days
        if execution_idx < len(dates):
            execution_plan[dates[execution_idx]] = dates[signal_idx]

    shares = {symbol: 0.0 for symbol in UNIVERSE}
    cash = 1.0
    previous_value = 1.0
    active = False
    daily_rows: list[dict] = []
    rebalances: list[RebalanceRecord] = []

    for current_date in dates:
        prices = {symbol: lookup[symbol][current_date].open for symbol in UNIVERSE}
        value_before_trade, current_weights = _portfolio_value(shares, cash, prices)
        turnover = 0.0
        cost_fraction = 0.0

        if current_date in execution_plan:
            signal_date = execution_plan[current_date]
            signal_idx = index_by_date[signal_date]
            if signal_idx >= max(max(lookbacks), VOL_LOOKBACK):
                histories = {
                    symbol: [lookup[symbol][d].close for d in dates[: signal_idx + 1]]
                    for symbol in UNIVERSE
                }
                target, votes = compute_target_weights(histories, lookbacks, VOL_LOOKBACK)
                turnover = sum(abs(target[s] - current_weights[s]) for s in UNIVERSE)
                trading_cost = value_before_trade * turnover * cost_rate
                if trading_cost >= value_before_trade:
                    raise ValueError("trading costs exhausted portfolio")
                value_after_cost = value_before_trade - trading_cost
                shares = {s: value_after_cost * target[s] / prices[s] for s in UNIVERSE}
                gross = sum(target.values())
                cash = value_after_cost * (1.0 - gross)
                value_before_trade = value_after_cost
                cost_fraction = trading_cost / (value_after_cost + trading_cost) if trading_cost else 0.0
                active = True
                rebalances.append(
                    RebalanceRecord(
                        signal_date=signal_date.isoformat(),
                        execution_date=current_date.isoformat(),
                        turnover=turnover,
                        cost_fraction=cost_fraction,
                        gross_target=gross,
                        cash_target=1.0 - gross,
                        positive_assets=sum(v >= 2 for v in votes.values()),
                        weights=target,
                        signal_votes=votes,
                    )
                )

        if current_date < start or not active:
            previous_value = value_before_trade
            continue

        daily_return = value_before_trade / previous_value - 1.0
        portfolio_value, end_weights = _portfolio_value(shares, cash, prices)
        daily_rows.append(
            {
                "date": current_date.isoformat(),
                "portfolio_value": portfolio_value,
                "daily_return": daily_return,
                "turnover": turnover,
                "cost_fraction": cost_fraction,
                "gross_exposure": sum(end_weights.values()),
            }
        )
        previous_value = portfolio_value

    if not daily_rows:
        raise ValueError("backtest produced no observations")

    return {
        "candidate_id": CANDIDATE_ID,
        "parameters": {
            "universe": list(UNIVERSE),
            "lookbacks": list(lookbacks),
            "vol_lookback": VOL_LOOKBACK,
            "cost_bps": cost_bps,
            "execution_delay_days": execution_delay_days,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "daily": daily_rows,
        "rebalances": [asdict(record) for record in rebalances],
    }
