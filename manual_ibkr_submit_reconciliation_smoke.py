from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from time import monotonic
import time

from broker_interface import BrokerSubmitIntent
from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import load_ibkr_native_api
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator
from ibkr_submit_reconciliation_workflow import IBKRSubmitReconciliationWorkflow


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 9116
DEFAULT_TIMEOUT = 15.0
DEFAULT_SYMBOL = "AAPL"
DEFAULT_QTY = 1
LOCALHOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
PAPER_PORTS = frozenset({7497, 4002})
NON_FATAL_CONNECT_STATUS_CODES = frozenset({2104, 2106, 2158})
RUN_THREAD_READY_TIMEOUT = 2.0


@dataclass
class ReconciliationSmokeRecorder:
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


class RecordingReconciliationBridge(IBKRCallbackBridge):
    def __init__(
        self,
        registry: IBKRPendingRequestRegistry,
        *,
        request_coordinator: IBKRRequestCoordinator,
        recorder: ReconciliationSmokeRecorder,
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

    def timeout_order_submission(self, *, order_id: object):
        result = super().timeout_order_submission(order_id=order_id)
        self.recorder.record(
            "timeout_order_submission",
            order_id=order_id,
            result=result,
        )
        return result

    def begin_execution_snapshot(
        self,
        *,
        request_id: object,
        symbol: str | None = None,
        generation: int | None = None,
    ) -> int:
        generation_result = super().begin_execution_snapshot(
            request_id=request_id,
            symbol=symbol,
            generation=generation,
        )
        self.recorder.record(
            "begin_execution_snapshot",
            request_id=request_id,
            symbol=symbol,
            generation=generation_result,
        )
        return generation_result

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

    def begin_position_snapshot(self, *, request_id: object, symbol: str) -> None:
        self.recorder.record(
            "begin_position_snapshot",
            request_id=request_id,
            symbol=symbol,
        )
        return super().begin_position_snapshot(request_id=request_id, symbol=symbol)

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
        active_open_generation = self._active_open_orders_generation
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
            generation=active_open_generation,
            order_id=order_id,
            perm_id=perm_id,
            symbol=symbol,
            side=side,
            qty=qty,
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
        active_open_generation = self._active_open_orders_generation
        routed = super().open_order_status_update(
            order_id=order_id,
            status=status,
            perm_id=perm_id,
        )
        self.recorder.record(
            "orderStatus",
            generation=active_open_generation,
            order_id=order_id,
            perm_id=perm_id,
            status=status,
            routed=routed,
            route_method="open_order_status_update",
        )
        return routed

    def exec_details(
        self,
        *,
        request_id: object,
        order_id: object | None = None,
        client_id: object | None = None,
        perm_id: object | None = None,
        symbol: str = "",
        side: str = "",
        shares: object | None = None,
        cumulative_qty: object | None = None,
        avg_price: object | None = None,
        price: object | None = None,
        time: object | None = None,
        exec_id: object | None = None,
        raw_execution: object | None = None,
    ) -> bool:
        routed = super().exec_details(
            request_id=request_id,
            order_id=order_id,
            client_id=client_id,
            perm_id=perm_id,
            symbol=symbol,
            side=side,
            shares=shares,
            cumulative_qty=cumulative_qty,
            avg_price=avg_price,
            price=price,
            time=time,
            exec_id=exec_id,
            raw_execution=raw_execution,
        )
        self.recorder.record(
            "execDetails",
            request_id=request_id,
            order_id=order_id,
            client_id=client_id,
            perm_id=perm_id,
            symbol=symbol,
            side=side,
            shares=shares,
            cumulative_qty=cumulative_qty,
            avg_price=avg_price,
            price=price,
            time=time,
            exec_id=exec_id,
            routed=routed,
        )
        return routed

    def exec_details_end(self, *, request_id: object) -> bool:
        routed = super().exec_details_end(request_id=request_id)
        self.recorder.record(
            "execDetailsEnd",
            request_id=request_id,
            routed=routed,
        )
        return routed

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


class SubmitReconciliationSmokeWrapper:
    def __init__(
        self,
        *,
        coordinator: IBKRRuntimeArbitrationCoordinator,
        bridge: RecordingReconciliationBridge,
        recorder: ReconciliationSmokeRecorder,
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
        if self.bridge._active_open_orders_generation is not None:
            return self.bridge.open_order_status_update(
                order_id=orderId,
                perm_id=permId,
                status=status,
            )
        return self.bridge.order_status(
            order_id=orderId,
            status=status,
        )

    def execDetails(self, reqId, contract, execution) -> bool:
        return self.bridge.exec_details(
            request_id=reqId,
            order_id=getattr(execution, "orderId", None),
            client_id=getattr(execution, "clientId", None),
            perm_id=getattr(execution, "permId", None),
            symbol=getattr(contract, "symbol", ""),
            side=getattr(execution, "side", ""),
            shares=getattr(execution, "shares", None),
            cumulative_qty=getattr(execution, "cumQty", None),
            avg_price=getattr(execution, "avgPrice", None),
            price=getattr(execution, "price", None),
            time=getattr(execution, "time", None),
            exec_id=getattr(execution, "execId", None),
            raw_execution=execution,
        )

    def execDetailsEnd(self, reqId) -> bool:
        return self.bridge.exec_details_end(request_id=reqId)

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


def build_native_submit_reconciliation_wrapper_class(native_wrapper_class):
    class NativeSubmitReconciliationSmokeWrapper(
        SubmitReconciliationSmokeWrapper,
        native_wrapper_class,
    ):
        def __init__(
            self,
            *,
            coordinator: IBKRRuntimeArbitrationCoordinator,
            bridge: RecordingReconciliationBridge,
            recorder: ReconciliationSmokeRecorder,
        ) -> None:
            native_wrapper_class.__init__(self)
            SubmitReconciliationSmokeWrapper.__init__(
                self,
                coordinator=coordinator,
                bridge=bridge,
                recorder=recorder,
            )

    return NativeSubmitReconciliationSmokeWrapper


class RecordingReconciliationClient:
    def __init__(
        self,
        *,
        client,
        request_coordinator: IBKRRequestCoordinator,
        recorder: ReconciliationSmokeRecorder,
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

    def reqExecutions(self, request_id, execution_filter) -> object:
        self.recorder.record(
            "reqExecutions",
            request_id=request_id,
            symbol=getattr(execution_filter, "symbol", None),
            side=getattr(execution_filter, "side", None),
            time=getattr(execution_filter, "time", None),
        )
        return self.client.reqExecutions(request_id, execution_filter)

    def reqAllOpenOrders(self) -> object:
        self.recorder.record("reqAllOpenOrders")
        return self.client.reqAllOpenOrders()

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


def run_localhost_submit_reconciliation_smoke(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    timeout: float = DEFAULT_TIMEOUT,
    symbol: str = DEFAULT_SYMBOL,
    qty: int = DEFAULT_QTY,
):
    _validate_smoke_inputs(host=host, port=port, timeout=timeout, qty=qty)

    native_api = load_ibkr_native_api()
    recorder = ReconciliationSmokeRecorder()
    registry = IBKRPendingRequestRegistry()
    request_coordinator = IBKRRequestCoordinator(registry=registry)
    bridge = RecordingReconciliationBridge(
        registry,
        request_coordinator=request_coordinator,
        recorder=recorder,
    )
    coordinator = IBKRRuntimeArbitrationCoordinator(enabled=True)
    wrapper_class = build_native_submit_reconciliation_wrapper_class(
        native_api.e_wrapper
    )
    wrapper = wrapper_class(
        coordinator=coordinator,
        bridge=bridge,
        recorder=recorder,
    )
    native_client = native_api.e_client(wrapper)
    client = RecordingReconciliationClient(
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
        "IBKR manual localhost submit-reconciliation smoke "
        f"host={host} port={port} client_id={client_id} symbol={symbol} qty={qty}"
    )
    order_result = None
    allocated_order_id = None
    workflow_result = None

    try:
        coordinator.connect(
            host=host,
            port=port,
            client_id=client_id,
            timeout=timeout,
        )
        if not coordinator.wait_for_completion(timeout=timeout):
            coordinator.timeout_connect(
                message="submit-reconciliation smoke timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )
        connection_result = coordinator.connect_result()
        print(f"connection_result={connection_result}")
        print(f"connection_completion_source={coordinator.completed_by}")
        print(f"next_valid_id={bridge.latest_next_valid_id}")

        if connection_result is None or not connection_result.passed:
            print("submit_reconciliation_skipped=connect_failed")
            return None

        run_thread_ready = wait_for_run_thread_ready(
            coordinator,
            timeout=RUN_THREAD_READY_TIMEOUT,
        )
        print(f"run_thread_ready_before_submit={run_thread_ready}")
        print(f"run_thread_state_before_submit={coordinator.thread_owner.thread_state}")
        if not run_thread_ready:
            print("submit_reconciliation_skipped=run_thread_not_ready")
            return None

        order = adapter.build_market_order(symbol, qty)
        try:
            order_result = adapter.submit_market_order(
                order,
                timeout_seconds=timeout,
            )
            allocated_order_id = order_result.order_id
            print(f"allocated_order_id={allocated_order_id}")
            print(f"raw_submit_result={order_result}")
        except Exception as exc:
            print(f"allocated_order_id={_latest_place_order_id(recorder)}")
            print(f"submit_exception_type={type(exc).__name__}")
            print(f"submit_exception={exc!r}")
            return None

        became_reconciliation_required = (
            order_result.order_status == "reconciliation_required"
        )
        print(
            "submit_became_reconciliation_required="
            f"{became_reconciliation_required}"
        )
        if not became_reconciliation_required:
            print("reconciliation_not_invoked=True")
            return order_result

        intent = BrokerSubmitIntent(
            broker_name="ibkr",
            order_id=order_result.order_id,
            client_id=str(client_id),
            perm_id=None,
            symbol=symbol,
            side="buy" if qty > 0 else "sell",
            qty=abs(float(qty)),
            submitted_at=None,
        )
        workflow_result = IBKRSubmitReconciliationWorkflow().reconcile_if_required(
            broker=adapter,
            submit_result=order_result,
            intent=intent,
            timeout_seconds=timeout,
        )
        evidence = _workflow_evidence(workflow_result)
        print(f"execution_snapshot_result={evidence.get('execution_snapshot')}")
        print(f"open_order_snapshot_result={evidence.get('open_order_snapshot')}")
        print(f"position_snapshot_result={evidence.get('position_snapshot')}")
        print(f"final_reconciliation_status={workflow_result.reconciliation_status}")
        print(f"manual_review_required={workflow_result.manual_review_required}")
        print(f"terminal_for_run={workflow_result.terminal_for_run}")
        print(f"filled_qty={workflow_result.filled_qty}")
        print(f"working_qty={workflow_result.working_qty}")
        print(f"ambiguous={workflow_result.ambiguous}")
        print(f"reason={workflow_result.reason}")
        return workflow_result
    finally:
        print(f"callback_count={len(recorder.events)}")
        for event in recorder.events:
            print(f"callback_event={event}")
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


def _validate_smoke_inputs(
    *,
    host: str,
    port: int,
    timeout: float,
    qty: int,
) -> None:
    if host not in LOCALHOSTS:
        raise ValueError("IBKR reconciliation smoke is restricted to localhost")
    if port not in PAPER_PORTS:
        raise ValueError("IBKR reconciliation smoke is restricted to paper ports")
    if not isfinite(timeout) or timeout <= 0:
        raise ValueError("IBKR reconciliation smoke requires a finite positive timeout")
    if int(qty) == 0:
        raise ValueError("IBKR reconciliation smoke qty must be non-zero")


def _is_negative_position(pos) -> bool:
    try:
        return float(pos) < 0
    except (TypeError, ValueError):
        return False


def _workflow_evidence(workflow_result) -> dict:
    reconciliation = getattr(workflow_result, "reconciliation_result", None)
    raw_evidence = getattr(reconciliation, "raw_evidence", None)
    if isinstance(raw_evidence, dict):
        return raw_evidence
    return {}


def _latest_place_order_id(recorder: ReconciliationSmokeRecorder):
    place_events = [
        event for event in recorder.events if event["event_type"] == "placeOrder"
    ]
    if not place_events:
        return None
    return place_events[-1].get("order_id")


if __name__ == "__main__":
    run_localhost_submit_reconciliation_smoke()
