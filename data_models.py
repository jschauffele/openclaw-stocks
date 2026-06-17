from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


AdjustmentType = Literal["raw", "split", "split_dividend"]
DataSource = Literal["alpaca", "alpaca_iex"]


@dataclass(frozen=True)
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        normalized_symbol = self.symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("Candle.symbol must be non-empty")

        if self.timestamp.tzinfo is None:
            raise ValueError("Candle.timestamp must be timezone-aware")

        normalized_timestamp = self.timestamp.astimezone(timezone.utc)

        open_price = float(self.open)
        high_price = float(self.high)
        low_price = float(self.low)
        close_price = float(self.close)
        volume_value = float(self.volume)

        if min(open_price, high_price, low_price, close_price) < 0:
            raise ValueError("Candle OHLC values cannot be negative")

        if high_price < low_price:
            raise ValueError("Candle.high cannot be less than Candle.low")

        if open_price > high_price or open_price < low_price:
            raise ValueError("Candle.open must be within Candle.low and Candle.high")

        if close_price > high_price or close_price < low_price:
            raise ValueError("Candle.close must be within Candle.low and Candle.high")

        if volume_value < 0:
            raise ValueError("Candle.volume cannot be negative")

        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "timestamp", normalized_timestamp)
        object.__setattr__(self, "open", open_price)
        object.__setattr__(self, "high", high_price)
        object.__setattr__(self, "low", low_price)
        object.__setattr__(self, "close", close_price)
        object.__setattr__(self, "volume", volume_value)


@dataclass(frozen=True)
class HistoricalBarsRequest:
    symbol: str
    timeframe: str
    limit: int
    start: datetime | None = None
    end: datetime | None = None

    def __post_init__(self) -> None:
        normalized_symbol = self.symbol.strip().upper()
        normalized_timeframe = self.timeframe.strip()

        if not normalized_symbol:
            raise ValueError("HistoricalBarsRequest.symbol must be non-empty")

        if not normalized_timeframe:
            raise ValueError("HistoricalBarsRequest.timeframe must be non-empty")

        if not isinstance(self.limit, int):
            raise ValueError("HistoricalBarsRequest.limit must be an integer")

        if self.limit <= 0:
            raise ValueError("HistoricalBarsRequest.limit must be greater than 0")

        if self.limit > 1000:
            raise ValueError("HistoricalBarsRequest.limit must be <= 1000")

        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "timeframe", normalized_timeframe)
        if self.start is not None:
            if self.start.tzinfo is None:
                raise ValueError("HistoricalBarsRequest.start must be timezone-aware")
            object.__setattr__(self, "start", self.start.astimezone(timezone.utc))
        if self.end is not None:
            if self.end.tzinfo is None:
                raise ValueError("HistoricalBarsRequest.end must be timezone-aware")
            object.__setattr__(self, "end", self.end.astimezone(timezone.utc))
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("HistoricalBarsRequest.start must be before end")


@dataclass(frozen=True)
class HistoricalBarsResult:
    symbol: str
    timeframe: str
    source: DataSource
    adjustment_type: AdjustmentType
    is_adjusted: bool
    candles: tuple[Candle, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    provider: str = ""
    feed: str = ""
    requested_start: datetime | None = None
    requested_end: datetime | None = None

    def __post_init__(self) -> None:
        normalized_symbol = self.symbol.strip().upper()
        normalized_timeframe = self.timeframe.strip()
        normalized_provider = self.provider.strip() if self.provider else self.source
        normalized_feed = self.feed.strip() if self.feed else "unknown"

        if not normalized_symbol:
            raise ValueError("HistoricalBarsResult.symbol must be non-empty")

        if not normalized_timeframe:
            raise ValueError("HistoricalBarsResult.timeframe must be non-empty")

        if not normalized_provider:
            raise ValueError("HistoricalBarsResult.provider must be non-empty")

        if not normalized_feed:
            raise ValueError("HistoricalBarsResult.feed must be non-empty")

        if not self.candles:
            raise ValueError("HistoricalBarsResult.candles cannot be empty")

        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "timeframe", normalized_timeframe)
        object.__setattr__(self, "candles", tuple(self.candles))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "provider", normalized_provider)
        object.__setattr__(self, "feed", normalized_feed)
        if self.requested_start is not None:
            if self.requested_start.tzinfo is None:
                raise ValueError("HistoricalBarsResult.requested_start must be timezone-aware")
            object.__setattr__(
                self,
                "requested_start",
                self.requested_start.astimezone(timezone.utc),
            )
        if self.requested_end is not None:
            if self.requested_end.tzinfo is None:
                raise ValueError("HistoricalBarsResult.requested_end must be timezone-aware")
            object.__setattr__(
                self,
                "requested_end",
                self.requested_end.astimezone(timezone.utc),
            )
