from __future__ import annotations

import threading
from dataclasses import dataclass
from types import SimpleNamespace

from broker_interface import (
    BrokerAccountState,
    BrokerCapabilities,
    BrokerExecutionSnapshotState,
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


@dataclass(frozen=True, slots=True)
class IBKRMarketOrder:
    symbol: str
    qty: int
    contract: object
    order: object


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
        execution_request_id_start: int = 20001,
        order_id_start: int | None = None,
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
        self._next_execution_request_id = execution_request_id_start
        self._order_id_lock = threading.RLock()
        self._next_order_id = order_id_start
        self._active_order_id: int | None = None

    def get_capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            broker_name="ibkr",
            supports_market_orders=True,
            supports_account_read=True,
            supports_positions_read=True,
            supports_open_orders_read=True,
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
                self.bridge.timeout_position_snapshot()
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

    def get_open_buy_order_qty(
        self,
        symbol: str,
        timeout_seconds: float | None = None,
    ) -> BrokerOpenOrderState:
        client = self._require_open_orders_client()
        timeout = self._normalize_timeout(timeout_seconds)
        generation = self.bridge.begin_open_orders_snapshot(symbol=symbol)

        try:
            client.reqAllOpenOrders()
        except Exception:
            self.bridge.timeout_open_orders_snapshot()
            raise
        if not self.request_coordinator.wait_for_completion(
            generation,
            timeout=timeout,
        ):
            result = self.bridge.timeout_open_orders_snapshot()
            raise TimeoutError(
                "IBKR open-order request timed out: "
                f"generation={generation}, error={result.error}"
            )
        result = self.request_coordinator.result(generation)
        if result is None:
            raise RuntimeError(
                "IBKR open-order request produced no result: "
                f"generation={generation}"
            )
        if isinstance(result, Exception):
            raise result
        return result

    def get_execution_snapshot(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
        since: str | None = None,
        timeout_seconds: float | None = None,
    ) -> BrokerExecutionSnapshotState:
        client = self._require_execution_client()
        timeout = self._normalize_timeout(timeout_seconds)
        request_id = self._allocate_execution_request_id()
        generation = self.bridge.begin_execution_snapshot(
            request_id=request_id,
            symbol=symbol,
        )
        execution_filter = self._build_execution_filter(symbol=symbol, side=side, since=since)

        try:
            client.reqExecutions(request_id, execution_filter)
        except Exception:
            self.bridge.timeout_execution_snapshot()
            raise
        if not self.request_coordinator.wait_for_completion(
            generation,
            timeout=timeout,
        ):
            result = self.bridge.timeout_execution_snapshot()
            raise TimeoutError(
                "IBKR execution request timed out: "
                f"generation={generation}, error={result.error}"
            )
        result = self.request_coordinator.result(generation)
        if result is None:
            raise RuntimeError(
                "IBKR execution request produced no result: "
                f"generation={generation}"
            )
        if isinstance(result, Exception):
            raise result
        return result

    def build_market_order(self, symbol: str, qty: int):
        if self.native_api is None:
            raise NotImplementedError(_SKELETON_MESSAGE)
        if int(qty) == 0:
            raise ValueError("IBKR market order qty must be non-zero")

        contract = self.native_api.contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        order = self.native_api.order()
        order.action = "BUY" if int(qty) > 0 else "SELL"
        order.orderType = "MKT"
        order.totalQuantity = abs(int(qty))
        if hasattr(order, "tif"):
            order.tif = "DAY"
        if hasattr(order, "eTradeOnly"):
            order.eTradeOnly = False
        if hasattr(order, "firmQuoteOnly"):
            order.firmQuoteOnly = False

        return IBKRMarketOrder(
            symbol=symbol,
            qty=int(qty),
            contract=contract,
            order=order,
        )

    def submit_market_order(
        self,
        order,
        timeout_seconds: float | None = None,
    ) -> BrokerOrderResult:
        client = self._require_order_client()
        timeout = self._normalize_timeout(timeout_seconds)
        order_id = self._allocate_and_activate_order_id()
        try:
            self.bridge.begin_order_submission(order_id=order_id)
        except Exception:
            with self._order_id_lock:
                if self._active_order_id == order_id:
                    self._active_order_id = None
            raise
        try:
            contract, native_order = self._extract_native_order_payload(order)
            try:
                client.placeOrder(order_id, contract, native_order)
            except Exception:
                self.bridge.timeout_order_submission(order_id=order_id)
                raise
            if not self.request_coordinator.wait_for_completion(
                order_id,
                timeout=timeout,
            ):
                return self.bridge.timeout_order_submission(order_id=order_id)
            result = self.request_coordinator.result(order_id)
            if result is None:
                raise RuntimeError(
                    "IBKR order submission produced no result: "
                    f"orderId={order_id}"
                )
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            with self._order_id_lock:
                if self._active_order_id == order_id:
                    self._active_order_id = None

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

    def _require_open_orders_client(self):
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        if getattr(client, "reqAllOpenOrders", None) is None:
            raise NotImplementedError(_SKELETON_MESSAGE)
        return client

    def _require_execution_client(self):
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        if getattr(client, "reqExecutions", None) is None:
            raise NotImplementedError(_SKELETON_MESSAGE)
        return client

    def _require_order_client(self):
        client = self.client
        if client is None and self.coordinator is not None:
            client = getattr(self.coordinator, "client", None)
        if getattr(client, "placeOrder", None) is None:
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

    def _allocate_execution_request_id(self) -> int:
        request_id = self._next_execution_request_id
        self._next_execution_request_id += 1
        return request_id

    def _build_execution_filter(
        self,
        *,
        symbol: str | None,
        side: str | None,
        since: str | None,
    ):
        execution_filter_class = getattr(self.native_api, "execution_filter", None)
        execution_filter = (
            execution_filter_class()
            if execution_filter_class is not None
            else SimpleNamespace()
        )
        if symbol is not None:
            execution_filter.symbol = symbol
        if side is not None:
            execution_filter.side = side
        if since is not None:
            execution_filter.time = since
        return execution_filter

    def advance_order_id_floor(self, next_valid_id: object) -> None:
        next_order_id = int(next_valid_id)
        with self._order_id_lock:
            if self._next_order_id is None or self._next_order_id < next_order_id:
                self._next_order_id = next_order_id

    def _allocate_order_id(self) -> int:
        with self._order_id_lock:
            latest_next_valid_id = self.bridge.latest_next_valid_id
            if latest_next_valid_id is not None:
                self.advance_order_id_floor(latest_next_valid_id)
            if self._next_order_id is None:
                raise RuntimeError("IBKR order ID allocator has no nextValidId")
            order_id = self._next_order_id
            self._next_order_id += 1
            return order_id

    def _allocate_and_activate_order_id(self) -> int:
        with self._order_id_lock:
            if self._active_order_id is not None:
                raise RuntimeError("IBKR order placement already active")
            order_id = self._allocate_order_id()
            self._active_order_id = order_id
            return order_id

    def _extract_native_order_payload(self, order) -> tuple[object, object]:
        if isinstance(order, IBKRMarketOrder):
            return order.contract, order.order
        contract = getattr(order, "contract", None)
        native_order = getattr(order, "order", None)
        if contract is not None and native_order is not None:
            return contract, native_order
        raise TypeError("IBKR submit_market_order requires contract and order payload")

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
