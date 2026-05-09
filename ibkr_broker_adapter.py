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
from ibkr_request_coordinator import IBKRRequestCoordinator
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
        request_coordinator=None,
        coordinator=None,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 9107,
        enabled: bool = False,
        account_summary_group: str = "All",
        account_summary_tags: str = "BuyingPower",
        account_summary_request_id_start: int = 1,
        position_account: str = "",
        position_model_code: str = "",
        position_request_id_start: int = 10001,
    ) -> None:
        self.client = client
        self.native_api = native_api
        self.enabled = enabled
        self.coordinator = coordinator
        self.host = host
        self.port = port
        self.client_id = client_id
        self.registry = registry or IBKRPendingRequestRegistry()
        self.request_coordinator = request_coordinator or IBKRRequestCoordinator(
            registry=self.registry
        )
        self.bridge = bridge or IBKRCallbackBridge(
            self.registry,
            request_coordinator=self.request_coordinator,
        )
        self.timeout_injector = timeout_injector or IBKRTimeoutInjector(
            self.registry
        )
        self.account_summary_group = account_summary_group
        self.account_summary_tags = account_summary_tags
        self._next_account_summary_request_id = account_summary_request_id_start
        self.position_account = position_account
        self.position_model_code = position_model_code
        self._next_position_request_id = position_request_id_start

    def get_capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            broker_name="ibkr",
            supports_market_orders=False,
            supports_account_read=True,
            supports_positions_read=True,
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

    def get_account_buying_power(
        self,
        timeout_seconds: float | None = None,
    ) -> BrokerAccountState:
        client = self._require_account_summary_client()
        timeout = self._normalize_timeout(timeout_seconds)
        request_id = self._allocate_account_summary_request_id()

        self.bridge.begin_account_snapshot(request_id=request_id)
        try:
            client.reqAccountSummary(
                request_id,
                self.account_summary_group,
                self.account_summary_tags,
            )
            if not self.request_coordinator.wait_for_completion(
                request_id,
                timeout=timeout,
            ):
                self.request_coordinator.timeout_request(request_id)
                raise TimeoutError(
                    f"IBKR account summary request timed out: reqId={request_id}"
                )
            result = self.request_coordinator.result(request_id)
            if result is None:
                raise RuntimeError(
                    f"IBKR account summary request produced no result: reqId={request_id}"
                )
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            self._cancel_account_summary(request_id)

    def get_existing_position(
        self,
        symbol: str,
        timeout_seconds: float | None = None,
    ) -> BrokerPositionState:
        client = self._require_position_client()
        timeout = self._normalize_timeout(timeout_seconds)
        request_id = self._allocate_position_request_id()

        self.bridge.begin_position_snapshot(request_id=request_id, symbol=symbol)
        try:
            client.reqPositionsMulti(
                request_id,
                self.position_account,
                self.position_model_code,
            )
            if not self.request_coordinator.wait_for_completion(
                request_id,
                timeout=timeout,
            ):
                self.request_coordinator.timeout_request(request_id)
                raise TimeoutError(
                    f"IBKR position request timed out: reqId={request_id}"
                )
            result = self.request_coordinator.result(request_id)
            if result is None:
                raise RuntimeError(
                    f"IBKR position request produced no result: reqId={request_id}"
                )
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            self._cancel_positions_multi(request_id)

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

    def _require_account_summary_client(self):
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        if getattr(client, "reqAccountSummary", None) is None:
            raise NotImplementedError(_SKELETON_MESSAGE)
        return client

    def _require_position_client(self):
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        if getattr(client, "reqPositionsMulti", None) is None:
            raise NotImplementedError(_SKELETON_MESSAGE)
        return client

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

    def _allocate_account_summary_request_id(self) -> int:
        request_id = self._next_account_summary_request_id
        self._next_account_summary_request_id += 1
        return request_id

    def _allocate_position_request_id(self) -> int:
        request_id = self._next_position_request_id
        self._next_position_request_id += 1
        return request_id

    def _cancel_account_summary(self, request_id: object) -> None:
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        cancel = getattr(client, "cancelAccountSummary", None)
        if cancel is not None:
            cancel(request_id)

    def _cancel_positions_multi(self, request_id: object) -> None:
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        cancel = getattr(client, "cancelPositionsMulti", None)
        if cancel is not None:
            cancel(request_id)
