"""Local-only IBKR read-only historical market-data smoke path.

The default path delegates to the D11.13 fail-closed scaffold and makes no
connection attempt. A future local smoke may attempt historical market data only
when --authorize-local-ibkr-read-only-smoke is supplied. This module never reads
credentials, never starts TWS/Gateway, never queries account/order/position/
margin/portfolio state, never captures packages, never replays, never scores,
never generates candidates, never marks D11 complete, and never opens Unit 12.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from typing import Any, Callable

from ibkr_market_data_diagnostic_contract import (
    D11_STATUS_INSUFFICIENT,
    IBKR_PROVIDER_KEY,
    IBKR_PROVIDER_NAME,
    IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    UNIT_12_STATUS_BLOCKED,
)
from market_data import classify_market_data_freshness, compute_request_window
from market_data_provider_selection import CANDIDATE_STATUS_CANDIDATE
from tools.ops.ibkr_market_data_freshness_diagnostic import build_scaffold_result


IBKR_READ_ONLY_SMOKE_RESULT_TYPE = "ibkr_local_read_only_market_data_smoke"
IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "local_only",
    "explicit_cli_authorization_required",
    "historical_market_data_only",
    "no_credentials_read",
    "no_tws_gateway_start",
    "no_account_query",
    "no_position_query",
    "no_margin_query",
    "no_buying_power_query",
    "no_portfolio_query",
    "no_order_placement",
    "no_order_modification",
    "no_order_cancellation",
    "no_order_routing",
    "no_execution_authority",
    "no_package_capture",
    "no_replay",
    "no_scoring",
    "no_candidate_generation",
    "no_d11_completion",
    "no_unit_12_opening",
    "no_vps_runtime_systemd_timer_mutation",
)
IBKR_READ_ONLY_SMOKE_DEPENDENCY_UNAVAILABLE_REASON = (
    "ib_insync dependency unavailable; local IBKR read-only smoke failed closed"
)
IBKR_READ_ONLY_SMOKE_CONNECTION_FAILED_REASON = (
    "local IBKR read-only historical market-data smoke failed closed"
)


def build_smoke_result(
    *,
    symbols: Iterable[str],
    timeframe: str,
    limit: int,
    requested_end: datetime | None = None,
    lookback_minutes: int | None = None,
    host: str = "127.0.0.1",
    port: int = 7497,
    client_id: int = 9117,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
    outside_rth: bool = False,
    timeout_seconds: float = 10.0,
    authorize_local_ibkr_read_only_smoke: bool = False,
    ibkr_dependency_loader: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    if not authorize_local_ibkr_read_only_smoke:
        return build_scaffold_result(
            symbols=symbols,
            timeframe=timeframe,
            limit=limit,
            requested_end=requested_end,
            lookback_minutes=lookback_minutes,
        )

    window_start, window_end = compute_request_window(
        timeframe=timeframe,
        limit=limit,
        requested_end=requested_end,
        lookback_minutes=lookback_minutes,
    )
    rows = tuple(
        _authorized_local_smoke_row(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            requested_start=window_start,
            requested_end=window_end,
            host=host,
            port=port,
            client_id=client_id,
            exchange=exchange,
            currency=currency,
            sec_type=sec_type,
            outside_rth=outside_rth,
            timeout_seconds=timeout_seconds,
            ibkr_dependency_loader=ibkr_dependency_loader,
        )
        for symbol in symbols
    )
    return {
        "result_type": IBKR_READ_ONLY_SMOKE_RESULT_TYPE,
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
        "authority_boundary": IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY,
        "contract_authority_boundary": IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    }


def run_smoke_diagnostic(
    *,
    symbols: Iterable[str],
    timeframe: str,
    requested_end: datetime | None = None,
    lookback_minutes: int | None = None,
    authorize_local_ibkr_read_only_smoke: bool = False,
    ibkr_dependency_loader: Callable[[], Any] | None = None,
    host: str = "127.0.0.1",
    port: int = 7497,
    client_id: int = 9117,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
    outside_rth: bool = False,
    timeout_seconds: float = 10.0,
    limit: int = 5,
) -> dict[str, Any]:
    """Stable public API for the local-only IBKR read-only smoke diagnostic."""

    return build_smoke_result(
        symbols=symbols,
        timeframe=timeframe,
        limit=limit,
        requested_end=requested_end,
        lookback_minutes=lookback_minutes,
        host=host,
        port=port,
        client_id=client_id,
        exchange=exchange,
        currency=currency,
        sec_type=sec_type,
        outside_rth=outside_rth,
        timeout_seconds=timeout_seconds,
        authorize_local_ibkr_read_only_smoke=authorize_local_ibkr_read_only_smoke,
        ibkr_dependency_loader=ibkr_dependency_loader,
    )


def _authorized_local_smoke_row(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    requested_start: datetime,
    requested_end: datetime,
    host: str,
    port: int,
    client_id: int,
    exchange: str,
    currency: str,
    sec_type: str,
    outside_rth: bool,
    timeout_seconds: float,
    ibkr_dependency_loader: Callable[[], Any] | None,
) -> dict[str, Any]:
    normalized_symbol = symbol.strip().upper()
    try:
        dependency_loader = ibkr_dependency_loader or _load_ib_insync
        ib_insync = dependency_loader()
    except ImportError:
        return _fail_closed_row(
            symbol=normalized_symbol,
            timeframe=timeframe,
            requested_start=requested_start,
            requested_end=requested_end,
            failure_reason=IBKR_READ_ONLY_SMOKE_DEPENDENCY_UNAVAILABLE_REASON,
            connection_mode="local_read_only_smoke",
        )

    ib_client = ib_insync.IB()
    try:
        ib_client.connect(host, port, clientId=client_id, timeout=timeout_seconds)
        contract = ib_insync.Contract()
        contract.symbol = normalized_symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        bars = ib_client.reqHistoricalData(
            contract,
            endDateTime=requested_end,
            durationStr=_duration_string(requested_start, requested_end),
            barSizeSetting=_ibkr_bar_size(timeframe),
            whatToShow="TRADES",
            useRTH=0 if outside_rth else 1,
            formatDate=2,
            keepUpToDate=False,
        )
    except Exception as exc:  # noqa: BLE001 - local smoke must fail closed.
        return _fail_closed_row(
            symbol=normalized_symbol,
            timeframe=timeframe,
            requested_start=requested_start,
            requested_end=requested_end,
            failure_reason=f"{IBKR_READ_ONLY_SMOKE_CONNECTION_FAILED_REASON}: {type(exc).__name__}",
            connection_mode="local_read_only_smoke",
        )
    finally:
        if ib_client.isConnected():
            ib_client.disconnect()

    if not bars:
        return _fail_closed_row(
            symbol=normalized_symbol,
            timeframe=timeframe,
            requested_start=requested_start,
            requested_end=requested_end,
            failure_reason="local IBKR read-only smoke returned no historical bars",
            connection_mode="local_read_only_smoke",
        )

    latest_candle_timestamp = _bar_timestamp(bars[-1])
    freshness = classify_market_data_freshness(
        latest_candle_timestamp=latest_candle_timestamp,
        run_timestamp=requested_end,
        warnings=(),
    )
    return {
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": IBKR_PROVIDER_NAME,
        "connection_mode": "local_read_only_smoke",
        "read_only": True,
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "symbol": normalized_symbol,
        "timeframe": timeframe,
        "latest_candle_timestamp": freshness.latest_candle_timestamp,
        "lag_minutes": freshness.lag_minutes,
        "freshness_classification": freshness.freshness_classification,
        "d11_countable": freshness.d11_countable,
        "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
        "d11_primary_eligible": False,
        "failure_reason": freshness.warning_reason,
        "authority_boundary": IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY,
    }


def _fail_closed_row(
    *,
    symbol: str,
    timeframe: str,
    requested_start: datetime,
    requested_end: datetime,
    failure_reason: str,
    connection_mode: str,
) -> dict[str, Any]:
    return {
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": IBKR_PROVIDER_NAME,
        "connection_mode": connection_mode,
        "read_only": True,
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "symbol": symbol,
        "timeframe": timeframe,
        "latest_candle_timestamp": None,
        "lag_minutes": None,
        "freshness_classification": "unavailable",
        "d11_countable": False,
        "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
        "d11_primary_eligible": False,
        "failure_reason": failure_reason,
        "authority_boundary": IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY,
    }


def _load_ib_insync():
    import ib_insync  # type: ignore[import-not-found]

    return ib_insync


def _duration_string(start: datetime, end: datetime) -> str:
    seconds = max(60, int((end - start).total_seconds()))
    return f"{seconds} S"


def _ibkr_bar_size(timeframe: str) -> str:
    mapping = {
        "1Min": "1 min",
        "5Min": "5 mins",
        "15Min": "15 mins",
        "1Hour": "1 hour",
        "1Day": "1 day",
    }
    if timeframe not in mapping:
        raise ValueError(f"Unsupported IBKR smoke timeframe: {timeframe}")
    return mapping[timeframe]


def _bar_timestamp(bar: Any) -> datetime:
    value = bar.date
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
        description="Local-only IBKR read-only historical market-data smoke."
    )
    parser.add_argument("--symbol", action="append", dest="symbols", required=True)
    parser.add_argument("--timeframe", default="15Min")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--requested-end")
    parser.add_argument("--lookback-minutes", type=int)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7497)
    parser.add_argument("--client-id", type=int, default=9117)
    parser.add_argument("--exchange", default="SMART")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--sec-type", default="STK")
    parser.add_argument("--outside-rth", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument(
        "--authorize-local-ibkr-read-only-smoke",
        action="store_true",
        help="Required before any local IBKR read-only connection attempt.",
    )
    args = parser.parse_args(argv)

    result = build_smoke_result(
        symbols=args.symbols,
        timeframe=args.timeframe,
        limit=args.limit,
        requested_end=_parse_requested_end(args.requested_end),
        lookback_minutes=args.lookback_minutes,
        host=args.host,
        port=args.port,
        client_id=args.client_id,
        exchange=args.exchange,
        currency=args.currency,
        sec_type=args.sec_type,
        outside_rth=args.outside_rth,
        timeout_seconds=args.timeout_seconds,
        authorize_local_ibkr_read_only_smoke=(
            args.authorize_local_ibkr_read_only_smoke
        ),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
