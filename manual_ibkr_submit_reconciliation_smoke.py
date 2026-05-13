from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from math import isfinite
import os
from pathlib import Path
from time import monotonic
import time

from broker_interface import BrokerSubmitIntent
from ibkr_broker_adapter import IBKRBrokerAdapter, IBKRMarketOrder
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
SMOKE_SAFETY_READ_TIMEOUT = 2.0
SMOKE_MIN_MARKET_ORDER_TIMEOUT = 5.0
SMOKE_LOCAL_DIR = Path(__file__).resolve().parent / ".local"
SMOKE_LOCK_PATH = SMOKE_LOCAL_DIR / "ibkr_smoke.lock"
SMOKE_LAST_STATE_PATH = SMOKE_LOCAL_DIR / "ibkr_smoke_last_state.json"
UNSAFE_RECONCILIATION_STATUSES = frozenset(
    {"unresolved", "partially_filled_unresolved"}
)


class SmokeSafetyRefusal(RuntimeError):
    pass


@dataclass(frozen=True)
class SmokeBrokerState:
    open_order_snapshot: object
    position_snapshot: object
    state: str
    reason: str


class SmokeRunLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.acquired = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "created_at_monotonic": monotonic(),
            "purpose": "ibkr_localhost_smoke_single_flight",
        }
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise SmokeSafetyRefusal(
                f"IBKR smoke already in flight: lock_path={self.path}"
            ) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
            json.dump(payload, lock_file, sort_keys=True)
        self.acquired = True

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        self.acquired = False


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
    ) -> int:
        generation_result = super().begin_execution_snapshot(
            request_id=request_id,
            symbol=symbol,
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
    lock_path: Path | str = SMOKE_LOCK_PATH,
    last_state_path: Path | str = SMOKE_LAST_STATE_PATH,
    preflight_only: bool = False,
    order_type: str = "market",
    limit_price: float | None = None,
):
    _validate_smoke_inputs(host=host, port=port, timeout=timeout, qty=qty)
    smoke_order_type = _normalize_smoke_order_type(order_type)
    lock = SmokeRunLock(Path(lock_path))
    _refuse_if_last_run_requires_cleanup(Path(last_state_path))

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
    lock.acquire()

    print(
        "IBKR manual localhost submit-reconciliation smoke "
        f"host={host} port={port} client_id={client_id} symbol={symbol} qty={qty}"
    )
    print(f"smoke_order_type={smoke_order_type}")
    if smoke_order_type == "limit":
        print(f"limit_price={limit_price}")
    order_result = None
    allocated_order_id = None
    workflow_result = None
    connection_result = None
    pre_submit_state = None
    final_broker_state = "not_submitted"
    final_broker_state_reason = "submit_not_attempted"
    submit_attempted = False
    disconnect_joined = False
    disconnect_passed = False
    safety_timeout = max(timeout, SMOKE_SAFETY_READ_TIMEOUT)

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

        pre_submit_state = query_smoke_broker_state(
            adapter,
            symbol=symbol,
            timeout=safety_timeout,
        )
        print(f"pre_submit_open_order_snapshot={pre_submit_state.open_order_snapshot}")
        print(f"pre_submit_position_snapshot={pre_submit_state.position_snapshot}")
        print(f"pre_submit_broker_state={pre_submit_state.state}")
        if pre_submit_state.state != "clean":
            print(f"submit_reconciliation_refused={pre_submit_state.reason}")
            final_broker_state = pre_submit_state.state
            final_broker_state_reason = pre_submit_state.reason
            return None
        if preflight_only:
            print("submit_reconciliation_preflight_only=True")
            final_broker_state = pre_submit_state.state
            final_broker_state_reason = pre_submit_state.reason
            return pre_submit_state

        order = build_smoke_order(
            adapter=adapter,
            native_api=native_api,
            symbol=symbol,
            qty=qty,
            order_type=smoke_order_type,
            timeout=timeout,
            limit_price=limit_price,
        )
        if order is None:
            final_broker_state = "not_submitted"
            final_broker_state_reason = _smoke_order_refusal_reason(
                order_type=smoke_order_type,
                qty=qty,
                timeout=timeout,
                limit_price=limit_price,
            )
            print(f"submit_reconciliation_refused={final_broker_state_reason}")
            return None
        try:
            submit_attempted = True
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
        if submit_attempted:
            try:
                final_state = query_smoke_broker_state(
                    adapter,
                    symbol=symbol,
                    timeout=safety_timeout,
                )
                final_broker_state = final_state.state
                final_broker_state_reason = final_state.reason
                print(f"final_open_order_snapshot={final_state.open_order_snapshot}")
                print(f"final_position_snapshot={final_state.position_snapshot}")
                print(f"final_broker_state={final_broker_state}")
            except Exception as exc:
                final_broker_state = "unknown"
                final_broker_state_reason = str(exc) or type(exc).__name__
                print(f"final_broker_state={final_broker_state}")
                print(f"final_broker_state_error={final_broker_state_reason}")
        print(f"callback_count={len(recorder.events)}")
        for event in recorder.events:
            print(f"callback_event={event}")
        disconnect_error = None
        try:
            disconnect_joined = coordinator.disconnect(timeout=timeout)
            disconnect_result = coordinator.disconnect_result()
            disconnect_passed = bool(
                disconnect_joined
                and disconnect_result is not None
                and getattr(disconnect_result, "passed", False)
            )
        except Exception as exc:
            disconnect_result = None
            disconnect_passed = False
            disconnect_error = str(exc) or type(exc).__name__
        print(f"disconnect_joined={disconnect_joined}")
        print(f"disconnect_result={disconnect_result}")
        if disconnect_error is not None:
            print(f"disconnect_error={disconnect_error}")
        print(f"connect_state={coordinator.connect_state}")
        print(f"shutdown_state={coordinator.shutdown_state}")
        print(f"thread_state={coordinator.thread_owner.thread_state}")
        try:
            write_smoke_last_state(
                Path(last_state_path),
                {
                    "symbol": symbol,
                    "qty": qty,
                    "order_type": smoke_order_type,
                    "limit_price": limit_price,
                    "submit_attempted": submit_attempted,
                    "order_id": getattr(order_result, "order_id", None),
                    "order_status": getattr(order_result, "order_status", None),
                    "reconciliation_status": getattr(
                        workflow_result, "reconciliation_status", None
                    ),
                    "manual_review_required": bool(
                        getattr(workflow_result, "manual_review_required", False)
                    ),
                    "final_broker_state": final_broker_state,
                    "final_broker_state_reason": final_broker_state_reason,
                    "disconnect_joined": disconnect_joined,
                    "disconnect_passed": disconnect_passed,
                    "disconnect_error": disconnect_error,
                },
            )
        finally:
            lock.release()


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


