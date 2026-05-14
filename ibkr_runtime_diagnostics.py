from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from math import isfinite
from typing import Any

from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import load_ibkr_native_api
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 9117
DEFAULT_TIMEOUT = 5.0
DEFAULT_DISCONNECT_TIMEOUT = 1.0
DEFAULT_SYMBOL = "AAPL"
NON_FATAL_CONNECT_STATUS_CODES = frozenset({2104, 2106, 2158})


class IBKRRuntimeDiagnosticsWrapper:
    def __init__(
        self,
        *,
        coordinator: IBKRRuntimeArbitrationCoordinator,
        bridge: IBKRCallbackBridge,
    ) -> None:
        self.coordinator = coordinator
        self.bridge = bridge
        self.latest_next_valid_id: int | None = None

    def nextValidId(self, order_id) -> bool:
        try:
            self.latest_next_valid_id = int(order_id)
        except (TypeError, ValueError):
            self.latest_next_valid_id = None
        return self.coordinator.callback_connect_ready(message="next_valid_id")

    def error(self, reqId, code, msg, *args) -> bool:
        if code in NON_FATAL_CONNECT_STATUS_CODES:
            return False
        return self.coordinator.callback_connect_error(
            message=str(msg),
            retryable=True,
        )

    def accountSummary(self, reqId, account, tag, value, currency) -> bool:
        return self.bridge.account_summary(
            request_id=reqId,
            account=account,
            tag=tag,
            value=value,
            currency=currency,
        )

    def accountSummaryEnd(self, reqId) -> bool:
        return self.bridge.account_summary_end(request_id=reqId)

    def positionMulti(self, reqId, account, modelCode, contract, pos, avgCost) -> bool:
        symbol = getattr(contract, "symbol", "")
        return self.bridge.position_multi(
            request_id=reqId,
            account=account,
            model_code=modelCode,
            symbol=symbol,
            qty=pos,
            side="short" if _is_negative_position(pos) else "long",
            avg_cost=avgCost,
        )

    def positionMultiEnd(self, reqId) -> bool:
        return self.bridge.position_multi_end(request_id=reqId)

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

    def connectAck(self) -> bool:
        return False

    def connectionClosed(self) -> bool:
        return False


def build_native_diagnostics_wrapper_class(native_wrapper_class):
    class NativeIBKRRuntimeDiagnosticsWrapper(
        IBKRRuntimeDiagnosticsWrapper,
        native_wrapper_class,
    ):
        def __init__(
            self,
            *,
            coordinator: IBKRRuntimeArbitrationCoordinator,
            bridge: IBKRCallbackBridge,
        ) -> None:
            native_wrapper_class.__init__(self)
            IBKRRuntimeDiagnosticsWrapper.__init__(
                self,
                coordinator=coordinator,
                bridge=bridge,
            )

    return NativeIBKRRuntimeDiagnosticsWrapper


