from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
import time

from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import load_ibkr_native_api
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 9115
DEFAULT_TIMEOUT = 15.0
DEFAULT_SYMBOL = "AAPL"
DEFAULT_QTY = 1
NON_FATAL_CONNECT_STATUS_CODES = frozenset({2104, 2106, 2158})
RUN_THREAD_READY_TIMEOUT = 2.0


@dataclass
class SubmitAckCallbackRecorder:
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


class RecordingSubmitAckBridge(IBKRCallbackBridge):
    def __init__(
        self,
        registry: IBKRPendingRequestRegistry,
        *,
        request_coordinator: IBKRRequestCoordinator,
        recorder: SubmitAckCallbackRecorder,
    ) -> None:
        super().__init__(
            registry,
            request_coordinator=request_coordinator,
        )
        self.recorder = recorder

    def begin_order_submission(self, *, order_id: object) -> None:
        result = super().begin_order_submission(order_id=order_id)
        self.recorder.record(
            "begin_order_submission",
            order_id=order_id,
            pending=self.request_coordinator.has_pending_request(order_id),
        )
        return result

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
            order_id=order_id,
            perm_id=perm_id,
            symbol=symbol,
            side=side,
            qty=qty,
            status=status,
            routed=routed,
        )
        return routed

    def order_status(self, *, order_id: object, status: str) -> bool:
        routed = super().order_status(order_id=order_id, status=status)
        self.recorder.record(
            "orderStatus",
            order_id=order_id,
            status=status,
            routed=routed,
            route_method="order_status_submit_lifecycle",
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
            order_id=order_id,
            perm_id=perm_id,
            status=status,
            routed=routed,
            route_method="open_order_status_update",
        )
        return routed

    def timeout_order_submission(self, *, order_id: object):
        result = super().timeout_order_submission(order_id=order_id)
        self.recorder.record(
            "timeout_order_submission",
            order_id=order_id,
            result=result,
        )
        return result


class SubmitAckSmokeWrapper:
    def __init__(
        self,
        *,
        coordinator: IBKRRuntimeArbitrationCoordinator,
        bridge: RecordingSubmitAckBridge,
        recorder: SubmitAckCallbackRecorder,
    ) -> None:
        self.coordinator = coordinator
        self.bridge = bridge
        self.recorder = recorder

    def nextValidId(self, order_id) -> bool:
        self.recorder.record("nextValidId", order_id=order_id)
        self.bridge.next_valid_id(order_id=order_id)
        return self.coordinator.callback_connect_ready(message="next_valid_id")

    def error(self, reqId, code, msg, *args) -> bool:
        self.recorder.record("error", request_id=reqId, code=code, message=str(msg))
        if self.bridge.order_error(
            order_id=reqId,
            code=code,
            message=str(msg),
            advanced_order_reject_json=args[0] if args else None,
        ):
            return True
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
        return self.bridge.order_status(
            order_id=orderId,
            status=status,
        )

    def connectAck(self) -> bool:
        self.recorder.record("connectAck")
        return False

    def connectionClosed(self) -> bool:
        self.recorder.record("connectionClosed")
        return False


def build_native_submit_ack_wrapper_class(native_wrapper_class):
    class NativeSubmitAckSmokeWrapper(
        SubmitAckSmokeWrapper,
        native_wrapper_class,
    ):
        def __init__(
            self,
            *,
            coordinator: IBKRRuntimeArbitrationCoordinator,
            bridge: RecordingSubmitAckBridge,
            recorder: SubmitAckCallbackRecorder,
        ) -> None:
            native_wrapper_class.__init__(self)
            SubmitAckSmokeWrapper.__init__(
                self,
                coordinator=coordinator,
                bridge=bridge,
                recorder=recorder,
            )

    return NativeSubmitAckSmokeWrapper


class RecordingSubmitAckClient:
    def __init__(
        self,
        *,
        client,
        request_coordinator: IBKRRequestCoordinator,
        recorder: SubmitAckCallbackRecorder,
    ) -> None:
        self.client = client
        self.request_coordinator = request_coordinator
        self.recorder = recorder

    def placeOrder(self, order_id, contract, order) -> object:
        pending_before = self.request_coordinator.has_pending_request(order_id)
        self.recorder.record(
            "placeOrder",
            order_id=order_id,
            symbol=getattr(contract, "symbol", ""),
            side=getattr(order, "action", ""),
            qty=getattr(order, "totalQuantity", None),
            order_type=getattr(order, "orderType", ""),
            pending_before_place_order=pending_before,
        )
        return self.client.placeOrder(order_id, contract, order)

    def __getattr__(self, name: str):
        return getattr(self.client, name)


