from __future__ import annotations

from broker_interface import (
    BrokerAccountState,
    BrokerCapabilities,
    BrokerLifecycleResult,
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
        coordinator=None,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 9107,
        enabled: bool = False,
    ) -> None:
        self.client = client
        self.native_api = native_api
        self.enabled = enabled
        self.coordinator = coordinator
        self.host = host
        self.port = port
        self.client_id = client_id
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

    def connect(
        self,
        timeout_seconds: float | None = None,
    ) -> BrokerLifecycleResult:
        coordinator = self._require_coordinator()
        timeout = self._normalize_timeout(timeout_seconds)
        coordinator.connect(
            host=self.host,
            port=self.port,
            client_id=self.client_id,
            timeout=timeout,
        )
        if not coordinator.wait_for_completion(timeout=timeout):
            coordinator.timeout_connect(
                message="IBKR adapter timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )
        result = coordinator.connect_result()
        if result is None:
            return BrokerLifecycleResult(
                broker_name="ibkr",
                operation="connect",
                passed=False,
                reason="connect_result_missing",
                message="IBKR coordinator did not produce a connect result",
                connected=False,
                retryable=True,
                elapsed_ms=None,
                raw_error=None,
            )
        return result

    def health_check(
        self,
        timeout_seconds: float | None = None,
    ) -> BrokerLifecycleResult:
        connected = bool(self._client_is_connected())
        if connected:
            return BrokerLifecycleResult(
                broker_name="ibkr",
                operation="health_check",
                passed=True,
                reason="ibkr_client_connected",
                message="IBKR client reports connected",
                connected=True,
                retryable=False,
                elapsed_ms=0,
                raw_error=None,
            )
        return BrokerLifecycleResult(
            broker_name="ibkr",
            operation="health_check",
            passed=False,
            reason="ibkr_client_disconnected",
            message="IBKR client reports disconnected",
            connected=False,
            retryable=True,
            elapsed_ms=0,
            raw_error=None,
        )

    def disconnect(
        self,
        timeout_seconds: float | None = None,
    ) -> BrokerLifecycleResult:
        coordinator = self._require_coordinator()
        timeout = self._normalize_timeout(timeout_seconds)
        joined = coordinator.disconnect(timeout=timeout)
        result = coordinator.disconnect_result()
        if result is not None:
            return result
        return BrokerLifecycleResult(
            broker_name="ibkr",
            operation="disconnect",
            passed=joined,
            reason="disconnect_complete" if joined else "runtime_thread_join_timeout",
            message=(
                "IBKR runtime disconnected"
                if joined
                else "IBKR runtime thread did not stop before join timeout"
            ),
            connected=False,
            retryable=not joined,
            elapsed_ms=None,
            raw_error=None,
        )

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

    def _require_coordinator(self):
        if self.coordinator is None:
            raise NotImplementedError(_SKELETON_MESSAGE)
        return self.coordinator

    def _client_is_connected(self) -> bool:
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        is_connected = getattr(client, "isConnected", None)
        if is_connected is None:
            return False
        return bool(is_connected())

    def _normalize_timeout(self, timeout_seconds: float | None) -> float:
        if timeout_seconds is None:
            return 5.0
        return timeout_seconds
