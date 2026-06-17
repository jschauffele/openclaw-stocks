from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from data_models import HistoricalBarsRequest, HistoricalBarsResult


SUPPORTED_TIMEFRAMES: tuple[str, ...] = (
    "1Min",
    "5Min",
    "15Min",
    "1Hour",
    "1Day",
)
MAX_LATEST_CANDLE_LAG_SECONDS = 30 * 60
FRESHNESS_CLEAN = "clean"
FRESHNESS_RECENCY_CAVEATED = "recency_caveated"
FRESHNESS_QUARANTINED = "quarantined"
TIMEFRAME_MINUTES = {
    "1Min": 1,
    "5Min": 5,
    "15Min": 15,
    "1Hour": 60,
    "1Day": 1440,
}

MARKET_DATA_DIAGNOSTIC_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "read_only_market_data_diagnostic",
    "no_package_capture",
    "no_replay",
    "no_scoring",
    "no_candidate_generation",
    "no_broker_api_authority",
    "no_order_authority",
    "no_execution_authority",
    "no_runtime_start_or_restart",
    "no_unit_12_opening",
)


class MarketDataProvider(Protocol):
    def get_historical_bars(self, request: HistoricalBarsRequest) -> HistoricalBarsResult:
        ...


@dataclass(frozen=True, slots=True)
class MarketDataFreshness:
    freshness_classification: str
    d11_countable: bool
    lag_minutes: float | None
    warning_reason: str
    latest_candle_timestamp: str
    run_timestamp: str
    warnings: tuple[str, ...]
    max_latest_candle_lag_seconds: int = MAX_LATEST_CANDLE_LAG_SECONDS


def validate_timeframe(timeframe: str) -> str:
    normalized = timeframe.strip()
    if normalized not in SUPPORTED_TIMEFRAMES:
        supported = ", ".join(SUPPORTED_TIMEFRAMES)
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {supported}")
    return normalized


def validate_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol must be non-empty")
    return normalized


def validate_request(request: HistoricalBarsRequest) -> HistoricalBarsRequest:
    validated_symbol = validate_symbol(request.symbol)
    validated_timeframe = validate_timeframe(request.timeframe)

    return HistoricalBarsRequest(
        symbol=validated_symbol,
        timeframe=validated_timeframe,
        limit=request.limit,
        start=request.start,
        end=request.end,
    )


def get_historical_bars(
    provider: MarketDataProvider,
    symbol: str,
    timeframe: str,
    limit: int,
    *,
    requested_start: datetime | None = None,
    requested_end: datetime | None = None,
    lookback_minutes: int | None = None,
) -> HistoricalBarsResult:
    if requested_start is None or requested_end is None:
        requested_start, requested_end = compute_request_window(
            timeframe=timeframe,
            limit=limit,
            requested_end=requested_end,
            lookback_minutes=lookback_minutes,
        )
    request = validate_request(
        HistoricalBarsRequest(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            start=requested_start,
            end=requested_end,
        )
    )
    return provider.get_historical_bars(request)