def run_localhost_submit_ack_smoke(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    timeout: float = DEFAULT_TIMEOUT,
    symbol: str = DEFAULT_SYMBOL,
    qty: int = DEFAULT_QTY,
):
    native_api = load_ibkr_native_api()
    recorder = SubmitAckCallbackRecorder()
    registry = IBKRPendingRequestRegistry()
    request_coordinator = IBKRRequestCoordinator(registry=registry)
    bridge = RecordingSubmitAckBridge(
        registry,
        request_coordinator=request_coordinator,
        recorder=recorder,
    )
    coordinator = IBKRRuntimeArbitrationCoordinator(enabled=True)
    wrapper_class = build_native_submit_ack_wrapper_class(native_api.e_wrapper)
    wrapper = wrapper_class(
        coordinator=coordinator,
        bridge=bridge,
        recorder=recorder,
    )
    native_client = native_api.e_client(wrapper)
    client = RecordingSubmitAckClient(
        client=native_client,
        request_coordinator=request_coordinator,
        recorder=recorder,
    )
    coordinator.client = client
    adapter = IBKRBrokerAdapter(
        client=client,
        native_api=native_api,
        bridge=bridge,
        registry=registry,
        request_coordinator=request_coordinator,
        coordinator=coordinator,
    )

    print(
        "IBKR manual localhost submit-ack smoke "
        f"host={host} port={port} client_id={client_id} symbol={symbol} qty={qty}"
    )
    terminal_result = None
    order_result = None
    order_exception = None
    allocated_order_id = None
    result_before_late_probe = None
    result_after_late_probe = None

    try:
        coordinator.connect(
            host=host,
            port=port,
            client_id=client_id,
            timeout=timeout,
        )
        if not coordinator.wait_for_completion(timeout=timeout):
            coordinator.timeout_connect(
                message="submit-ack smoke timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )
        terminal_result = coordinator.connect_result()
        print(f"terminal_result={terminal_result}")
        print(f"terminal_completion_source={coordinator.completed_by}")
        print(f"next_valid_id={bridge.latest_next_valid_id}")

        if terminal_result is None or not terminal_result.passed:
            print("submit_ack_skipped=connect_failed")
        else:
            run_thread_ready = wait_for_run_thread_ready(
                coordinator,
                timeout=RUN_THREAD_READY_TIMEOUT,
            )
            print(f"run_thread_ready_before_submit={run_thread_ready}")
            print(f"run_thread_state_before_submit={coordinator.thread_owner.thread_state}")
            if not run_thread_ready:
                print("submit_ack_skipped=run_thread_not_ready")
                return None
            order = adapter.build_market_order(symbol, qty)
            try:
                order_result = adapter.submit_market_order(
                    order,
                    timeout_seconds=timeout,
                )
                allocated_order_id = int(order_result.order_id)
                print(f"allocated_order_id={allocated_order_id}")
                print(f"order_result={order_result}")
            except Exception as exc:
                order_exception = exc
                place_events = [
                    event for event in recorder.events if event["event_type"] == "placeOrder"
                ]
                if place_events:
                    allocated_order_id = place_events[-1]["order_id"]
                print(f"allocated_order_id={allocated_order_id}")
                print(f"order_exception_type={type(exc).__name__}")
                print(f"order_exception={exc!r}")

        if allocated_order_id is not None:
            print(
                "request_completion_source="
                f"{request_coordinator.completed_by(allocated_order_id)}"
            )
            print(
                "pending_request="
                f"{request_coordinator.has_pending_request(allocated_order_id)}"
            )
            result_before_late_probe = request_coordinator.result(allocated_order_id)
            print(f"retained_result_before_late_probe={result_before_late_probe!r}")
            late_status_routed = bridge.order_status(
                order_id=allocated_order_id,
                status="Filled",
            )
            result_after_late_probe = request_coordinator.result(allocated_order_id)
            print(f"synthetic_late_status_routed={late_status_routed}")
            print(f"retained_result_after_late_probe={result_after_late_probe!r}")
            print(
                "late_probe_mutated_result="
                f"{result_before_late_probe != result_after_late_probe}"
            )
        else:
            print("request_completion_source=None")
            print("pending_request=None")
            print("retained_result_before_late_probe=None")
            print("synthetic_late_status_routed=None")
            print("retained_result_after_late_probe=None")
            print("late_probe_mutated_result=None")

        status_events = [
            event for event in recorder.events if event["event_type"] == "orderStatus"
        ]
        broker_statuses = [event.get("status") for event in status_events]
        first_ack_events = [
            event
            for event in recorder.events
            if event["event_type"] in {"openOrder", "orderStatus"}
            and event.get("routed") is True
        ]
        first_ack_type = first_ack_events[0]["event_type"] if first_ack_events else None
        filled_events = [
            event for event in status_events if str(event.get("status")) == "Filled"
        ]
        timeout_events = [
            event
            for event in recorder.events
            if event["event_type"] == "timeout_order_submission"
        ]
        place_events = [
            event for event in recorder.events if event["event_type"] == "placeOrder"
        ]
        registration_before_place_order = (
            place_events[-1].get("pending_before_place_order") if place_events else None
        )

        print(f"broker_statuses_observed={broker_statuses}")
        print(f"first_ack_type={first_ack_type}")
        print(f"submitted_or_open_order_arrived_first={first_ack_type}")
        print(f"filled_arrived_during_lifecycle_window={bool(filled_events)}")
        print(f"timeout_occurred={bool(timeout_events)}")
        print(f"registration_before_place_order={registration_before_place_order}")
        print(f"callback_count={len(recorder.events)}")
        for event in recorder.events:
            print(f"callback_event={event}")
        return order_result
    finally:
        joined = coordinator.disconnect(timeout=timeout)
        print(f"disconnect_joined={joined}")
        print(f"disconnect_result={coordinator.disconnect_result()}")
        print(f"connect_state={coordinator.connect_state}")
        print(f"shutdown_state={coordinator.shutdown_state}")
        print(f"thread_state={coordinator.thread_owner.thread_state}")


def wait_for_run_thread_ready(
    coordinator: IBKRRuntimeArbitrationCoordinator,
    *,
    timeout: float,
) -> bool:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        if coordinator.thread_owner.thread_state == "running":
            return True
        if coordinator.thread_owner.thread_state == "stopped":
            return False
        time.sleep(0.01)
    return coordinator.thread_owner.thread_state == "running"


if __name__ == "__main__":
    run_localhost_submit_ack_smoke()
