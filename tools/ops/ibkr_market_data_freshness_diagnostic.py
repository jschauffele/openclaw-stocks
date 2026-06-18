"""Fail-closed IBKR read-only market-data freshness diagnostic scaffold.

This CLI prepares the output shape for a future separately authorized IBKR
historical market-data diagnostic. It does not import IBKR clients, connect to
TWS/Gateway, read credentials, request market data, query account/order/
position/margin/portfolio state, capture packages, replay, score, generate
candidates, mutate runtime/systemd/timer state, mark D11 complete, or open
Unit 12.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from typing import Any

from ibkr_market_data_diagnostic_contract import (
    D11_STATUS_INSUFFICIENT,
    IBKR_PROVIDER_KEY,
    IBKR_PROVIDER_NAME,
    IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    UNIT_12_STATUS_BLOCKED,
)
from market_data import compute_request_window
from market_data_provider_selection import CANDIDATE_STATUS_CANDIDATE


IBKR_DIAGNOSTIC_SCAFFOLD_RESULT_TYPE = (
    "ibkr_read_only_market_data_freshness_diagnostic_scaffold"
)
IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "no_ibkr_connection",
    "no_tws_gateway_start",
    "no_credentials_read",
    "no_account_query",
    "no_position_query",
    "no_margin_query",
    "no_portfolio_query",
    "no_order_authority",
    "no_execution_authority",
    "no_package_capture",
    "no_replay",
    "no_scoring",
    "no_candidate_generation",
    "no_unit_12_opening",
    "no_d11_completion",
)
IBKR_DIAGNOSTIC_NOT_AUTHORIZED_REASON = (
    "real IBKR historical market-data diagnostic is not authorized or opened; "
    "IBKR connection is not opened, credentials are not read, TWS/Gateway is "
    "not started, and account/order/position/margin/portfolio queries are "
    "prohibited"
)


def build_scaffold_result(
    *,
    symbols: Iterable[str],
    timeframe: str,
    limit: int,
    requested_end: datetime | None = None,
    lookback_minutes: int | None = None,
) -> dict[str, Any]:
    window_start, window_end = compute_request_window(
        timeframe=timeframe,
        limit=limit,
        requested_end=requested_end,
        lookback_minutes=lookback_minutes,
    )
    rows = tuple(
        _scaffold_row(
            symbol=symbol,
            timeframe=timeframe,
            requested_start=window_start,
            requested_end=window_end,
        )
        for symbol in symbols
    )
    return {
        "result_type": IBKR_DIAGNOSTIC_SCAFFOLD_RESULT_TYPE,
        "d11_status": D11_STATUS_INSUFFICIENT,
        "unit_12_status": UNIT_12_STATUS_BLOCKED,
        "results": rows,
        "package_capture": False,
        "replay": False,
        "scoring": False,
        "candidate_generation": False,
        "broker_api_authority": False,
        "order_authority": False,
        "execution_authority": False,
        "d11_completion_authority": False,
        "authority_boundary": IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY,
        "contract_authority_boundary": IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    }


def _scaffold_row(
    *,
    symbol: str,
    timeframe: str,
    requested_start: datetime,
    requested_end: datetime,
) -> dict[str, Any]:
    return {
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": IBKR_PROVIDER_NAME,
        "connection_mode": "not_opened",
        "read_only": True,
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "symbol": symbol.strip().upper(),
        "timeframe": timeframe,
        "latest_candle_timestamp": None,
        "lag_minutes": None,
        "freshness_classification": "unavailable",
        "d11_countable": False,
        "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
        "d11_primary_eligible": False,
        "failure_reason": IBKR_DIAGNOSTIC_NOT_AUTHORIZED_REASON,
        "authority_boundary": IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY,
    }


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
        description="Fail-closed IBKR read-only market-data diagnostic scaffold."
    )
    parser.add_argument("--symbol", action="append", dest="symbols", required=True)
    parser.add_argument("--timeframe", default="15Min")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--requested-end")
    parser.add_argument("--lookback-minutes", type=int)
    args = parser.parse_args(argv)

    result = build_scaffold_result(
        symbols=args.symbols,
        timeframe=args.timeframe,
        limit=args.limit,
        requested_end=_parse_requested_end(args.requested_end),
        lookback_minutes=args.lookback_minutes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
