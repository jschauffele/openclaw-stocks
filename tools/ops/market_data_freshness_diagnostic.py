"""Read-only market-data provider freshness diagnostic.

This command checks normalized market-data provider output across configured
symbols. It does not capture packages, replay, score, generate candidates,
touch runtime/systemd, call broker/order APIs, open Unit 12, or grant execution
authority.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from typing import Any

import config
from alpaca_data_provider import AlpacaMarketDataProvider
from data_models import HistoricalBarsRequest
from market_data import (
    MARKET_DATA_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    classify_market_data_freshness,
)


DIAGNOSTIC_RESULT_TYPE = "market_data_freshness_diagnostic"


def run_diagnostic(
    *,
    provider: Any,
    symbols: Iterable[str],
    timeframe: str,
    limit: int,
    run_timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate provider freshness using already-normalized provider results."""

    evaluated_at = (run_timestamp or datetime.now(timezone.utc)).astimezone(
        timezone.utc
    )
    results = []
    for symbol in symbols:
        request = HistoricalBarsRequest(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        bars_result = provider.get_historical_bars(request)
        latest_candle = bars_result.candles[-1].timestamp
        freshness = classify_market_data_freshness(
            latest_candle_timestamp=latest_candle,
            run_timestamp=evaluated_at,
            warnings=tuple(bars_result.warnings),
        )
        results.append(
            {
                "provider": bars_result.provider,
                "feed": bars_result.feed,
                "symbol": bars_result.symbol,
                "timeframe": bars_result.timeframe,
                "requested_start": (
                    bars_result.requested_start.isoformat()
                    if bars_result.requested_start is not None
                    else None
                ),
                "requested_end": (
                    bars_result.requested_end.isoformat()
                    if bars_result.requested_end is not None
                    else None
                ),
                "latest_candle_timestamp": freshness.latest_candle_timestamp,
                "run_timestamp": freshness.run_timestamp,
                "lag_minutes": freshness.lag_minutes,
                "freshness_classification": freshness.freshness_classification,
                "warnings": list(freshness.warnings),
                "d11_countable": freshness.d11_countable,
                "freshness_warning_reason": freshness.warning_reason,
            }
        )

    return {
        "result_type": DIAGNOSTIC_RESULT_TYPE,
        "results": tuple(results),
        "package_capture": False,
        "replay": False,
        "scoring": False,
        "candidate_generation": False,
        "broker_api_authority": False,
        "order_authority": False,
        "execution_authority": False,
        "runtime_work": False,
        "unit_12_opening": False,
        "authority_boundary": MARKET_DATA_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    }


def _symbols_from_args(values: Sequence[str] | None) -> tuple[str, ...]:
    if values:
        return tuple(symbol.strip().upper() for symbol in values if symbol.strip())
    return tuple(config.ALLOWED_SYMBOLS)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only market-data provider freshness diagnostic."
    )
    parser.add_argument("--symbol", action="append", dest="symbols")
    parser.add_argument("--timeframe", default="15Min")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)

    provider = AlpacaMarketDataProvider()
    result = run_diagnostic(
        provider=provider,
        symbols=_symbols_from_args(args.symbols),
        timeframe=args.timeframe,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
