from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence

CANDIDATE_ID = "CGP-ETF-TREND-001"
UNIVERSE = (
    "SPY", "QQQ", "IWM", "EFA", "EEM", "VNQ",
    "SHY", "IEF", "TLT", "LQD", "HYG",
    "GLD", "DBC", "UUP",
)
ASSET_CLASS = {
    "SPY": "equity", "QQQ": "equity", "IWM": "equity",
    "EFA": "equity", "EEM": "equity", "VNQ": "real_estate",
    "SHY": "rates", "IEF": "rates", "TLT": "rates",
    "LQD": "credit", "HYG": "credit",
    "GLD": "commodity", "DBC": "commodity", "UUP": "currency",
}
PRIMARY_LOOKBACKS = (63, 126, 252)
VOL_LOOKBACK = 63
MIN_HISTORY = max(PRIMARY_LOOKBACKS) + 5
SINGLE_ASSET_CAP = 0.15
ASSET_CLASS_CAP = 0.35
VOL_FLOOR = 0.05
DEFAULT_COST_BPS = 5.0
DEFAULT_START = date(2010, 1, 1)
SEGMENTS = {
    "development": (date(2010, 1, 1), date(2017, 12, 31)),
    "validation": (date(2018, 1, 1), date(2021, 12, 31)),
    "historical_holdout": (date(2022, 1, 1), date(2099, 12, 31)),
}


@dataclass(frozen=True)
class Bar:
    trading_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class RebalanceRecord:
    signal_date: str
    execution_date: str
    turnover: float
    cost_fraction: float
    gross_target: float
    cash_target: float
    positive_assets: int
    weights: dict[str, float]
    signal_votes: dict[str, int]


def safe_float(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def pct_return(start_price: float, end_price: float) -> float:
    start_price = safe_float(start_price, "start_price")
    end_price = safe_float(end_price, "end_price")
    if start_price <= 0 or end_price <= 0:
        raise ValueError("prices must be positive")
    return end_price / start_price - 1.0


def sample_std(values: Sequence[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def annualized_vol(daily_returns: Sequence[float]) -> float:
    return sample_std(daily_returns) * math.sqrt(252.0)


def trailing_returns(closes: Sequence[float], lookbacks: Sequence[int]) -> dict[int, float]:
    if len(closes) <= max(lookbacks):
        raise ValueError("insufficient close history")
    latest = closes[-1]
    return {lb: pct_return(closes[-1 - lb], latest) for lb in lookbacks}


def trailing_daily_returns(closes: Sequence[float], lookback: int) -> list[float]:
    if len(closes) <= lookback:
        raise ValueError("insufficient close history for volatility")
    window = closes[-(lookback + 1):]
    return [pct_return(window[i - 1], window[i]) for i in range(1, len(window))]


def compute_target_weights(
    close_history: Mapping[str, Sequence[float]],
    lookbacks: Sequence[int] = PRIMARY_LOOKBACKS,
    vol_lookback: int = VOL_LOOKBACK,
    single_asset_cap: float = SINGLE_ASSET_CAP,
    asset_class_cap: float = ASSET_CLASS_CAP,
) -> tuple[dict[str, float], dict[str, int]]:
    """Map lagged closes to long/cash inverse-volatility weights.

    An ETF is eligible when at least two of the three fixed momentum horizons
    are positive. The function accepts no execution-date data.
    """
    raw: dict[str, float] = {}
    votes: dict[str, int] = {}
    for symbol in UNIVERSE:
        closes = list(close_history[symbol])
        horizon_returns = trailing_returns(closes, lookbacks)
        positive_votes = sum(value > 0.0 for value in horizon_returns.values())
        votes[symbol] = positive_votes
        if positive_votes < 2:
            raw[symbol] = 0.0
            continue
        vol = max(annualized_vol(trailing_daily_returns(closes, vol_lookback)), VOL_FLOOR)
        raw[symbol] = (positive_votes / len(lookbacks)) / vol

    raw_total = sum(raw.values())
    if raw_total <= 0.0:
        return {symbol: 0.0 for symbol in UNIVERSE}, votes

    weights = {symbol: min(raw[symbol] / raw_total, single_asset_cap) for symbol in UNIVERSE}
    for asset_class in sorted(set(ASSET_CLASS.values())):
        members = [symbol for symbol in UNIVERSE if ASSET_CLASS[symbol] == asset_class]
        group_total = sum(weights[symbol] for symbol in members)
        if group_total > asset_class_cap:
            scale = asset_class_cap / group_total
            for symbol in members:
                weights[symbol] *= scale

    if sum(weights.values()) > 1.0 + 1e-12:
        raise AssertionError("target gross exceeds one")
    return weights, votes


def validate_bars(bars_by_symbol: Mapping[str, Sequence[Bar]], start: date) -> list[date]:
    missing = [symbol for symbol in UNIVERSE if symbol not in bars_by_symbol]
    if missing:
        raise ValueError(f"missing symbols: {missing}")

    date_sets: list[set[date]] = []
    for symbol in UNIVERSE:
        bars = list(bars_by_symbol[symbol])
        if len(bars) < MIN_HISTORY:
            raise ValueError(f"{symbol}: only {len(bars)} bars; need {MIN_HISTORY}")
        dates = [bar.trading_date for bar in bars]
        if len(dates) != len(set(dates)):
            raise ValueError(f"{symbol}: duplicate trading dates")
        if dates != sorted(dates):
            raise ValueError(f"{symbol}: bars are not sorted")
        for bar in bars:
            if min(bar.open, bar.high, bar.low, bar.close) <= 0:
                raise ValueError(f"{symbol} {bar.trading_date}: non-positive price")
            if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
                raise ValueError(f"{symbol} {bar.trading_date}: invalid OHLC relationship")
        pre_start = sum(d < start for d in dates)
        if pre_start < max(PRIMARY_LOOKBACKS):
            raise ValueError(
                f"{symbol}: only {pre_start} pre-start bars; need {max(PRIMARY_LOOKBACKS)}"
            )
        date_sets.append(set(dates))

    common_dates = sorted(set.intersection(*date_sets))
    if len(common_dates) < MIN_HISTORY:
        raise ValueError("insufficient common-date history")
    return common_dates
