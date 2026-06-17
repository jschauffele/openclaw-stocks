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
    compute_request_window,
)
from market_data_provider_registry import get_provider_registry_entry


DIAGNOSTIC_RESULT_TYPE = "market_data_freshness_diagnostic"


def run_diagnostic(
    *,
    provider: Any,
    symbols: Iterable[str],
    timeframe: str,
    limit: int,
    run_timestamp: datetime | None = None,
    requested_end: datetime | None = None,
    lookback_minutes: int | None = None,
) -> dict[str, Any]:
    """Evaluate provider freshness using already-normalized provider results."""

    evaluated_at = (run_timestamp or datetime.now(timezone.utc)).astimezone(
        timezone.utc
    )
    window_start, window_end = compute_request_window(
        timeframe=timeframe,
        limit=limit,
        requested_end=requested_end or evaluated_at,
        lookback_minutes=lookback_minutes,
    )
    results = []
    for symbol in symbols:
        request = HistoricalBarsRequest(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            start=window_start,
            end=window_end,
        )
        bars_result = provider.get_historical_bars(request)
        provider_registry_entry = get_provider_registry_entry(
            provider=bars_result.provider,
            feed=bars_result.feed,
        )
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
                "provider_role": provider_registry_entry["provider_role"],
                "provider_status": provider_registry_entry["provider_status"],
                "d11_primary_eligible": provider_registry_entry[
                    "d11_primary_eligible"
                ],
                "reason": provider_registry_entry["reason"],
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


def _parse_requested_end(value: str | None) -> datetime | None:
    if value is None:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("--requested-end must be timezone-aware UTC")
    return parsed.astimezone(timezone.utc)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only market-data provider freshness diagnostic."
    )
    parser.add_argument("--symbol", action="append", dest="symbols")
    parser.add_argument("--timeframe", default="15Min")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--requested-end")
    parser.add_argument("--lookback-minutes", type=int)
    args = parser.parse_args(argv)

    provider = AlpacaMarketDataProvider()
    requested_end = _parse_requested_end(args.requested_end)
    result = run_diagnostic(
        provider=provider,
        symbols=_symbols_from_args(args.symbols),
        timeframe=args.timeframe,
        limit=args.limit,
        requested_end=requested_end,
        lookback_minutes=args.lookback_minutes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
