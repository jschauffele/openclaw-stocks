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
DEFAULT_CLIENT_ID = 9113
DEFAULT_TIMEOUT = 5.0
DEFAULT_SYMBOL = "AAPL"
DEFAULT_POSITION_REQUEST_ID_START = 8201
NON_FATAL_CONNECT_STATUS_CODES = frozenset({2104, 2106, 2158})


@dataclass
class PositionMultiCallbackRecorder:
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


class RecordingPositionMultiBridge(IBKRCallbackBridge):
    def __init__(
        self,
        registry: IBKRPendingRequestRegistry,
        *,
        request_coordinator: IBKRRequestCoordinator,
        recorder: PositionMultiCallbackRecorder,
    ) -> None:
        super().__init__(
            registry,
            request_coordinator=request_coordinator,
        )
        self.recorder = recorder

    def begin_position_snapshot(self, *, request_id: object, symbol: str) -> None:
        self.recorder.record(
            "begin_position_snapshot",
            request_id=request_id,
            symbol=symbol,
        )
        return super().begin_position_snapshot(request_id=request_id, symbol=symbol)

    def position_multi(
        self,
        *,
        request_id: object,
        symbol: str,
        qty: object,
        side: str = "long",
        account: object | None = None,
        model_code: object | None = None,
        avg_cost: object | None = None,
    ) -> bool:
        routed = super().position_multi(
            request_id=request_id,
            account=account,
            model_code=model_code,
            symbol=symbol,
            qty=qty,
            side=side,
            avg_cost=avg_cost,
        )
        self.recorder.record(
            "positionMulti",
            request_id=request_id,
            account=account,
            model_code=model_code,
            symbol=symbol,
            qty=qty,
            side=side,
            avg_cost=avg_cost,
            routed=routed,
        )
        return routed

    def position_multi_end(self, *, request_id: object) -> bool:
        routed = super().position_multi_end(request_id=request_id)
        self.recorder.record(
            "positionMultiEnd",
            request_id=request_id,
            routed=routed,
        )
        return routed