def compute_request_window(
    *,
    timeframe: str,
    limit: int,
    requested_end: datetime | None = None,
    lookback_minutes: int | None = None,
) -> tuple[datetime, datetime]:
    """Return a deterministic UTC request window for a bars request."""

    validated_timeframe = validate_timeframe(timeframe)
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")
    end = (requested_end or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if lookback_minutes is None:
        lookback_minutes = TIMEFRAME_MINUTES[validated_timeframe] * (limit + 1)
    if lookback_minutes <= 0:
        raise ValueError("lookback_minutes must be positive")
    start = end - timedelta(minutes=lookback_minutes)
    if start >= end:
        raise ValueError("requested_start must be before requested_end")
    return start, end


def normalized_closes_from_bars(result: HistoricalBarsResult) -> list[float]:
    """Return strategy-ready closes from normalized provider output."""

    return [float(candle.close) for candle in result.candles]


def classify_market_data_freshness(
    *,
    latest_candle_timestamp: datetime | str | None,
    run_timestamp: datetime | str | None,
    warnings: tuple[str, ...] | list[str] = (),
    max_lag_seconds: int = MAX_LATEST_CANDLE_LAG_SECONDS,
) -> MarketDataFreshness:
    """Classify already-loaded market data without reading packages or providers."""

    normalized_warnings = tuple(str(warning) for warning in warnings if str(warning))
    latest_dt = _parse_timestamp(latest_candle_timestamp)
    run_dt = _parse_timestamp(run_timestamp)
    latest_text = _timestamp_text(latest_dt, latest_candle_timestamp)
    run_text = _timestamp_text(run_dt, run_timestamp)

    if normalized_warnings:
        return MarketDataFreshness(
            freshness_classification=FRESHNESS_QUARANTINED,
            d11_countable=False,
            lag_minutes=_lag_minutes(run_dt, latest_dt),
            warning_reason="market_input_captured_warnings_present",
            latest_candle_timestamp=latest_text,
            run_timestamp=run_text,
            warnings=normalized_warnings,
            max_latest_candle_lag_seconds=max_lag_seconds,
        )
    if run_dt is None:
        return MarketDataFreshness(
            freshness_classification=FRESHNESS_QUARANTINED,
            d11_countable=False,
            lag_minutes=None,
            warning_reason="missing_or_malformed_run_timestamp",
            latest_candle_timestamp=latest_text,
            run_timestamp=run_text,
            warnings=normalized_warnings,
            max_latest_candle_lag_seconds=max_lag_seconds,
        )
    if latest_dt is None:
        return MarketDataFreshness(
            freshness_classification=FRESHNESS_QUARANTINED,
            d11_countable=False,
            lag_minutes=None,
            warning_reason="missing_or_malformed_latest_candle_timestamp",
            latest_candle_timestamp=latest_text,
            run_timestamp=run_text,
            warnings=normalized_warnings,
            max_latest_candle_lag_seconds=max_lag_seconds,
        )
    lag_seconds = (run_dt - latest_dt).total_seconds()
    lag_minutes = lag_seconds / 60
    if latest_dt.date() < run_dt.date():
        classification = FRESHNESS_QUARANTINED
        reason = "latest_candle_prior_to_run_date"
        countable = False
    elif latest_dt.date() > run_dt.date() or lag_seconds < 0:
        classification = FRESHNESS_QUARANTINED
        reason = "latest_candle_after_run_timestamp"
        countable = False
    elif lag_seconds > max_lag_seconds:
        classification = FRESHNESS_RECENCY_CAVEATED
        reason = "latest_candle_lag_exceeds_threshold"
        countable = False
    else:
        classification = FRESHNESS_CLEAN
        reason = ""
        countable = True
    return MarketDataFreshness(
        freshness_classification=classification,
        d11_countable=countable,
        lag_minutes=lag_minutes,
        warning_reason=reason,
        latest_candle_timestamp=latest_text,
        run_timestamp=run_text,
        warnings=normalized_warnings,
        max_latest_candle_lag_seconds=max_lag_seconds,
    )


def freshness_payload(freshness: MarketDataFreshness) -> dict:
    return {
        "lag_minutes": freshness.lag_minutes,
        "freshness_classification": freshness.freshness_classification,
        "d11_countable": freshness.d11_countable,
        "freshness_warning_reason": freshness.warning_reason,
        "max_latest_candle_lag_seconds": freshness.max_latest_candle_lag_seconds,
    }


def _parse_timestamp(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value:
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_text(
    parsed: datetime | None, original: datetime | str | None
) -> str | None:
    if parsed is not None:
        return parsed.isoformat()
    if isinstance(original, str):
        return original
    return None


def _lag_minutes(
    run_dt: datetime | None, latest_dt: datetime | None
) -> float | None:
    if run_dt is None or latest_dt is None:
        return None
    return (run_dt - latest_dt).total_seconds() / 60
