from __future__ import annotations

from broker_interface import (
    BrokerAccountState,
    BrokerCapabilities,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_timeout_injector import IBKRTimeoutInjector


_SKELETON_MESSAGE = "IBKR adapter skeleton only; not runtime-enabled"


class IBKRBrokerAdapter:
    def __init__(
        self,
        client=None,
        *,
        native_api=None,
        bridge=None,
        registry=None,
        timeout_injector=None,
        enabled: bool = False,
    ) -> None:
        self.client = client
        self.native_api = native_api
        self.enabled = enabled
        self.registry = registry or IBKRPendingRequestRegistry()
        self.bridge = bridge or IBKRCallbackBridge(self.registry)
        self.timeout_injector = timeout_injector or IBKRTimeoutInjector(
            self.registry
        )

    def get_capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            broker_name="ibkr",
            supports_market_orders=False,
            supports_account_read=False,
            supports_positions_read=False,
            supports_open_orders_read=False,
            supports_paper_trading=True,
            lifecycle_async=True,
        )

    def connect(self, timeout_seconds: float | None = None):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def health_check(self, timeout_seconds: float | None = None):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def disconnect(self, timeout_seconds: float | None = None):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def get_account_buying_power(self) -> BrokerAccountState:
        raise NotImplementedError(_SKELETON_MESSAGE)

    def get_existing_position(self, symbol: str) -> BrokerPositionState:
        raise NotImplementedError(_SKELETON_MESSAGE)

    def get_open_buy_order_qty(self, symbol: str) -> BrokerOpenOrderState:
        raise NotImplementedError(_SKELETON_MESSAGE)

    def build_market_order(self, symbol: str, qty: int):
        raise NotImplementedError(_SKELETON_MESSAGE)

    def submit_market_order(self, order) -> BrokerOrderResult:
        raise NotImplementedError(_SKELETON_MESSAGE)

    def normalize_order_response(self, response) -> BrokerOrderResult:
        raise NotImplementedError(_SKELETON_MESSAGE)
