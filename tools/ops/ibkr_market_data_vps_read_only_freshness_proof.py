"""VPS-only, read-only IBKR historical-market-data freshness proof.

The command is inert unless its explicit authorization flag is supplied.  It
does not read credentials, start TWS/Gateway, access account state, submit or
manage orders, write packages, or mutate VPS runtime state.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ibkr_market_data_diagnostic_contract import (
    D11_STATUS_INSUFFICIENT,
    IBKR_PROVIDER_KEY,
    IBKR_PROVIDER_NAME,
    UNIT_12_STATUS_BLOCKED,
)
from market_data import classify_market_data_freshness, compute_request_window
from market_data_provider_selection import CANDIDATE_STATUS_CANDIDATE


VPS_REPO_ROOT = "/opt/openclaw-stocks"
VPS_EXECUTION_CONTEXT = "VPS"
VPS_DIAGNOSTIC_DEPENDENCY_CONTRACT = "requirements-diagnostics.txt / ib_insync==0.9.86"
VPS_DIAGNOSTIC_DEPENDENCY_VERSION = "0.9.86"
VPS_READ_ONLY_PROOF_RESULT_TYPE = "ibkr_vps_read_only_market_data_freshness_proof"
VPS_READ_ONLY_PROOF_CONNECTION_MODE = "vps_read_only_historical_market_data"
VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "vps_only",
    "explicit_cli_authorization_required",
    "historical_market_data_only",
    "no_credentials_read",
    "no_tws_gateway_start",
    "no_account_query",
    "no_position_query",
    "no_margin_query",
    "no_buying_power_query",
    "no_portfolio_query",
    "no_order_query",
    "no_balance_query",
    "no_execution_query",
    "no_order_placement",
    "no_order_modification",
    "no_order_routing",
    "no_order_cancellation",
    "no_cleanup",
    "no_flatten",
    "no_sell",
    "no_live_trading",
    "no_package_capture",
    "no_replay",
    "no_scoring",
    "no_candidate_generation",
    "no_timer_service_systemd_runtime_mutation",
    "no_strategy_risk_execution_behavior_change",
    "no_d11_completion",
    "no_unit_12_opening",
)

RepoStateInspector = Callable[[str], Mapping[str, object]]
DependencyLoader = Callable[[], Any]
HistoricalFetcher = Callable[..., datetime]


def build_vps_read_only_freshness_proof(
    *,
    repo_root: str,
    expected_source_commit: str,
    execution_context: str,
    symbols: Iterable[str],
    timeframe: str,
    requested_end: datetime,
    lookback_minutes: int,
    host: str,
    port: int,
    client_id: int,
    exchange: str,
    currency: str,
    sec_type: str,
    timeout_seconds: float,
    authorize_vps_ibkr_read_only_freshness_proof: bool = False,
    repo_state_inspector: RepoStateInspector | None = None,
    ibkr_dependency_loader: DependencyLoader | None = None,
    historical_fetcher: HistoricalFetcher | None = None,
) -> dict[str, Any]:
    """Build one fail-closed VPS proof result without changing provider status."""

    normalized_symbols = tuple(symbol.strip().upper() for symbol in symbols if symbol.strip())
    result = _base_result(
        repo_root=repo_root,
        expected_source_commit=expected_source_commit,
        execution_context=execution_context,
        symbols=normalized_symbols,
        timeframe=timeframe,
        requested_end=requested_end,
        lookback_minutes=lookback_minutes,
    )
    failure = _validate_request(
        repo_root=repo_root,
        expected_source_commit=expected_source_commit,
        execution_context=execution_context,
        symbols=normalized_symbols,
        timeframe=timeframe,
        requested_end=requested_end,
        lookback_minutes=lookback_minutes,
        exchange=exchange,
        currency=currency,
        sec_type=sec_type,
        timeout_seconds=timeout_seconds,
    )
    if failure:
        return _blocked_result(result, failure)
    if not authorize_vps_ibkr_read_only_freshness_proof:
        return _blocked_result(
            result,
            "explicit --authorize-vps-ibkr-read-only-freshness-proof flag required",
        )

    inspect = repo_state_inspector or _inspect_repo_state
    before = inspect(repo_root)
    result.update(_state_fields(before, "before"))
    if before.get("branch") != "main":
        return _blocked_result(result, "branch is not main")
    if before.get("observed_head") != expected_source_commit:
        return _blocked_result(result, "observed commit does not match expected commit")
    if before.get("worktree_status") != "clean":
        return _blocked_result(result, "worktree is not clean before proof")
    if not _pinned_dependency_contract_present(repo_root):
        return _blocked_result(result, "requirements-diagnostics.txt does not match pinned contract")

    try:
        dependency = (ibkr_dependency_loader or _load_ib_insync)()
    except ImportError:
        return _blocked_result(result, "ib_insync dependency unavailable")
    if str(getattr(dependency, "__version__", "")) != VPS_DIAGNOSTIC_DEPENDENCY_VERSION:
        return _blocked_result(result, "ib_insync dependency version does not match pinned contract")
    result["observed_dependency"] = f"ib_insync=={dependency.__version__}"

    requested_start, normalized_end = compute_request_window(
        timeframe=timeframe,
        limit=5,
        requested_end=requested_end,
        lookback_minutes=lookback_minutes,
    )
    result["requested_start"] = requested_start.isoformat()
    result["requested_end"] = normalized_end.isoformat()
    fetch = historical_fetcher or _fetch_historical_latest_timestamp
    rows: list[dict[str, Any]] = []
    for symbol in normalized_symbols:
        try:
            latest = fetch(
                dependency=dependency,
                symbol=symbol,
                requested_start=requested_start,
                requested_end=normalized_end,
                host=host,
                port=port,
                client_id=client_id,
                exchange=exchange,
                currency=currency,
                sec_type=sec_type,
                timeout_seconds=timeout_seconds,
            )
            freshness = classify_market_data_freshness(
                latest_candle_timestamp=latest,
                run_timestamp=normalized_end,
                warnings=(),
            )
            rows.append(
                _row(
                    symbol=symbol,
                    timeframe=timeframe,
                    requested_start=requested_start,
                    requested_end=normalized_end,
                    latest=freshness.latest_candle_timestamp,
                    lag=freshness.lag_minutes,
                    freshness_classification=freshness.freshness_classification,
                    countable=freshness.d11_countable,
                    failure_reason=freshness.warning_reason,
                )
            )
        except Exception as exc:  # noqa: BLE001 - proof must fail closed.
            rows.append(
                _row(
                    symbol=symbol,
                    timeframe=timeframe,
                    requested_start=requested_start,
                    requested_end=normalized_end,
                    latest=None,
                    lag=None,
                    freshness_classification="unavailable",
                    countable=False,
                    failure_reason=f"historical read-only request failed: {type(exc).__name__}",
                )
            )

    after = inspect(repo_root)
    result.update(_state_fields(after, "after"))
    result["results"] = tuple(rows)
    result["vps_freshness_proof_run"] = True
    if after.get("branch") != "main" or after.get("observed_head") != expected_source_commit:
        return _blocked_result(result, "branch or commit changed during proof")
    if after.get("worktree_status") != "clean":
        return _blocked_result(result, "worktree is not clean after proof")
    result["failure_reason"] = ""
    return result


def _base_result(**kwargs: Any) -> dict[str, Any]:
    return {
        "result_type": VPS_READ_ONLY_PROOF_RESULT_TYPE,
        "execution_context": kwargs["execution_context"],
        "repo_root": kwargs["repo_root"],
        "expected_source_commit": kwargs["expected_source_commit"],
        "observed_head": None,
        "branch": None,
        "worktree_status_before_run": None,
        "worktree_status_after_run": None,
        "dependency_contract": VPS_DIAGNOSTIC_DEPENDENCY_CONTRACT,
        "observed_dependency": None,
        "credential_configuration_status": "operator_managed_tws_gateway_session_attested",
        "credentials_stored_in_repository": False,
        "credential_values_emitted": False,
        "secrets_captured": False,
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": IBKR_PROVIDER_NAME,
        "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
        "d11_primary_eligible": False,
        "connection_mode": VPS_READ_ONLY_PROOF_CONNECTION_MODE,
        "read_only": True,
        "symbols": kwargs["symbols"],
        "timeframe": kwargs["timeframe"],
        "requested_start": None,
        "requested_end": kwargs["requested_end"].isoformat(),
        "lookback_minutes": kwargs["lookback_minutes"],
        "warnings": (),
        "results": (),
        "vps_freshness_proof_run": False,
        "failure_reason": None,
        "ibkr_primary_eligibility": "NOT_APPROVED",
        "d11_status": D11_STATUS_INSUFFICIENT,
        "unit_12_status": UNIT_12_STATUS_BLOCKED,
        "vps_runtime": "NOT_TOUCHED",
        "timer_service": "NOT_TOUCHED",
        "package_capture": False,
        "replay": False,
        "scoring": False,
        "candidate_generation": False,
        "broker_api_authority": False,
        "account_query_authority": False,
        "order_authority": False,
        "execution_authority": False,
        "cleanup_authority": False,
        "flatten_authority": False,
        "sell_authority": False,
        "cancel_authority": False,
        "live_trading_authority": False,
        "d11_completion_authority": False,
        "authority_boundary": VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY,
    }


def _validate_request(**kwargs: Any) -> str | None:
    if kwargs["execution_context"] != VPS_EXECUTION_CONTEXT:
        return "execution_context must be VPS"
    if kwargs["repo_root"] != VPS_REPO_ROOT:
        return f"repo_root must be {VPS_REPO_ROOT}"
    if not re.fullmatch(r"[0-9a-f]{40}", kwargs["expected_source_commit"]):
        return "expected_source_commit must be a 40-character lowercase hex commit"
    if not kwargs["symbols"]:
        return "at least one symbol is required"
    if kwargs["timeframe"] != "15Min":
        return "timeframe must be 15Min"
    if kwargs["lookback_minutes"] != 120:
        return "lookback_minutes must be 120"
    if kwargs["timeout_seconds"] != 10:
        return "timeout_seconds must be 10"
    if kwargs["requested_end"].tzinfo is None or kwargs["requested_end"].utcoffset() is None:
        return "requested_end must be timezone-aware UTC"
    if kwargs["requested_end"].astimezone(timezone.utc) != kwargs["requested_end"]:
        return "requested_end must be UTC"
    if (kwargs["exchange"], kwargs["currency"], kwargs["sec_type"]) != ("SMART", "USD", "STK"):
        return "exchange, currency, and sec_type must be SMART, USD, and STK"
    return None


def _blocked_result(result: dict[str, Any], reason: str) -> dict[str, Any]:
    result["failure_reason"] = reason
    return result


def _state_fields(state: Mapping[str, object], suffix: str) -> dict[str, object]:
    fields: dict[str, object] = {}
    if suffix == "before":
        fields["branch"] = state.get("branch")
        fields["observed_head"] = state.get("observed_head")
        fields["worktree_status_before_run"] = state.get("worktree_status")
    else:
        fields["branch_after_run"] = state.get("branch")
        fields["observed_head_after_run"] = state.get("observed_head")
        fields["worktree_status_after_run"] = state.get("worktree_status")
    return fields


def _row(**kwargs: Any) -> dict[str, Any]:
    return {
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": IBKR_PROVIDER_NAME,
        "connection_mode": VPS_READ_ONLY_PROOF_CONNECTION_MODE,
        "read_only": True,
        "requested_start": kwargs["requested_start"].isoformat(),
        "requested_end": kwargs["requested_end"].isoformat(),
        "symbol": kwargs["symbol"],
        "timeframe": kwargs["timeframe"],
        "latest_candle_timestamp": _iso_timestamp_or_none(kwargs["latest"]),
        "lag_minutes": kwargs["lag"],
        "freshness_classification": kwargs["freshness_classification"],
        "d11_countable": kwargs["countable"],
        "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
        "d11_primary_eligible": False,
        "failure_reason": kwargs["failure_reason"],
        "warnings": (),
        "authority_boundary": VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY,
    }


def _iso_timestamp_or_none(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return normalized.isoformat()
    return value


def _inspect_repo_state(repo_root: str) -> dict[str, str]:
    return {
        "branch": _git(repo_root, "branch", "--show-current"),
        "observed_head": _git(repo_root, "rev-parse", "HEAD"),
        "worktree_status": "clean" if not _git(repo_root, "status", "--short") else "dirty",
    }


def _pinned_dependency_contract_present(repo_root: str) -> bool:
    try:
        return (
            (Path(repo_root) / "requirements-diagnostics.txt").read_text(
                encoding="utf-8"
            ).splitlines()
            == [f"ib_insync=={VPS_DIAGNOSTIC_DEPENDENCY_VERSION}"]
        )
    except OSError:
        return False


def _git(repo_root: str, *args: str) -> str:
    return subprocess.run(
        ("git", "-C", repo_root, *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def _load_ib_insync() -> Any:
    import ib_insync  # type: ignore[import-not-found]

    return ib_insync


def _fetch_historical_latest_timestamp(**kwargs: Any) -> datetime:
    dependency = kwargs["dependency"]
    client = dependency.IB()
    try:
        client.connect(kwargs["host"], kwargs["port"], clientId=kwargs["client_id"], timeout=kwargs["timeout_seconds"])
        contract = dependency.Contract()
        contract.symbol = kwargs["symbol"]
        contract.secType = kwargs["sec_type"]
        contract.exchange = kwargs["exchange"]
        contract.currency = kwargs["currency"]
        bars = client.reqHistoricalData(
            contract,
            endDateTime=kwargs["requested_end"],
            durationStr=f"{max(60, int((kwargs['requested_end'] - kwargs['requested_start']).total_seconds()))} S",
            barSizeSetting="15 mins",
            whatToShow="TRADES",
            useRTH=1,
            formatDate=2,
            keepUpToDate=False,
        )
        if not bars:
            raise RuntimeError("no historical bars returned")
        value = bars[-1].date
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    finally:
        if client.isConnected():
            client.disconnect()


def _parse_utc_z(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("--requested-end must be a UTC Z timestamp")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("--requested-end must be timezone-aware UTC")
    return parsed.astimezone(timezone.utc)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VPS-only IBKR read-only historical freshness proof.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--execution-context", required=True)
    parser.add_argument("--symbol", action="append", dest="symbols", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--requested-end", required=True)
    parser.add_argument("--lookback-minutes", type=int, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--client-id", type=int, required=True)
    parser.add_argument("--exchange", required=True)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--sec-type", required=True)
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--authorize-vps-ibkr-read-only-freshness-proof", action="store_true")
    args = parser.parse_args(argv)
    result = build_vps_read_only_freshness_proof(
        repo_root=args.repo_root,
        expected_source_commit=args.expected_source_commit,
        execution_context=args.execution_context,
        symbols=args.symbols,
        timeframe=args.timeframe,
        requested_end=_parse_utc_z(args.requested_end),
        lookback_minutes=args.lookback_minutes,
        host=args.host,
        port=args.port,
        client_id=args.client_id,
        exchange=args.exchange,
        currency=args.currency,
        sec_type=args.sec_type,
        timeout_seconds=args.timeout_seconds,
        authorize_vps_ibkr_read_only_freshness_proof=args.authorize_vps_ibkr_read_only_freshness_proof,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