def run_ibkr_runtime_diagnostics(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    timeout: float = DEFAULT_TIMEOUT,
    disconnect_timeout: float = DEFAULT_DISCONNECT_TIMEOUT,
    symbol: str = DEFAULT_SYMBOL,
    include_execution_snapshot: bool = False,
    execution_since: str | None = None,
    native_api_loader=load_ibkr_native_api,
    print_output: bool = True,
) -> dict[str, Any]:
    _validate_runtime_inputs(
        host=host,
        port=port,
        timeout=timeout,
        disconnect_timeout=disconnect_timeout,
    )

    native_api = native_api_loader()
    registry = IBKRPendingRequestRegistry()
    request_coordinator = IBKRRequestCoordinator(registry=registry)
    bridge = IBKRCallbackBridge(
        registry,
        request_coordinator=request_coordinator,
    )
    coordinator = IBKRRuntimeArbitrationCoordinator(
        enabled=True,
        registry=registry,
        bridge=bridge,
    )
    wrapper_class = build_native_diagnostics_wrapper_class(native_api.e_wrapper)
    wrapper = wrapper_class(coordinator=coordinator, bridge=bridge)
    native_client = native_api.e_client(wrapper)
    coordinator.client = native_client
    adapter = IBKRBrokerAdapter(
        client=native_client,
        native_api=native_api,
        bridge=bridge,
        registry=registry,
        request_coordinator=request_coordinator,
        coordinator=coordinator,
    )

    diagnostics: dict[str, Any] = {
        "connection_result": None,
        "connection_completion_source": None,
        "next_valid_id": None,
        "open_order_snapshot": None,
        "position_snapshot": None,
        "broker_state": "unknown",
        "disconnect_result": None,
        "connect_state": None,
        "shutdown_state": None,
        "thread_state": None,
    }
    if include_execution_snapshot:
        diagnostics["execution_snapshot"] = None

    try:
        coordinator.connect(
            host=host,
            port=port,
            client_id=client_id,
            timeout=timeout,
        )
        if not coordinator.wait_for_completion(timeout=timeout):
            coordinator.timeout_connect(
                message="IBKR diagnostics timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )

        _wait_for_thread_running(coordinator, timeout=timeout)
        connection_result = coordinator.connect_result()
        diagnostics["connection_result"] = _structured(connection_result)
        diagnostics["connection_completion_source"] = coordinator.completed_by
        diagnostics["next_valid_id"] = wrapper.latest_next_valid_id
        diagnostics["connect_state"] = coordinator.connect_state
        diagnostics["shutdown_state"] = coordinator.shutdown_state
        diagnostics["thread_state"] = _thread_state(coordinator)

        if connection_result is None or not connection_result.passed:
            return diagnostics
        if coordinator.thread_owner.thread_state != "running":
            return diagnostics

        open_order_snapshot = _capture_snapshot(
            lambda: adapter.get_open_buy_order_qty(
                symbol,
                timeout_seconds=timeout,
            )
        )
        position_snapshot = _capture_snapshot(
            lambda: adapter.get_existing_position(
                symbol,
                timeout_seconds=timeout,
            )
        )
        diagnostics["open_order_snapshot"] = open_order_snapshot
        diagnostics["position_snapshot"] = position_snapshot

        if include_execution_snapshot:
            diagnostics["execution_snapshot"] = _capture_snapshot(
                lambda: adapter.get_execution_snapshot(
                    symbol=symbol,
                    since=execution_since,
                    timeout_seconds=timeout,
                )
            )

        diagnostics["broker_state"] = classify_broker_state(
            open_order_snapshot=open_order_snapshot,
            position_snapshot=position_snapshot,
        )
        return diagnostics
    finally:
        coordinator.disconnect(timeout=disconnect_timeout)
        diagnostics["disconnect_result"] = _structured(coordinator.disconnect_result())
        diagnostics["connect_state"] = coordinator.connect_state
        diagnostics["shutdown_state"] = coordinator.shutdown_state
        diagnostics["thread_state"] = _thread_state(coordinator)
        if print_output:
            print(json.dumps(diagnostics, sort_keys=True, indent=2))


def classify_broker_state(
    *,
    open_order_snapshot: dict[str, Any] | None,
    position_snapshot: dict[str, Any] | None,
) -> str:
    if not open_order_snapshot or not position_snapshot:
        return "unknown"
    if open_order_snapshot.get("error") or position_snapshot.get("error"):
        return "unknown"
    if open_order_snapshot.get("open_buy_order_count") is None:
        return "unknown"
    if position_snapshot.get("qty") is None:
        return "unknown"
    if int(open_order_snapshot.get("open_buy_order_count") or 0) > 0:
        return "open_orders"
    if int(position_snapshot.get("qty") or 0) != 0:
        return "non_flat_position"
    return "clean"


def _validate_runtime_inputs(
    *,
    host: str,
    port: int,
    timeout: float,
    disconnect_timeout: float,
) -> None:
    if host not in IBKRRuntimeArbitrationCoordinator.LOCALHOSTS:
        raise ValueError("IBKR diagnostics are restricted to localhost")
    if port not in IBKRRuntimeArbitrationCoordinator.PAPER_PORTS:
        raise ValueError("IBKR diagnostics are restricted to paper ports")
    if not _is_positive_finite(timeout):
        raise ValueError("IBKR diagnostics require a finite positive timeout")
    if not _is_positive_finite(disconnect_timeout):
        raise ValueError(
            "IBKR diagnostics require a finite positive disconnect timeout"
        )


def _is_positive_finite(value: float | None) -> bool:
    return value is not None and isfinite(value) and value > 0


def _wait_for_thread_running(
    coordinator: IBKRRuntimeArbitrationCoordinator,
    *,
    timeout: float,
) -> None:
    with coordinator.condition:
        coordinator.condition.wait_for(
            lambda: coordinator.thread_owner.thread_state != "starting",
            timeout=timeout,
        )


def _capture_snapshot(callback) -> dict[str, Any]:
    try:
        return _structured(callback())
    except Exception as exc:
        return {
            "error": type(exc).__name__,
            "message": str(exc),
        }


def _thread_state(coordinator: IBKRRuntimeArbitrationCoordinator) -> dict[str, Any]:
    return {
        "thread_state": coordinator.thread_owner.thread_state,
        "target_run_count": coordinator.thread_owner.target_run_count,
        "ready": coordinator.thread_owner.thread_state == "running",
    }


def _structured(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return {
            field.name: _structured(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _structured(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_structured(item) for item in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _is_negative_position(pos) -> bool:
    try:
        return float(pos) < 0
    except (TypeError, ValueError):
        return str(pos).strip().startswith("-")


if __name__ == "__main__":
    run_ibkr_runtime_diagnostics()
