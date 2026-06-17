"""Metadata-only D11 market-data provider selection criteria.

This module defines candidate metadata and deterministic criteria for a future
D11 primary market-data provider. It does not instantiate providers, read
credentials, call network APIs, capture packages, replay, score, generate
candidates, touch broker/order/execution state, or open Unit 12.
"""

from __future__ import annotations

from dataclasses import dataclass


CANDIDATE_STATUS_CANDIDATE = "candidate"
CANDIDATE_STATUS_ELIGIBLE_FOR_READ_ONLY_DIAGNOSTIC = (
    "eligible_for_read_only_diagnostic"
)
CANDIDATE_STATUS_DIAGNOSTIC_FAILED = "diagnostic_failed"
CANDIDATE_STATUS_DIAGNOSTIC_PASSED = "diagnostic_passed"
CANDIDATE_STATUS_APPROVED_PRIMARY = "approved_primary"
CANDIDATE_STATUS_REJECTED = "rejected"

D11_PRIMARY_CANDIDATE_STATUS_VOCABULARY: tuple[str, ...] = (
    CANDIDATE_STATUS_CANDIDATE,
    CANDIDATE_STATUS_ELIGIBLE_FOR_READ_ONLY_DIAGNOSTIC,
    CANDIDATE_STATUS_DIAGNOSTIC_FAILED,
    CANDIDATE_STATUS_DIAGNOSTIC_PASSED,
    CANDIDATE_STATUS_APPROVED_PRIMARY,
    CANDIDATE_STATUS_REJECTED,
)

D11_PRIMARY_PROVIDER_SELECTION_CRITERIA: tuple[str, ...] = (
    "explicit_request_windows_required",
    "provider_feed_metadata_required",
    "latest_candle_freshness_clean_under_d11_8",
    "target_symbols_supported",
    "timezone_aware_utc_timestamps_required",
    "no_strategy_risk_execution_coupling",
    "no_broker_order_authority_through_data_path",
    "auditable_failure_reasons_required",
    "read_only_diagnostics_required",
    "separate_vps_read_only_freshness_proof_required_before_primary_eligibility",
)

PROVIDER_SELECTION_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "metadata_only",
    "criteria_only",
    "candidate_placeholders_only",
    "no_credentials",
    "no_provider_api_implementation",
    "no_network_api_calls",
    "no_broker_api_authority",
    "no_order_authority",
    "no_execution_authority",
    "no_package_capture",
    "no_replay",
    "no_scoring",
    "no_candidate_generation",
    "no_runtime_work",
    "no_unit_12_opening",
)


@dataclass(frozen=True, slots=True)
class MarketDataProviderCandidate:
    provider_key: str
    provider_name: str
    asset_classes_supported: tuple[str, ...]
    data_type_supported: tuple[str, ...]
    feed_name: str
    auth_required: bool
    credentials_configured: bool
    network_required_for_diagnostic: bool
    broker_coupled: bool
    order_authority: bool
    execution_authority: bool
    d11_primary_candidate_status: str
    d11_primary_eligible: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "provider_name": self.provider_name,
            "asset_classes_supported": self.asset_classes_supported,
            "data_type_supported": self.data_type_supported,
            "feed_name": self.feed_name,
            "auth_required": self.auth_required,
            "credentials_configured": self.credentials_configured,
            "network_required_for_diagnostic": self.network_required_for_diagnostic,
            "broker_coupled": self.broker_coupled,
            "order_authority": self.order_authority,
            "execution_authority": self.execution_authority,
            "d11_primary_candidate_status": self.d11_primary_candidate_status,
            "d11_primary_eligible": self.d11_primary_eligible,
            "reason": self.reason,
        }