class PositionMultiSmokeWrapper:
    def __init__(
        self,
        *,
        coordinator: IBKRRuntimeArbitrationCoordinator,
        bridge: RecordingPositionMultiBridge,
        recorder: PositionMultiCallbackRecorder,
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

    def positionMulti(self, reqId, account, modelCode, contract, pos, avgCost) -> bool:
        symbol = getattr(contract, "symbol", "")
        side = "short" if _is_negative_position(pos) else "long"
        return self.bridge.position_multi(
            request_id=reqId,
            account=account,
            model_code=modelCode,
            symbol=symbol,
            qty=pos,
            side=side,
            avg_cost=avgCost,
        )

    def positionMultiEnd(self, reqId) -> bool:
        return self.bridge.position_multi_end(request_id=reqId)

    def connectAck(self) -> bool:
        self.recorder.record("connectAck")
        return False

    def connectionClosed(self) -> bool:
        self.recorder.record("connectionClosed")
        return False


def build_native_position_multi_wrapper_class(native_wrapper_class):
    class NativePositionMultiSmokeWrapper(
        PositionMultiSmokeWrapper,
        native_wrapper_class,
    ):
        def __init__(
            self,
            *,
            coordinator: IBKRRuntimeArbitrationCoordinator,
            bridge: RecordingPositionMultiBridge,
            recorder: PositionMultiCallbackRecorder,
        ) -> None:
            native_wrapper_class.__init__(self)
            PositionMultiSmokeWrapper.__init__(
                self,
                coordinator=coordinator,
                bridge=bridge,
                recorder=recorder,
            )

    return NativePositionMultiSmokeWrapper


class RecordingPositionClient:
    def __init__(
        self,
        *,
        client,
        recorder: PositionMultiCallbackRecorder,
    ) -> None:
        self.client = client
        self.recorder = recorder

    def reqPositionsMulti(self, request_id, account, model_code) -> object:
        self.recorder.record(
            "reqPositionsMulti",
            request_id=request_id,
            account=account,
            model_code=model_code,
        )
        return self.client.reqPositionsMulti(request_id, account, model_code)

    def cancelPositionsMulti(self, request_id) -> object:
        self.recorder.record("cancelPositionsMulti", request_id=request_id)
        return self.client.cancelPositionsMulti(request_id)

    def __getattr__(self, name: str):
        return getattr(self.client, name)


def run_localhost_position_multi_smoke(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    timeout: float = DEFAULT_TIMEOUT,
    symbol: str = DEFAULT_SYMBOL,
    position_request_id_start: int = DEFAULT_POSITION_REQUEST_ID_START,
    position_account: str = "",
    position_model_code: str = "",
):
    native_api = load_ibkr_native_api()
    recorder = PositionMultiCallbackRecorder()
    registry = IBKRPendingRequestRegistry()
    request_coordinator = IBKRRequestCoordinator(registry=registry)
    bridge = RecordingPositionMultiBridge(
        registry,
        request_coordinator=request_coordinator,
        recorder=recorder,
    )
    coordinator = IBKRRuntimeArbitrationCoordinator(enabled=True)
    wrapper_class = build_native_position_multi_wrapper_class(native_api.e_wrapper)
    wrapper = wrapper_class(
        coordinator=coordinator,
        bridge=bridge,
        recorder=recorder,
    )
    native_client = native_api.e_client(wrapper)
    client = RecordingPositionClient(client=native_client, recorder=recorder)
    coordinator.client = client
    adapter = IBKRBrokerAdapter(
        client=client,
        bridge=bridge,
        registry=registry,
        request_coordinator=request_coordinator,
        coordinator=coordinator,
        position_account=position_account,
        position_model_code=position_model_code,
        position_request_id_start=position_request_id_start,
    )

    print(
        "IBKR manual localhost positionMulti smoke "
        f"host={host} port={port} client_id={client_id} "
        f"symbol={symbol} position_request_id_start={position_request_id_start} "
        f"position_account={position_account!r} position_model_code={position_model_code!r}"
    )
    terminal_result = None
    position_state = None
    position_exception = None
    requested_id = None

    try:
        coordinator.connect(
            host=host,
            port=port,
            client_id=client_id,
            timeout=timeout,
        )
        if not coordinator.wait_for_completion(timeout=timeout):
            coordinator.timeout_connect(
                message="positionMulti smoke timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )
        terminal_result = coordinator.connect_result()
        print(f"terminal_result={terminal_result}")

        if terminal_result is None or not terminal_result.passed:
            print("position_multi_skipped=connect_failed")
            return None

        try:
            position_state = adapter.get_existing_position(
                symbol,
                timeout_seconds=timeout,
            )
            requested_id = adapter._next_position_request_id - 1
            print(f"request_id={requested_id}")
            print(f"position_state={position_state}")
        except Exception as exc:
            requested_id = adapter._next_position_request_id - 1
            position_exception = exc
            print(f"request_id={requested_id}")
            print(f"position_exception_type={type(exc).__name__}")
            print(f"position_exception={exc!r}")

        if requested_id is not None:
            print(f"completion_source={request_coordinator.completed_by(requested_id)}")
            print(f"retained_result={request_coordinator.result(requested_id)!r}")
            print(f"pending_request={request_coordinator.has_pending_request(requested_id)}")
        print(f"callback_count={len(recorder.events)}")
        for event in recorder.events:
            print(f"callback_event={event}")
        return position_state
    finally:
        joined = coordinator.disconnect(timeout=timeout)
        print(f"disconnect_joined={joined}")
        print(f"connect_state={coordinator.connect_state}")
        print(f"shutdown_state={coordinator.shutdown_state}")
        print(f"thread_state={coordinator.thread_owner.thread_state}")
        print(f"disconnect_result={coordinator.disconnect_result()}")


def _is_negative_position(pos) -> bool:
    try:
        return float(pos) < 0
    except (TypeError, ValueError):
        return str(pos).strip().startswith("-")


if __name__ == "__main__":
    run_localhost_position_multi_smoke()
