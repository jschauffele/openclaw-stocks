from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

from alpaca.common.exceptions import APIError
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

from data_models import Candle, HistoricalBarsRequest, HistoricalBarsResult
from market_data import MarketDataProvider, validate_request


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _resolve_data_url_override(base_url: Optional[str]) -> Optional[str]:
    if not base_url:
        return None

    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()

    if host in {"paper-api.alpaca.markets", "api.alpaca.markets"}:
        return None

    return base_url


_TIMEFRAME_MAP = {
    "1Min": TimeFrame.Minute,
    "5Min": TimeFrame(5, TimeFrame.Minute.unit_value),
    "15Min": TimeFrame(15, TimeFrame.Minute.unit_value),
    "1Hour": TimeFrame.Hour,
    "1Day": TimeFrame.Day,
}


def _fallback_start_for(timeframe_name: str) -> datetime:
    now = datetime.now(timezone.utc)
    if timeframe_name == "1Day":
        return now - timedelta(days=10)
    if timeframe_name == "1Hour":
        return now - timedelta(days=5)
    return now - timedelta(days=2)


class AlpacaMarketDataProvider(MarketDataProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        raw_data: bool = False,
    ) -> None:
        load_dotenv()

        resolved_api_key = api_key or _first_env("ALPACA_API_KEY", "APCA_API_KEY_ID")
        resolved_secret_key = secret_key or _first_env(
            "ALPACA_SECRET_KEY",
            "APCA_API_SECRET_KEY",
        )
        resolved_base_url = _resolve_data_url_override(
            base_url or _first_env("ALPACA_BASE_URL", "APCA_API_BASE_URL")
        )

        if not resolved_api_key or not resolved_secret_key:
            raise ValueError(
                "Missing Alpaca credentials. Set ALPACA_API_KEY / ALPACA_SECRET_KEY "
                "or APCA_API_KEY_ID / APCA_API_SECRET_KEY."
            )

        client_kwargs = {
            "api_key": resolved_api_key,
            "secret_key": resolved_secret_key,
            "raw_data": raw_data,
        }

        if resolved_base_url:
            client_kwargs["url_override"] = resolved_base_url

        self.client = StockHistoricalDataClient(**client_kwargs)

    def _fetch_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        limit: int,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ):
        request_kwargs = {
            "symbol_or_symbols": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "adjustment": "raw",
            "feed": "iex",
        }

        if start is not None:
            request_kwargs["start"] = start
        if end is not None:
            request_kwargs["end"] = end

        bars_request = StockBarsRequest(**request_kwargs)
        response = self.client.get_stock_bars(bars_request)
        return response.data.get(symbol, [])

    def get_historical_bars(self, request: HistoricalBarsRequest) -> HistoricalBarsResult:
        validated_request = validate_request(request)
        timeframe = _TIMEFRAME_MAP[validated_request.timeframe]
        warnings: list[str] = []

        try:
            bars = self._fetch_bars(
                symbol=validated_request.symbol,
                timeframe=timeframe,
                limit=validated_request.limit,
            )
        except APIError as exc:
            raise ValueError(f"Alpaca market data request failed: {exc}") from exc

        requires_retry_window = (
            validated_request.timeframe == "1Day" and len(bars) < 2
        )

        if not bars or requires_retry_window:
            end = datetime.now(timezone.utc)
            start = _fallback_start_for(validated_request.timeframe)

            try:
                fallback_bars = self._fetch_bars(
                    symbol=validated_request.symbol,
                    timeframe=timeframe,
                    limit=validated_request.limit,
                    start=start,
                    end=end,
                )
            except APIError as exc:
                raise ValueError(f"Alpaca fallback market data request failed: {exc}") from exc

            if fallback_bars:
                bars = fallback_bars
                if requires_retry_window:
                    warnings.append(
                        "Default IEX request returned fewer than 2 daily bars; retried with explicit recent date window."
                    )
                else:
                    warnings.append(
                        "Default IEX request returned no bars; retried with explicit recent date window."
                    )

        candles = tuple(
            Candle(
                symbol=validated_request.symbol,
                timestamp=bar.timestamp.astimezone(timezone.utc),
                open=float(bar.open),
                high=float(bar.high),
                low=float(bar.low),
                close=float(bar.close),
                volume=float(bar.volume),
            )
            for bar in bars
        )

        if not candles:
            raise ValueError(
                f"No historical bars returned for {validated_request.symbol} "
                f"({validated_request.timeframe})."
            )

        return HistoricalBarsResult(
            symbol=validated_request.symbol,
            timeframe=validated_request.timeframe,
            source="alpaca",
            adjustment_type="raw",
            is_adjusted=False,
            candles=candles,
            warnings=tuple(warnings),
        )


AlpacaDataProvider = AlpacaMarketDataProvider
