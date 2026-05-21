from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Real


ALLOWED_REGIME_IDS = frozenset(
    {
        "insufficient_data",
        "volatile",
        "uptrend",
        "downtrend",
        "sideways",
        "unknown",
    }
)


@dataclass(frozen=True, slots=True)
class RegimeClassificationInput:
    closes: tuple[float, ...]
    lookback: int = 5
    min_trend_percent: float = 1.0
    volatility_percent: float = 2.0

    def __post_init__(self) -> None:
        if isinstance(self.lookback, bool) or not isinstance(self.lookback, int):
            raise ValueError("lookback must be an int")
        if self.lookback < 2:
            raise ValueError("lookback must be >= 2")
        _validate_threshold("min_trend_percent", self.min_trend_percent)
        _validate_threshold("volatility_percent", self.volatility_percent)
        for close in self.closes:
            _validate_close(close)


@dataclass(frozen=True, slots=True)
class RegimeClassificationResult:
    regime_id: str
    reason: str
    lookback: int
    sample_count: int
    latest_close: float
    oldest_close: float
    percent_change: float
    absolute_percent_change: float
    max_one_period_move_percent: float

    def __post_init__(self) -> None:
        if self.regime_id not in ALLOWED_REGIME_IDS:
            raise ValueError(f"Unsupported regime_id: {self.regime_id}")
        if not self.reason.strip():
            raise ValueError("reason must be non-empty")
        _validate_finite_number("latest_close", self.latest_close)
        _validate_finite_number("oldest_close", self.oldest_close)
        _validate_finite_number("percent_change", self.percent_change)
        _validate_finite_number("absolute_percent_change", self.absolute_percent_change)
        _validate_finite_number(
            "max_one_period_move_percent",
            self.max_one_period_move_percent,
        )


def classify_regime(
    input_model: RegimeClassificationInput,
) -> RegimeClassificationResult:
    if not isinstance(input_model, RegimeClassificationInput):
        raise ValueError("input_model must be RegimeClassificationInput")

    sample_count = len(input_model.closes)
    if sample_count < input_model.lookback:
        latest_close = float(input_model.closes[-1]) if input_model.closes else 0.0
        oldest_close = float(input_model.closes[0]) if input_model.closes else 0.0
        return RegimeClassificationResult(
            regime_id="insufficient_data",
            reason="sample_count_below_lookback",
            lookback=input_model.lookback,
            sample_count=sample_count,
            latest_close=latest_close,
            oldest_close=oldest_close,
            percent_change=0.0,
            absolute_percent_change=0.0,
            max_one_period_move_percent=0.0,
        )

    window = tuple(float(close) for close in input_model.closes[-input_model.lookback :])
    oldest_close = window[0]
    latest_close = window[-1]
    percent_change = ((latest_close - oldest_close) / oldest_close) * 100.0
    absolute_percent_change = abs(percent_change)
    max_one_period_move_percent = _max_one_period_move_percent(window)

    if max_one_period_move_percent >= input_model.volatility_percent:
        regime_id = "volatile"
        reason = "one_period_move_meets_volatility_threshold"
    elif percent_change >= input_model.min_trend_percent:
        regime_id = "uptrend"
        reason = "percent_change_meets_uptrend_threshold"
    elif percent_change <= -input_model.min_trend_percent:
        regime_id = "downtrend"
        reason = "percent_change_meets_downtrend_threshold"
    else:
        regime_id = "sideways"
        reason = "percent_change_inside_trend_thresholds"

    return RegimeClassificationResult(
        regime_id=regime_id,
        reason=reason,
        lookback=input_model.lookback,
        sample_count=sample_count,
        latest_close=latest_close,
        oldest_close=oldest_close,
        percent_change=percent_change,
        absolute_percent_change=absolute_percent_change,
        max_one_period_move_percent=max_one_period_move_percent,
    )


def _max_one_period_move_percent(closes: tuple[float, ...]) -> float:
    moves = []
    for previous_close, latest_close in zip(closes, closes[1:]):
        moves.append(abs(((latest_close - previous_close) / previous_close) * 100.0))
    return max(moves) if moves else 0.0


def _validate_close(close: float) -> None:
    if isinstance(close, bool) or not isinstance(close, Real):
        raise ValueError("closes must contain numeric values")
    close_value = float(close)
    if not isfinite(close_value):
        raise ValueError("closes must contain finite values")
    if close_value <= 0:
        raise ValueError("closes must contain positive values")


def _validate_threshold(field_name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be numeric")
    threshold_value = float(value)
    if not isfinite(threshold_value):
        raise ValueError(f"{field_name} must be finite")
    if threshold_value < 0:
        raise ValueError(f"{field_name} must be >= 0")


def _validate_finite_number(field_name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be numeric")
    if not isfinite(float(value)):
        raise ValueError(f"{field_name} must be finite")
