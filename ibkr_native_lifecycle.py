from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass

from broker_interface import BrokerLifecycleResult
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_timeout_injector import IBKRTimeoutInjector


class IBKRWrapperBridge:
    def __init__(self, bridge: IBKRCallbackBridge) -> None:
        self.bridge = bridge

    def nextValidId(self, order_id) -> bool:
        return self.bridge.next_valid_id(order_id=order_id)

    def error(self, reqId, code, msg, *args) -> bool:
        return self.bridge.connect_error(
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
        routed_open_order = self.bridge.open_order_status_update(
            order_id=orderId,
            perm_id=permId,
            status=status,
        )
        routed_order = self.bridge.order_status(order_id=orderId, status=status)
        return routed_open_order or routed_order

    def connect_ready(
        self,
        *,
        message: str = "connect_ready",
        elapsed_ms: int | None = None,
    ) -> bool:
        return self.bridge.connect_ready(
            message=message,
            elapsed_ms=elapsed_ms,
        )

    def connect_error(
        self,
        *,
        message: str = "connect_error",
        retryable: bool = True,
        elapsed_ms: int | None = None,
    ) -> bool:
        return self.bridge.connect_error(
            message=message,
            retryable=retryable,
            elapsed_ms=elapsed_ms,
        )


@dataclass(frozen=True, slots=True)
class IBKRNativeClientBundle:
    wrapper: IBKRWrapperBridge
    client: object


def build_ibkr_native_client_bundle(
    *,
    native_api,
    bridge: IBKRCallbackBridge,
) -> IBKRNativeClientBundle:
    wrapper = IBKRWrapperBridge(bridge)
    client = native_api.e_client(wrapper)
    return IBKRNativeClientBundle(
        wrapper=wrapper,
        client=client,
    )


def _is_negative_position(pos) -> bool:
    try:
        return float(pos) < 0
    except (TypeError, ValueError):
        return str(pos).strip().startswith("-")


class IBKRClientLifecycleController:
    def __init__(
        self,
        *,
        client,
        bridge: IBKRCallbackBridge,
        timeout_injector: IBKRTimeoutInjector,
    ) -> None:
        self.client = client
        self.bridge = bridge
        self.timeout_injector = timeout_injector

    def connect(
        self,
        *,
        host: str,
        port: int,
        client_id: int,
    ) -> None:
        self.bridge.begin_lifecycle(operation="connect")
        self.client.connect(host, port, client_id)

    def complete_connect(self) -> BrokerLifecycleResult:
        return self.bridge.complete_lifecycle(operation="connect")

    def connect_timeout(
        self,
        *,
        message: str = "connect_timeout",
        elapsed_ms: int | None = None,
    ) -> BrokerLifecycleResult:
        return self.timeout_injector.inject_lifecycle_timeout(
            operation="connect",
            message=message,
            elapsed_ms=elapsed_ms,
        )

    def health_check(self) -> BrokerLifecycleResult:
        connected = bool(self.client.isConnected())
        if connected:
            return BrokerLifecycleResult(
                broker_name="ibkr",
                operation="health_check",
                passed=True,
                reason="ibkr_client_connected",
                message="IBKR fake client reports connected",
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
            message="IBKR fake client reports disconnected",
            connected=False,
            retryable=True,
            elapsed_ms=0,
            raw_error=None,
        )

    def disconnect(self) -> BrokerLifecycleResult:
        self.client.disconnect()
        return BrokerLifecycleResult(
            broker_name="ibkr",
            operation="disconnect",
            passed=True,
            reason="ibkr_client_disconnected",
            message="IBKR fake client disconnect requested",
            connected=False,
            retryable=False,
            elapsed_ms=0,
            raw_error=None,
        )


class IBKRRuntimeThreadOwner:
    def __init__(
        self,
        *,
        lock: threading.RLock | None = None,
        condition: threading.Condition | None = None,
    ) -> None:
        self.lock = lock or threading.RLock()
        self.condition = condition or threading.Condition(self.lock)
        self.thread_state = "not_started"
        self.shutdown_state = "active"
        self.thread: threading.Thread | None = None
        self.target_run_count = 0
        self.target_exception: BaseException | None = None

    def start_thread(self, target: Callable[[], None]) -> None:
        with self.lock:
            if self.thread_state != "not_started":
                raise RuntimeError(f"IBKR runtime thread already {self.thread_state}")
            self.thread_state = "starting"
            self.thread = threading.Thread(
                target=self._run_target,
                args=(target,),
                name="ibkr-runtime-owner",
                daemon=True,
            )
            thread = self.thread
        thread.start()

    def _run_target(self, target: Callable[[], None]) -> None:
        with self.lock:
            self.thread_state = "running"
            self.target_run_count += 1
            self.condition.notify_all()
        try:
            target()
        except BaseException as exc:
            with self.lock:
                self.target_exception = exc
        finally:
            self.mark_thread_exited()

    def mark_thread_exited(self) -> None:
        with self.lock:
            self.thread_state = "stopped"
            self.condition.notify_all()

    def request_shutdown(
        self,
        stop_signal: Callable[[], None] | None = None,
    ) -> None:
        with self.lock:
            if self.shutdown_state != "active":
                raise RuntimeError(f"IBKR runtime shutdown already {self.shutdown_state}")
            self.shutdown_state = "stopping"
            self.condition.notify_all()
        if stop_signal is not None:
            stop_signal()

    def complete_shutdown(self) -> None:
        with self.lock:
            self.shutdown_state = "complete"
            self.condition.notify_all()

    def join_thread(self, timeout: float | None = None) -> bool:
        with self.lock:
            thread = self.thread
        if thread is None:
            raise RuntimeError("IBKR runtime thread has not been started")
        thread.join(timeout=timeout)
        joined = not thread.is_alive()
        if joined:
            with self.lock:
                if self.shutdown_state == "stopping":
                    self.shutdown_state = "complete"
                    self.condition.notify_all()
        return joined
