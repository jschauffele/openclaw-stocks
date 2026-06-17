"""Deterministic market-data provider readiness registry.

This module is metadata-only. It does not instantiate providers, read
credentials, call network APIs, touch broker/order state, capture packages,
replay, score, generate candidates, or open Unit 12.
"""

from __future__ import annotations

from dataclasses import dataclass


PROVIDER_ROLE_PRIMARY = "primary"
PROVIDER_ROLE_SECONDARY = "secondary"
PROVIDER_STATUS_PRIMARY = "primary"
PROVIDER_STATUS_SECONDARY = "secondary"
PROVIDER_STATUS_SUSPECT = "suspect"
PROVIDER_STATUS_UNAVAILABLE = "unavailable"
PROVIDER_STATUS_NOT_CONFIGURED = "not_configured"

PROVIDER_STATUS_VOCABULARY: tuple[str, ...] = (
    PROVIDER_STATUS_PRIMARY,
    PROVIDER_STATUS_SECONDARY,
    PROVIDER_STATUS_SUSPECT,
    PROVIDER_STATUS_UNAVAILABLE,
    PROVIDER_STATUS_NOT_CONFIGURED,
)

PROVIDER_REGISTRY_AUTHORITY_BOUNDARY: tuple[str, ...] = (
    "metadata_only",
    "no_credentials",
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

ALPACA_IEX_FRESHNESS_FAILURE_REASON = (
    "explicit-window Alpaca/IEX diagnostic returned 122-167 minute stale "
    "15Min candles across AAPL, MSFT, NVDA, TSLA, and MSTR; records were "
    "recency_caveated and d11_countable=false"
)


@dataclass(frozen=True, slots=True)
class MarketDataProviderRegistryEntry:
    provider_key: str
    provider: str
    feed: str
    provider_role: str
    provider_status: str
    d11_primary_eligible: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "provider": self.provider,
            "feed": self.feed,
            "provider_role": self.provider_role,
            "provider_status": self.provider_status,
            "d11_primary_eligible": self.d11_primary_eligible,
            "reason": self.reason,
        }


_REGISTRY: tuple[MarketDataProviderRegistryEntry, ...] = (
    MarketDataProviderRegistryEntry(
        provider_key="alpaca_iex",
        provider="alpaca",
        feed="iex",
        provider_role=PROVIDER_ROLE_SECONDARY,
        provider_status=PROVIDER_STATUS_SUSPECT,
        d11_primary_eligible=False,
        reason=ALPACA_IEX_FRESHNESS_FAILURE_REASON,
    ),
    MarketDataProviderRegistryEntry(
        provider_key="future_primary",
        provider="future_primary",
        feed="not_configured",
        provider_role=PROVIDER_ROLE_PRIMARY,
        provider_status=PROVIDER_STATUS_NOT_CONFIGURED,
        d11_primary_eligible=False,
        reason="future primary market-data provider slot exists but is not configured",
    ),
)


def list_provider_registry() -> tuple[dict[str, object], ...]:
    return tuple(entry.as_dict() for entry in _REGISTRY)


def get_provider_registry_entry(
    *, provider: str, feed: str | None = None
) -> dict[str, object]:
    normalized_provider = provider.strip().lower()
    normalized_feed = (feed or "").strip().lower()
    for entry in _REGISTRY:
        if entry.provider == normalized_provider and (
            not normalized_feed or entry.feed == normalized_feed
        ):
            return entry.as_dict()
    return MarketDataProviderRegistryEntry(
        provider_key=normalized_provider or "unknown",
        provider=normalized_provider or "unknown",
        feed=normalized_feed or "unknown",
        provider_role=PROVIDER_ROLE_SECONDARY,
        provider_status=PROVIDER_STATUS_UNAVAILABLE,
        d11_primary_eligible=False,
        reason="provider is unavailable in the source-controlled registry",
    ).as_dict()
