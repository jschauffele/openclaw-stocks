#!/usr/bin/env python3
"""
data_engine.py

Purpose:
- Connect to Alpaca market data API
- Fetch historical OHLCV bars
- Validate inputs
- Normalize output into a clean internal structure
- Run standalone from terminal for testing

Examples:
    python3 data_engine.py
    python3 data_engine.py AAPL 1Min 5
    python3 data_engine.py MSFT 5Min 10

Important:
- Does NOT place trades
- Does NOT import main.py
- Does NOT integrate with execution yet
- Does NOT include strategy, features, or ML
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


@dataclass
class Candle:
    symbol: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: Optional[int] = None
    vwap: Optional[float] = None


class DataEngine:
    """
    Standalone data access layer for historical stock bar retrieval.
    """

    SUPPORTED_TIMEFRAMES = {
        "1Min": TimeFrame.Minute,
        "5Min": TimeFrame(5, TimeFrame.Minute.unit_value),
        "15Min": TimeFrame(15, TimeFrame.Minute.unit_value),
        "1Hour": TimeFrame.Hour,
        "1Day": TimeFrame.Day,
    }

    def __init__(self) -> None:
        load_dotenv()

        self.api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Missing Alpaca credentials. Set ALPACA_API_KEY / ALPACA_SECRET_KEY "
                "or APCA_API_KEY_ID / APCA_API_SECRET_KEY in .env"
            )

        self.client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
        )

    def get_recent_bars(
        self,
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 5,
    ) -> List[Candle]:
        normalized_symbol = self._validate_symbol(symbol)
        normalized_timeframe = self._validate_timeframe(timeframe)
        normalized_limit = self._validate_limit(limit)

        request = StockBarsRequest(
            symbol_or_symbols=normalized_symbol,
            timeframe=normalized_timeframe,
            limit=normalized_limit,
        )

        response = self.client.get_stock_bars(request)

        bars = getattr(response, "data", {}).get(normalized_symbol, [])
        if not bars:
            raise RuntimeError(f"No bar data returned for symbol={normalized_symbol}")

        candles: List[Candle] = []
        for bar in bars:
            candles.append(
                Candle(
                    symbol=normalized_symbol,
                    timestamp=bar.timestamp.isoformat(),
                    open=float(bar.open),
                    high=float(bar.high),
                    low=float(bar.low),
                    close=float(bar.close),
                    volume=float(bar.volume),
                    trade_count=self._safe_int(getattr(bar, "trade_count", None)),
                    vwap=self._safe_float(getattr(bar, "vwap", None)),
                )
            )

        return candles

    def _validate_symbol(self, symbol: str) -> str:
        if not isinstance(symbol, str):
            raise ValueError("symbol must be a string")

        cleaned = symbol.strip().upper()
        if not cleaned:
            raise ValueError("symbol must not be empty")

        if not cleaned.isalnum():
            raise ValueError("symbol must be alphanumeric only for this phase")

        if len(cleaned) > 10:
            raise ValueError("symbol is unexpectedly long")

        return cleaned

    def _validate_timeframe(self, timeframe: str) -> TimeFrame:
        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            supported = ", ".join(self.SUPPORTED_TIMEFRAMES.keys())
            raise ValueError(
                f"Unsupported timeframe '{timeframe}'. Supported: {supported}"
            )
        return self.SUPPORTED_TIMEFRAMES[timeframe]

    def _validate_limit(self, limit: int) -> int:
        if not isinstance(limit, int):
            raise ValueError("limit must be an integer")

        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        if limit > 1000:
            raise ValueError("limit must be <= 1000 for this phase")

        return limit

    @staticmethod
    def _safe_int(value: object) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value: object) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


def parse_args() -> tuple[str, str, int]:
    """
    Optional CLI usage:
        python3 data_engine.py
        python3 data_engine.py AAPL 1Min 5
    """
    symbol = "AAPL"
    timeframe = "1Min"
    limit = 5

    if len(sys.argv) >= 2:
        symbol = sys.argv[1]

    if len(sys.argv) >= 3:
        timeframe = sys.argv[2]

    if len(sys.argv) >= 4:
        try:
            limit = int(sys.argv[3])
        except ValueError as exc:
            raise ValueError("limit must be an integer") from exc

    if len(sys.argv) > 4:
        raise ValueError(
            "Too many arguments. Usage: python3 data_engine.py [SYMBOL] [TIMEFRAME] [LIMIT]"
        )

    return symbol, timeframe, limit


def main() -> int:
    print("=== DataEngine standalone test ===")
    print("This test fetches historical market data only.")
    print("It does NOT place trades.\n")

    try:
        symbol, timeframe, limit = parse_args()

        engine = DataEngine()
        candles = engine.get_recent_bars(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        print(f"Symbol: {symbol}")
        print(f"Timeframe: {timeframe}")
        print(f"Limit: {limit}")
        print(f"Fetched {len(candles)} candles:\n")

        for candle in candles:
            print(candle)

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
