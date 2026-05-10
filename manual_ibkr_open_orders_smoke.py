from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import load_ibkr_native_api
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 9114
DEFAULT_TIMEOUT = 5.0
DEFAULT_SYMBOL = "AAPL"
NON_FATAL_CONNECT_STATUS_CODES = frozenset({2104, 2106, 2158})


@dataclass
class OpenOrdersCallbackRecorder:
    events: list[dict[str, object]] = field(default_factory=list)
    started_at: float = field(default_factory=monotonic)

    def record(self, event_type: str, **fields: object) -> None:
        self.events.append(
            {
                "index": len(self.events) + 1,
                "elapsed_ms": int((monotonic() - self.started_at) * 1000),
                "event_type": event_type,
                **fields,
            }
        )


class RecordingOpenOrdersBridge(IBKRCallbackBridge):
    def __init__(
        self,
        registry: IBKRPendingRequestRegistry,
        *,
        request_coordinator: IBKRRequestCoordinator,
        recorder: OpenOrdersCallbackRecorder,
    ) -> None:
        super().__init__(
            registry,
            request_coordinator=request_coordinator,
        )
        self.recorder = recorder

    def begin_open_orders_snapshot(
        self,
        *,
        symbol: str,
        request_id: object | None = None,
    ) -> int:
        generation = super().begin_open_orders_snapshot(
            symbol=symbol,
            request_id=request_id,
        )
        self.recorder.record(
            "begin_open_orders_snapshot",
            symbol=symbol,
            generation=generation,
        )
        return generation

    def open_order(
        self,
        *,
        order_id: object,
        symbol: str,
        side: str,
        qty: object,
        status: str,
        perm_id: object | None = None,
        request_id: object | None = None,
    ) -> bool:
        routed = super().open_order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            qty=qty,
            status=status,
            perm_id=perm_id,
            request_id=request_id,
        )
        self.recorder.record(
            "openOrder",
            generation=self._active_open_orders_generation,
            order_id=order_id,
            perm_id=perm_id,
            symbol=symbol,
            side=side,
            qty=qty,
            status=status,
            routed=routed,
        )
        return routed

    def open_order_status_update(
        self,
        *,
        order_id: object,
        status: str,
        perm_id: object | None = None,
    ) -> bool:
        routed = super().open_order_status_update(
            order_id=order_id,
            status=status,
            perm_id=perm_id,
        )
        self.recorder.record(
            "orderStatus",
            generation=self._active_open_orders_generation,
            order_id=order_id,
            perm_id=perm_id,
            status=status,
            routed=routed,
        )
        return routed

    def open_order_end(self, *, request_id: object | None = None) -> bool:
        active_before = self._active_open_orders_generation
        routed = super().open_order_end(request_id=request_id)
        self.recorder.record(
            "openOrderEnd",
            generation=active_before,
            routed=routed,
        )
        return routed


class OpenOrdersSmokeWrapper:
    def __init__(
        self,
        *,
        coordinator: IBKRRuntimeArbitrationCoordinator,
        bridge: RecordingOpenOrdersBridge,
        recorder: OpenOrdersCallbackRecorder,
    ) -> None:
        self.coordinator = coordinator
        self.bridge = bridge
        self.recorder = recorder

    def nextValidId(self, order_id) -> bool:
        self.recorder.record("nextValidId", order_id=order_id)
        return self.coordinator.callback_connect_ready(message="next_valid_id")

    def error(self, reqId, code, msg, *args) -> bool:
        self.recorder.record("error", request_id=reqId, code=code, message=str(msg))
        if code in NON_FATAL_CONNECT_STATUS_CODES:
            return False
        return self.coordinator.callback_connect_error(
            message=str(msg),
            retryable=True,
        )

    def openOrder(self, orderId, contract, order, orderState) -> bool:
        return self.bridge.open_order(
            order_id=orderId,
            perm_id=getattr(order, "permId", None),
            symbol=getattr(contract, "symbol", ""),
            side=getattr(order, "action", ""),
            qty=getattr(order, "totalQuantity", "0"),
            status=getattr(orderState, "status", ""),
        )

    def openOrderEnd(self) -> bool:
        return self.bridge.open_order_end()

    def orderStatus(
        self,
        orderId,
        status,
        filled,
        remaining,
        avgFillPrice,
        permId,
        parentId,
        lastFillPrice,
        clientId,
        whyHeld,
        mktCapPrice,
    ) -> bool:
        return self.bridge.open_order_status_update(
            order_id=orderId,
            perm_id=permId,
            status=status,
        )

    def connectAck(self) -> bool:
        self.recorder.record("connectAck")
        return False

    def connectionClosed(self) -> bool:
        self.recorder.record("connectionClosed")
        return False


