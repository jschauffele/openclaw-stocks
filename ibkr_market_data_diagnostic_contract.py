"""Metadata-only IBKR read-only market-data diagnostic contract.

This module defines a future diagnostic contract only. It does not import IBKR
clients, connect to TWS/Gateway, read credentials, request market data, query
account/position/order state, place/cancel/modify orders, capture packages,
replay, score, generate candidates, mutate runtime/systemd/timer state, mark
D11 complete, or open Unit 12.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from market_data import FRESHNESS_CLEAN, MAX_LATEST_CANDLE_LAG_SECONDS
from market_data_provider_selection import (
    CANDIDATE_STATUS_CANDIDATE,
    get_provider_candidate,
)


IBKR_PROVIDER_KEY = "ibkr_market_data_candidate"
IBKR_PROVIDER_NAME = "IBKR read-only market-data diagnostic candidate"
UNIT_12_STATUS_BLOCKED = "UNIT_12_BLOCKED"
D11_STATUS_INSUFFICIENT = "D11_INSUFFICIENT"

IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "metadata_only_contract",
    "read_only_market_data_diagnostic_contract_only",
    "requires_separate_explicit_authorization_before_any_historical_data_request",
    "no_ibkr_client_imports",
    "no_credentials",
    "no_tws_or_gateway_start",
    "no_account_queries",
    "no_position_queries",
    "no_margin_queries",
    "no_buying_power_queries",
    "no_portfolio_queries",
    "no_order_place_modify_cancel_route",
    "no_broker_api_authority",
    "no_order_authority",
    "no_execution_authority",
    "no_runtime_or_systemd_or_timer_mutation",
    "no_package_capture",
    "no_replay",
    "no_scoring",
    "no_candidate_generation",
    "no_unit_12_opening",
    "no_d11_completion_authority",
)

IBKR_DIAGNOSTIC_REQUIRED_OUTPUT_FIELDS: tuple[str, ...] = (
    "provider_key",
    "provider_name",
    "connection_mode",
    "read_only",
    "requested_start",
    "requested_end",
    "symbol",
    "timeframe",
    "latest_candle_timestamp",
    "lag_minutes",
    "freshness_classification",
    "d11_countable",
    "d11_primary_candidate_status",
    "d11_primary_eligible",
    "failure_reason",
    "authority_boundary",
)

IBKR_DIAGNOSTIC_FAIL_CLOSED_RULES: tuple[str, ...] = (
    "missing_timestamps_fail",
    "non_utc_timestamps_fail",
    "stale_latest_candle_fails",
    "warning_bearing_result_fails",
    "account_order_position_capability_detected_fails",
    "unavailable_tws_or_gateway_fails",
    "missing_explicit_request_window_fails",
    "credentials_or_config_not_present_fails",
    "network_or_client_import_in_metadata_contract_fails",
)


@dataclass(frozen=True, slots=True)
class IBKRDiagnosticContractEvaluation:
    valid: bool
    failure_reason: str
    d11_status: str = D11_STATUS_INSUFFICIENT
    unit_12_status: str = UNIT_12_STATUS_BLOCKED
    package_capture: bool = False
    replay: bool = False
    scoring: bool = False
    candidate_generation: bool = False
    broker_api_authority: bool = False
    order_authority: bool = False
    execution_authority: bool = False
    d11_completion_authority: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "failure_reason": self.failure_reason,
            "d11_status": self.d11_status,
            "unit_12_status": self.unit_12_status,
            "package_capture": self.package_capture,
            "replay": self.replay,
            "scoring": self.scoring,
            "candidate_generation": self.candidate_generation,
            "broker_api_authority": self.broker_api_authority,
            "order_authority": self.order_authority,
            "execution_authority": self.execution_authority,
            "d11_completion_authority": self.d11_completion_authority,
            "authority_boundary": IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
        }


def ibkr_read_only_diagnostic_contract() -> dict[str, object]:
    candidate = get_provider_candidate(IBKR_PROVIDER_KEY)
    return {
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": IBKR_PROVIDER_NAME,
        "connection_mode": "not_authorized_not_configured",
        "read_only": True,
        "allowed_action": (
            "historical_market_data_request_only_after_separate_explicit_authorization"
        ),
        "d11_primary_candidate_status": candidate["d11_primary_candidate_status"],
        "d11_primary_eligible": False,
        "required_output_fields": IBKR_DIAGNOSTIC_REQUIRED_OUTPUT_FIELDS,
        "fail_closed_rules": IBKR_DIAGNOSTIC_FAIL_CLOSED_RULES,
        "d11_status": D11_STATUS_INSUFFICIENT,
        "unit_12_status": UNIT_12_STATUS_BLOCKED,
        "authority_boundary": IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    }


def evaluate_ibkr_diagnostic_result(
    result: Mapping[str, Any],
) -> dict[str, object]:
    for field in IBKR_DIAGNOSTIC_REQUIRED_OUTPUT_FIELDS:
        if field not in result:
            return _blocked(f"missing required diagnostic field: {field}")

    if result.get("provider_key") != IBKR_PROVIDER_KEY:
        return _blocked("provider_key is not ibkr_market_data_candidate")
    if result.get("read_only") is not True:
        return _blocked("diagnostic result is not read-only")
    if result.get("connection_mode") not in {"paper_read_only", "gateway_read_only"}:
        return _blocked("unavailable TWS/Gateway or unauthorized connection mode")
    if result.get("account_capability") or result.get("order_capability"):
        return _blocked("account/order/position capability detected")
    if result.get("position_capability") or result.get("portfolio_capability"):
        return _blocked("account/order/position capability detected")
    if result.get("credentials_configured") is not True:
        return _blocked("credentials/config not present")

    requested_start = _parse_utc_timestamp(result.get("requested_start"))
    requested_end = _parse_utc_timestamp(result.get("requested_end"))
    latest_candle = _parse_utc_timestamp(result.get("latest_candle_timestamp"))
    if requested_start is None or requested_end is None:
        return _blocked("missing or non-UTC explicit request window")
    if latest_candle is None:
        return _blocked("missing or non-UTC latest candle timestamp")
    if requested_start >= requested_end:
        return _blocked("requested_start must be before requested_end")

    warnings = result.get("warnings", ())
    if isinstance(warnings, str) or (
        isinstance(warnings, (tuple, list)) and any(str(item) for item in warnings)
    ):
        return _blocked("warning-bearing diagnostic result")

    lag_minutes = result.get("lag_minutes")
    if not isinstance(lag_minutes, int | float):
        return _blocked("missing lag_minutes")
    if lag_minutes * 60 > MAX_LATEST_CANDLE_LAG_SECONDS:
        return _blocked("stale latest candle")
    if result.get("freshness_classification") != FRESHNESS_CLEAN:
        return _blocked("freshness classification is not clean")
    if result.get("d11_countable") is not True:
        return _blocked("diagnostic result is not D11 countable")
    if result.get("d11_primary_candidate_status") != CANDIDATE_STATUS_CANDIDATE:
        return _blocked("candidate status has not been separately governed")
    if result.get("d11_primary_eligible") is True:
        return _blocked("contract cannot mark IBKR primary eligible")

    return _blocked(
        "read-only diagnostic may pass freshness checks, but D11 primary "
        "eligibility requires a later separate governance record"
    )


def _blocked(reason: str) -> dict[str, object]:
    return IBKRDiagnosticContractEvaluation(
        valid=False,
        failure_reason=reason,
    ).as_dict()


def _parse_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("+00:00"):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)
