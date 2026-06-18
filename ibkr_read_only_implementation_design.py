"""Metadata-only IBKR read-only implementation design gate.

This module defines the future implementation contract for a separately
authorized IBKR historical market-data diagnostic. It does not import IBKR
clients, open connections, read credentials, start TWS/Gateway, query account or
order state, capture packages, replay, score, generate candidates, mark D11
complete, or open Unit 12.
"""

from __future__ import annotations

from dataclasses import dataclass

from ibkr_market_data_diagnostic_contract import (
    D11_STATUS_INSUFFICIENT,
    IBKR_DIAGNOSTIC_REQUIRED_OUTPUT_FIELDS,
    IBKR_PROVIDER_KEY,
    UNIT_12_STATUS_BLOCKED,
)


DESIGN_STATUS_DESIGN_ONLY = "design_only"
DESIGN_STATUS_AWAITING_LOCAL_AUTHORIZATION = "awaiting_local_authorization"
DESIGN_STATUS_AWAITING_MANUAL_TWS_GATEWAY = "awaiting_manual_tws_gateway"
DESIGN_STATUS_AWAITING_CREDENTIALS_CONFIGURATION = (
    "awaiting_credentials_configuration"
)
DESIGN_STATUS_READY_FOR_LOCAL_READ_ONLY_SMOKE = "ready_for_local_read_only_smoke"
DESIGN_STATUS_REJECTED = "rejected"

IBKR_READ_ONLY_IMPLEMENTATION_DESIGN_STATUSES: tuple[str, ...] = (
    DESIGN_STATUS_DESIGN_ONLY,
    DESIGN_STATUS_AWAITING_LOCAL_AUTHORIZATION,
    DESIGN_STATUS_AWAITING_MANUAL_TWS_GATEWAY,
    DESIGN_STATUS_AWAITING_CREDENTIALS_CONFIGURATION,
    DESIGN_STATUS_READY_FOR_LOCAL_READ_ONLY_SMOKE,
    DESIGN_STATUS_REJECTED,
)

IBKR_READ_ONLY_IMPLEMENTATION_REQUIREMENTS: tuple[str, ...] = (
    "explicit_operator_authorization_required",
    "local_only_first_implementation",
    "tws_or_gateway_must_already_be_running_manually",
    "code_must_not_start_tws_or_gateway",
    "credentials_must_not_be_stored_in_repo",
    "design_module_must_not_read_credentials",
    "read_only_historical_market_data_only",
    "account_position_margin_buying_power_portfolio_order_endpoints_prohibited",
    "order_place_modify_cancel_route_prohibited",
    "output_must_conform_to_d11_12_diagnostic_contract",
    "clean_d11_8_freshness_proof_required_before_primary_eligibility",
    "design_gate_cannot_mark_d11_complete",
    "unit_12_remains_blocked",
)

IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "metadata_only_design",
    "no_ibkr_client_imports",
    "no_socket_or_network_client_code",
    "no_connection_code",
    "no_credentials_read",
    "no_tws_gateway_start",
    "no_account_query",
    "no_position_query",
    "no_margin_query",
    "no_buying_power_query",
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

IBKR_CONNECTION_CONFIG_CONTRACT_FIELDS: tuple[str, ...] = (
    "host",
    "port",
    "client_id",
    "readonly_mode",
    "connection_mode",
    "market_data_type",
    "timeout_seconds",
    "symbols",
    "timeframe",
    "requested_start",
    "requested_end",
    "outside_rth",
    "exchange",
    "currency",
    "sec_type",
)


@dataclass(frozen=True, slots=True)
class IBKRReadOnlyImplementationDesign:
    provider_key: str
    design_status: str
    d11_status: str
    unit_12_status: str
    d11_primary_eligible: bool
    broker_api_authority: bool
    order_authority: bool
    execution_authority: bool
    package_capture: bool
    replay: bool
    scoring: bool
    candidate_generation: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "design_status": self.design_status,
            "d11_status": self.d11_status,
            "unit_12_status": self.unit_12_status,
            "d11_primary_eligible": self.d11_primary_eligible,
            "broker_api_authority": self.broker_api_authority,
            "order_authority": self.order_authority,
            "execution_authority": self.execution_authority,
            "package_capture": self.package_capture,
            "replay": self.replay,
            "scoring": self.scoring,
            "candidate_generation": self.candidate_generation,
            "requirements": IBKR_READ_ONLY_IMPLEMENTATION_REQUIREMENTS,
            "implementation_requirements": IBKR_READ_ONLY_IMPLEMENTATION_REQUIREMENTS,
            "config_contract_fields": IBKR_CONNECTION_CONFIG_CONTRACT_FIELDS,
            "future_connection_config_contract": (
                IBKR_CONNECTION_CONFIG_CONTRACT_FIELDS
            ),
            "diagnostic_output_fields": IBKR_DIAGNOSTIC_REQUIRED_OUTPUT_FIELDS,
            "status_vocabulary": IBKR_READ_ONLY_IMPLEMENTATION_DESIGN_STATUSES,
            "authority_boundary": IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY,
            "credentials_read": False,
            "connection_opened": False,
            "tws_gateway_started": False,
            "account_query_authority": False,
            "position_query_authority": False,
            "margin_query_authority": False,
            "buying_power_query_authority": False,
            "portfolio_query_authority": False,
        }


def ibkr_read_only_implementation_design() -> dict[str, object]:
    return IBKRReadOnlyImplementationDesign(
        provider_key=IBKR_PROVIDER_KEY,
        design_status=DESIGN_STATUS_DESIGN_ONLY,
        d11_status=D11_STATUS_INSUFFICIENT,
        unit_12_status=UNIT_12_STATUS_BLOCKED,
        d11_primary_eligible=False,
        broker_api_authority=False,
        order_authority=False,
        execution_authority=False,
        package_capture=False,
        replay=False,
        scoring=False,
        candidate_generation=False,
    ).as_dict()