def build_native_open_orders_wrapper_class(native_wrapper_class):
    class NativeOpenOrdersSmokeWrapper(
        OpenOrdersSmokeWrapper,
        native_wrapper_class,
    ):
        def __init__(
            self,
            *,
            coordinator: IBKRRuntimeArbitrationCoordinator,
            bridge: RecordingOpenOrdersBridge,
            recorder: OpenOrdersCallbackRecorder,
        ) -> None:
            native_wrapper_class.__init__(self)
            OpenOrdersSmokeWrapper.__init__(
                self,
                coordinator=coordinator,
                bridge=bridge,
                recorder=recorder,
            )

    return NativeOpenOrdersSmokeWrapper


class RecordingOpenOrdersClient:
    def __init__(
        self,
        *,
        client,
        recorder: OpenOrdersCallbackRecorder,
    ) -> None:
        self.client = client
        self.recorder = recorder

    def reqAllOpenOrders(self) -> object:
        self.recorder.record("reqAllOpenOrders")
        return self.client.reqAllOpenOrders()

    def __getattr__(self, name: str):
        return getattr(self.client, name)


def run_localhost_open_orders_smoke(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    timeout: float = DEFAULT_TIMEOUT,
    symbol: str = DEFAULT_SYMBOL,
):
    native_api = load_ibkr_native_api()
    recorder = OpenOrdersCallbackRecorder()
    registry = IBKRPendingRequestRegistry()
    request_coordinator = IBKRRequestCoordinator(registry=registry)
    bridge = RecordingOpenOrdersBridge(
        registry,
        request_coordinator=request_coordinator,
        recorder=recorder,
    )
    coordinator = IBKRRuntimeArbitrationCoordinator(enabled=True)
    wrapper_class = build_native_open_orders_wrapper_class(native_api.e_wrapper)
    wrapper = wrapper_class(
        coordinator=coordinator,
        bridge=bridge,
        recorder=recorder,
    )
    native_client = native_api.e_client(wrapper)
    client = RecordingOpenOrdersClient(client=native_client, recorder=recorder)
    coordinator.client = client
    adapter = IBKRBrokerAdapter(
        client=client,
        bridge=bridge,
        registry=registry,
        request_coordinator=request_coordinator,
        coordinator=coordinator,
    )

    print(
        "IBKR manual localhost open-orders smoke "
        f"host={host} port={port} client_id={client_id} symbol={symbol}"
    )
    terminal_result = None
    open_orders_state = None
    open_orders_exception = None
    generation = None

    try:
        coordinator.connect(
            host=host,
            port=port,
            client_id=client_id,
            timeout=timeout,
        )
        if not coordinator.wait_for_completion(timeout=timeout):
            coordinator.timeout_connect(
                message="open-orders smoke timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )
        terminal_result = coordinator.connect_result()
        print(f"terminal_result={terminal_result}")
        print(f"terminal_completion_source={coordinator.completed_by}")

        if terminal_result is None or not terminal_result.passed:
            print("open_orders_skipped=connect_failed")
        else:
            try:
                open_orders_state = adapter.get_open_buy_order_qty(
                    symbol,
                    timeout_seconds=timeout,
                )
                generation = bridge._latest_completed_open_orders_generation
                print(f"generation={generation}")
                print(f"open_orders_state={open_orders_state}")
            except Exception as exc:
                generation = bridge._latest_completed_open_orders_generation
                if generation is None:
                    generation = bridge._active_open_orders_generation
                open_orders_exception = exc
                print(f"generation={generation}")
                print(f"open_orders_exception_type={type(exc).__name__}")
                print(f"open_orders_exception={exc!r}")

        if generation is not None:
            print(f"generation_completion_source={request_coordinator.completed_by(generation)}")
            print(f"retained_result={request_coordinator.result(generation)!r}")
            print(f"pending_request={request_coordinator.has_pending_request(generation)}")
        else:
            print("generation_completion_source=None")
            print("retained_result=None")
            print("pending_request=None")
        print(f"active_generation={bridge._active_open_orders_generation}")
        print(f"latest_completed_generation={bridge._latest_completed_open_orders_generation}")

        if generation is not None:
            late_open_order_routed = bridge.open_order(
                order_id="late-smoke",
                symbol=symbol,
                side="BUY",
                qty="1",
                status="Submitted",
            )
            late_end_routed = bridge.open_order_end()
        else:
            late_open_order_routed = None
            late_end_routed = None
        print(f"late_open_order_routed={late_open_order_routed}")
        print(f"late_open_order_end_routed={late_end_routed}")

        open_order_end_events = [
            event for event in recorder.events if event["event_type"] == "openOrderEnd"
        ]
        print(f"open_order_end_arrived={bool(open_order_end_events)}")
        print(f"callback_count={len(recorder.events)}")
        for event in recorder.events:
            print(f"callback_event={event}")
        return open_orders_state
    finally:
        joined = coordinator.disconnect(timeout=timeout)
        print(f"disconnect_joined={joined}")
        print(f"disconnect_result={coordinator.disconnect_result()}")
        print(f"connect_state={coordinator.connect_state}")
        print(f"shutdown_state={coordinator.shutdown_state}")
        print(f"thread_state={coordinator.thread_owner.thread_state}")


if __name__ == "__main__":
    run_localhost_open_orders_smoke()
