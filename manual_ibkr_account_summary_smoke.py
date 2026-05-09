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
DEFAULT_CLIENT_ID = 9112
DEFAULT_TIMEOUT = 5.0
DEFAULT_ACCOUNT_REQUEST_ID_START = 8101
NON_FATAL_CONNECT_STATUS_CODES = frozenset({2104, 2106, 2158})


@dataclass
class AccountSummaryCallbackRecorder:
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


class RecordingAccountSummaryBridge(IBKRCallbackBridge):
    def __init__(
        self,
        registry: IBKRPendingRequestRegistry,
        *,
        request_coordinator: IBKRRequestCoordinator,
        recorder: AccountSummaryCallbackRecorder,
    ) -> None:
        super().__init__(
            registry,
            request_coordinator=request_coordinator,
        )
        self.recorder = recorder

    def begin_account_snapshot(self, *, request_id: object) -> None:
        self.recorder.record("begin_account_snapshot", request_id=request_id)
        return super().begin_account_snapshot(request_id=request_id)

    def account_summary(
        self,
        *,
        request_id: object,
        buying_power: object | None = None,
        account: object | None = None,
        tag: object | None = None,
        value: object | None = None,
        currency: object | None = None,
    ) -> bool:
        routed = super().account_summary(
            request_id=request_id,
            buying_power=buying_power,
            account=account,
            tag=tag,
            value=value,
            currency=currency,
        )
        self.recorder.record(
            "accountSummary",
            request_id=request_id,
            account=account,
            tag=tag,
            value=value,
            currency=currency,
            routed=routed,
        )
        return routed

    def account_summary_end(self, *, request_id: object) -> bool:
        routed = super().account_summary_end(request_id=request_id)
        self.recorder.record(
            "accountSummaryEnd",
            request_id=request_id,
            routed=routed,
        )
        return routed


class AccountSummarySmokeWrapper:
    def __init__(
        self,
        *,
        coordinator: IBKRRuntimeArbitrationCoordinator,
        bridge: RecordingAccountSummaryBridge,
        recorder: AccountSummaryCallbackRecorder,
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

    def connectAck(self) -> bool:
        self.recorder.record("connectAck")
        return False

    def connectionClosed(self) -> bool:
        self.recorder.record("connectionClosed")
        return False


def build_native_account_summary_wrapper_class(native_wrapper_class):
    class NativeAccountSummarySmokeWrapper(
        AccountSummarySmokeWrapper,
        native_wrapper_class,
    ):
        def __init__(
            self,
            *,
            coordinator: IBKRRuntimeArbitrationCoordinator,
            bridge: RecordingAccountSummaryBridge,
            recorder: AccountSummaryCallbackRecorder,
        ) -> None:
            native_wrapper_class.__init__(self)
            AccountSummarySmokeWrapper.__init__(
                self,
                coordinator=coordinator,
                bridge=bridge,
                recorder=recorder,
            )

    return NativeAccountSummarySmokeWrapper


def run_localhost_account_summary_smoke(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    timeout: float = DEFAULT_TIMEOUT,
    account_request_id_start: int = DEFAULT_ACCOUNT_REQUEST_ID_START,
):
    native_api = load_ibkr_native_api()
    recorder = AccountSummaryCallbackRecorder()
    registry = IBKRPendingRequestRegistry()
    request_coordinator = IBKRRequestCoordinator(registry=registry)
    bridge = RecordingAccountSummaryBridge(
        registry,
        request_coordinator=request_coordinator,
        recorder=recorder,
    )
    coordinator = IBKRRuntimeArbitrationCoordinator(enabled=True)
    wrapper_class = build_native_account_summary_wrapper_class(native_api.e_wrapper)
    wrapper = wrapper_class(
        coordinator=coordinator,
        bridge=bridge,
        recorder=recorder,
    )
    client = native_api.e_client(wrapper)
    coordinator.client = client
    adapter = IBKRBrokerAdapter(
        client=client,
        bridge=bridge,
        registry=registry,
        request_coordinator=request_coordinator,
        coordinator=coordinator,
        account_summary_request_id_start=account_request_id_start,
    )

    print(
        "IBKR manual localhost account-summary smoke "
        f"host={host} port={port} client_id={client_id} "
        f"account_request_id_start={account_request_id_start}"
    )
    terminal_result = None
    account_state = None
    account_exception = None
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
                message="account summary smoke timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )
        terminal_result = coordinator.connect_result()
        print(f"terminal_result={terminal_result}")

        if terminal_result is None or not terminal_result.passed:
            print("account_summary_skipped=connect_failed")
            return None

        try:
            account_state = adapter.get_account_buying_power(timeout_seconds=timeout)
            requested_id = adapter._next_account_summary_request_id - 1
            print(f"request_id={requested_id}")
            print(f"account_state={account_state}")
        except Exception as exc:
            requested_id = adapter._next_account_summary_request_id - 1
            account_exception = exc
            print(f"request_id={requested_id}")
            print(f"account_exception_type={type(exc).__name__}")
            print(f"account_exception={exc!r}")

        if requested_id is not None:
            print(f"completion_source={request_coordinator.completed_by(requested_id)}")
            print(f"retained_result={request_coordinator.result(requested_id)!r}")
            print(f"pending_request={request_coordinator.has_pending_request(requested_id)}")
        print(f"callback_count={len(recorder.events)}")
        for event in recorder.events:
            print(f"callback_event={event}")
        return account_state
    finally:
        joined = coordinator.disconnect(timeout=timeout)
        print(f"disconnect_joined={joined}")
        print(f"connect_state={coordinator.connect_state}")
        print(f"shutdown_state={coordinator.shutdown_state}")
        print(f"thread_state={coordinator.thread_owner.thread_state}")
        print(f"disconnect_result={coordinator.disconnect_result()}")


if __name__ == "__main__":
    run_localhost_account_summary_smoke()