def build_smoke_order(
    *,
    adapter: IBKRBrokerAdapter,
    native_api,
    symbol: str,
    qty: int,
    order_type: str,
    timeout: float,
    limit_price: float | None,
):
    refusal_reason = _smoke_order_refusal_reason(
        order_type=order_type,
        qty=qty,
        timeout=timeout,
        limit_price=limit_price,
    )
    if refusal_reason is not None:
        return None
    if order_type == "market":
        return adapter.build_market_order(symbol, qty)
    return build_smoke_limit_order(
        native_api=native_api,
        symbol=symbol,
        qty=qty,
        limit_price=float(limit_price),
    )


def build_smoke_limit_order(
    *,
    native_api,
    symbol: str,
    qty: int,
    limit_price: float,
) -> IBKRMarketOrder:
    contract = native_api.contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    order = native_api.order()
    order.action = "BUY"
    order.orderType = "LMT"
    order.totalQuantity = abs(int(qty))
    order.lmtPrice = float(limit_price)
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


def _smoke_order_refusal_reason(
    *,
    order_type: str,
    qty: int,
    timeout: float,
    limit_price: float | None,
) -> str | None:
    if order_type == "market":
        if timeout < SMOKE_MIN_MARKET_ORDER_TIMEOUT:
            return "market_order_timeout_too_short"
        return None
    if limit_price is None:
        return "limit_price_required"
    try:
        normalized_limit = float(limit_price)
    except (TypeError, ValueError):
        return "limit_price_required"
    if normalized_limit <= 0:
        return "limit_price_must_be_positive"
    if int(qty) <= 0:
        return "limit_smoke_requires_buy_qty"
    return None


def _normalize_smoke_order_type(order_type: str) -> str:
    normalized = str(order_type).lower()
    if normalized not in {"market", "limit"}:
        raise ValueError("IBKR smoke order_type must be 'market' or 'limit'")
    return normalized


def query_smoke_broker_state(
    adapter: IBKRBrokerAdapter,
    *,
    symbol: str,
    timeout: float,
) -> SmokeBrokerState:
    open_order_snapshot = adapter.get_open_buy_order_qty(
        symbol,
        timeout_seconds=timeout,
    )
    position_snapshot = adapter.get_existing_position(
        symbol,
        timeout_seconds=timeout,
    )
    return classify_smoke_broker_state(
        open_order_snapshot=open_order_snapshot,
        position_snapshot=position_snapshot,
    )


