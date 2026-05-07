from __future__ import annotations

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
