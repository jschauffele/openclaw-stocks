from __future__ import annotations

from typing import Protocol

from data_models import HistoricalBarsRequest, HistoricalBarsResult


SUPPORTED_TIMEFRAMES: tuple[str, ...] = (
    "1Min",
    "5Min",
    "15Min",
    "1Hour",
    "1Day",
)


class MarketDataProvider(Protocol):
    def get_historical_bars(self, request: HistoricalBarsRequest) -> HistoricalBarsResult:
        ...


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
    )


def get_historical_bars(
    provider: MarketDataProvider,
    symbol: str,
    timeframe: str,
    limit: int,
) -> HistoricalBarsResult:
    request = validate_request(
        HistoricalBarsRequest(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    )
    return provider.get_historical_bars(request)