_CANDIDATES: tuple[MarketDataProviderCandidate, ...] = (
    MarketDataProviderCandidate(
        provider_key="ibkr_market_data_candidate",
        provider_name="IBKR market data candidate",
        asset_classes_supported=("equities",),
        data_type_supported=("ohlcv_bars",),
        feed_name="not_implemented",
        auth_required=True,
        credentials_configured=False,
        network_required_for_diagnostic=True,
        broker_coupled=True,
        order_authority=False,
        execution_authority=False,
        d11_primary_candidate_status=CANDIDATE_STATUS_CANDIDATE,
        d11_primary_eligible=False,
        reason=(
            "candidate placeholder only; IBKR/TWS/Gateway not opened and no "
            "read-only freshness diagnostic has been authorized or passed"
        ),
    ),
    MarketDataProviderCandidate(
        provider_key="polygon_candidate",
        provider_name="Polygon market data candidate",
        asset_classes_supported=("equities",),
        data_type_supported=("ohlcv_bars",),
        feed_name="not_implemented",
        auth_required=True,
        credentials_configured=False,
        network_required_for_diagnostic=True,
        broker_coupled=False,
        order_authority=False,
        execution_authority=False,
        d11_primary_candidate_status=CANDIDATE_STATUS_CANDIDATE,
        d11_primary_eligible=False,
        reason="candidate placeholder only; credentials are not configured",
    ),
    MarketDataProviderCandidate(
        provider_key="tiingo_candidate",
        provider_name="Tiingo market data candidate",
        asset_classes_supported=("equities",),
        data_type_supported=("ohlcv_bars",),
        feed_name="not_implemented",
        auth_required=True,
        credentials_configured=False,
        network_required_for_diagnostic=True,
        broker_coupled=False,
        order_authority=False,
        execution_authority=False,
        d11_primary_candidate_status=CANDIDATE_STATUS_CANDIDATE,
        d11_primary_eligible=False,
        reason="candidate placeholder only; credentials are not configured",
    ),
    MarketDataProviderCandidate(
        provider_key="schwab_market_data_candidate",
        provider_name="Schwab market data candidate",
        asset_classes_supported=("equities",),
        data_type_supported=("ohlcv_bars",),
        feed_name="not_implemented",
        auth_required=True,
        credentials_configured=False,
        network_required_for_diagnostic=True,
        broker_coupled=True,
        order_authority=False,
        execution_authority=False,
        d11_primary_candidate_status=CANDIDATE_STATUS_CANDIDATE,
        d11_primary_eligible=False,
        reason="candidate placeholder only; credentials are not configured",
    ),
    MarketDataProviderCandidate(
        provider_key="manual_csv_offline_candidate",
        provider_name="Manual CSV offline candidate",
        asset_classes_supported=("equities",),
        data_type_supported=("ohlcv_bars",),
        feed_name="offline_file",
        auth_required=False,
        credentials_configured=False,
        network_required_for_diagnostic=False,
        broker_coupled=False,
        order_authority=False,
        execution_authority=False,
        d11_primary_candidate_status=CANDIDATE_STATUS_CANDIDATE,
        d11_primary_eligible=False,
        reason=(
            "candidate placeholder only; CSV ingestion is not implemented and no "
            "separate read-only diagnostic has passed"
        ),
    ),
)


def list_provider_candidates() -> tuple[dict[str, object], ...]:
    return tuple(candidate.as_dict() for candidate in _CANDIDATES)


def get_provider_candidate(provider_key: str) -> dict[str, object]:
    normalized_key = provider_key.strip().lower()
    for candidate in _CANDIDATES:
        if candidate.provider_key == normalized_key:
            return candidate.as_dict()
    raise KeyError(f"Unknown provider candidate: {provider_key}")


def candidate_can_count_for_d11(candidate: dict[str, object]) -> bool:
    """Return whether a candidate can currently count as D11 primary evidence."""

    return (
        candidate.get("d11_primary_candidate_status")
        == CANDIDATE_STATUS_APPROVED_PRIMARY
        and candidate.get("d11_primary_eligible") is True
        and candidate.get("order_authority") is False
        and candidate.get("execution_authority") is False
        and candidate.get("broker_coupled") is False
    )