def classify_smoke_broker_state(
    *,
    open_order_snapshot: object,
    position_snapshot: object,
) -> SmokeBrokerState:
    if not getattr(open_order_snapshot, "passed", False):
        return SmokeBrokerState(
            open_order_snapshot=open_order_snapshot,
            position_snapshot=position_snapshot,
            state="unknown",
            reason="open_order_snapshot_failed",
        )
    open_qty = getattr(open_order_snapshot, "open_buy_order_qty", None)
    open_count = getattr(open_order_snapshot, "open_buy_order_count", None)
    if _positive_number(open_qty) or _positive_number(open_count):
        return SmokeBrokerState(
            open_order_snapshot=open_order_snapshot,
            position_snapshot=position_snapshot,
            state="open_orders",
            reason="open_orders_exist",
        )
    if getattr(position_snapshot, "found", None) is None:
        return SmokeBrokerState(
            open_order_snapshot=open_order_snapshot,
            position_snapshot=position_snapshot,
            state="unknown",
            reason="position_snapshot_unknown",
        )
    if getattr(position_snapshot, "error", None):
        return SmokeBrokerState(
            open_order_snapshot=open_order_snapshot,
            position_snapshot=position_snapshot,
            state="unknown",
            reason="position_snapshot_failed",
        )
    if _non_flat_position(position_snapshot):
        return SmokeBrokerState(
            open_order_snapshot=open_order_snapshot,
            position_snapshot=position_snapshot,
            state="non_flat_position",
            reason="position_is_non_flat",
        )
    return SmokeBrokerState(
        open_order_snapshot=open_order_snapshot,
        position_snapshot=position_snapshot,
        state="clean",
        reason="no_open_orders_or_position",
    )


def write_smoke_last_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _refuse_if_last_run_requires_cleanup(path: Path) -> None:
    state = _read_smoke_last_state(path)
    if state is None:
        return
    reason = _last_run_cleanup_reason(state)
    if reason is None:
        return
    raise SmokeSafetyRefusal(
        "Previous IBKR smoke state requires cleanup before another run: "
        f"{reason}; state_path={path}"
    )


def _read_smoke_last_state(path: Path) -> dict[str, object] | None:
    try:
        raw_state = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        state = json.loads(raw_state)
    except json.JSONDecodeError as exc:
        raise SmokeSafetyRefusal(
            f"Previous IBKR smoke state is unreadable: state_path={path}"
        ) from exc
    if not isinstance(state, dict):
        raise SmokeSafetyRefusal(
            f"Previous IBKR smoke state is invalid: state_path={path}"
        )
    return state


def _last_run_cleanup_reason(state: dict[str, object]) -> str | None:
    if state.get("manual_review_required") is True:
        return "manual_review_required"
    reconciliation_status = state.get("reconciliation_status")
    if reconciliation_status in UNSAFE_RECONCILIATION_STATUSES:
        return f"reconciliation_status={reconciliation_status}"
    if state.get("disconnect_joined") is False or state.get("disconnect_passed") is False:
        return "disconnect_failed"
    final_broker_state = state.get("final_broker_state")
    if final_broker_state in {"open_orders", "non_flat_position"}:
        return f"final_broker_state={final_broker_state}"
    if state.get("submit_attempted") is True and state.get("final_broker_state") == "unknown":
        return "unknown_final_broker_state"
    return None


def _positive_number(value: object) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _non_flat_position(position_snapshot: object) -> bool:
    if not getattr(position_snapshot, "found", False):
        return False
    qty = getattr(position_snapshot, "qty", None)
    raw_qty = getattr(position_snapshot, "raw_qty", None)
    try:
        return float(qty if qty is not None else raw_qty) != 0.0
    except (TypeError, ValueError):
        return True


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


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run the localhost IBKR submit-reconciliation smoke harness."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--client-id", type=int, default=DEFAULT_CLIENT_ID)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--qty", type=int, default=DEFAULT_QTY)
    parser.add_argument("--order-type", choices=("market", "limit"), default="market")
    parser.add_argument("--limit-price", type=float, default=None)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Connect and verify smoke safety gates without placing an order.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_localhost_submit_reconciliation_smoke(
        host=args.host,
        port=args.port,
        client_id=args.client_id,
        timeout=args.timeout,
        symbol=args.symbol,
        qty=args.qty,
        preflight_only=args.preflight_only,
        order_type=args.order_type,
        limit_price=args.limit_price,
    )
