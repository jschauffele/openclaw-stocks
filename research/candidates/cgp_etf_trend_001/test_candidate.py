from __future__ import annotations

from datetime import date, timedelta

from model import ASSET_CLASS, UNIVERSE, Bar, compute_target_weights
from simulation import run_backtest


def synthetic_bars(days: int = 900, rising: bool = True) -> dict[str, list[Bar]]:
    start = date(2007, 1, 2)
    result: dict[str, list[Bar]] = {}
    for symbol_idx, symbol in enumerate(UNIVERSE):
        price = 50.0 + symbol_idx
        current = start
        bars: list[Bar] = []
        while len(bars) < days:
            if current.weekday() < 5:
                drift = (0.0007 + symbol_idx * 0.00001) * (1 if rising else -1)
                open_price = price
                close_price = price * (1.0 + drift)
                bars.append(
                    Bar(
                        trading_date=current,
                        open=open_price,
                        high=max(open_price, close_price) * 1.001,
                        low=min(open_price, close_price) * 0.999,
                        close=close_price,
                        volume=1_000_000.0,
                    )
                )
                price = close_price
            current += timedelta(days=1)
        result[symbol] = bars
    return result


def test_rising_history_generates_bounded_weights() -> None:
    bars = synthetic_bars()
    histories = {s: [bar.close for bar in bars[s]][:500] for s in UNIVERSE}
    weights, votes = compute_target_weights(histories)
    assert all(votes[s] == 3 for s in UNIVERSE)
    assert 0.0 < sum(weights.values()) <= 1.0
    assert max(weights.values()) <= 0.15 + 1e-12
    for group in set(ASSET_CLASS.values()):
        assert sum(weights[s] for s in UNIVERSE if ASSET_CLASS[s] == group) <= 0.35 + 1e-12


def test_falling_history_goes_to_cash() -> None:
    bars = synthetic_bars(rising=False)
    histories = {s: [bar.close for bar in bars[s]][:500] for s in UNIVERSE}
    weights, votes = compute_target_weights(histories)
    assert all(votes[s] == 0 for s in UNIVERSE)
    assert sum(weights.values()) == 0.0


def test_backtest_is_deterministic_and_costs_reduce_value() -> None:
    bars = synthetic_bars()
    start = date(2010, 1, 4)
    no_cost = run_backtest(bars, start=start, cost_bps=0.0)
    with_cost = run_backtest(bars, start=start, cost_bps=10.0)
    assert with_cost["daily"][-1]["portfolio_value"] < no_cost["daily"][-1]["portfolio_value"]
    assert run_backtest(bars, start=start, cost_bps=10.0) == with_cost
