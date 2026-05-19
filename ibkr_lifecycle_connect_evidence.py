from __future__ import annotations

from dataclasses import dataclass

from broker_interface import BrokerLifecycleResult
from ibkr_native_lifecycle import IBKRClientLifecycleController
from ibkr_runtime_assembly import IBKRRuntimeAssembly


@dataclass(frozen=True, slots=True)
class IBKRLifecycleConnectEvidence:
    connect_result: dict
    connection_completion_source: str
    next_valid_id: int
    run_thread_state: str
    disconnect_joined: bool
    disconnect_result: dict
    shutdown_state: str

    def as_report_fields(self) -> dict:
        return {
            "connect_result": self.connect_result,
            "connection_completion_source": self.connection_completion_source,
            "next_valid_id": self.next_valid_id,
            "run_thread_state": self.run_thread_state,
            "disconnect_joined": self.disconnect_joined,
            "disconnect_result": self.disconnect_result,
            "shutdown_state": self.shutdown_state,
        }


def record_fake_native_lifecycle_connect_evidence(
    assembly: IBKRRuntimeAssembly,
    *,
    next_valid_id: int | None = None,
) -> IBKRLifecycleConnectEvidence:
    if not assembly.enabled:
        raise ValueError("IBKR lifecycle evidence requires enabled fake-native assembly")
    if assembly.native_bundle is None or assembly.runtime_coordinator is None:
        raise ValueError("IBKR lifecycle evidence requires native runtime components")

    readiness_order_id = (
        next_valid_id
        if next_valid_id is not None
        else assembly.config.order_id_start
        if assembly.config.order_id_start is not None
        else 1
    )
    controller = IBKRClientLifecycleController(
        client=assembly.native_bundle.client,
        bridge=assembly.bridge,
        timeout_injector=assembly.timeout_injector,
    )

    controller.connect(
        host=assembly.config.host,
        port=assembly.config.port,
        client_id=assembly.config.client_id,
    )
    assembly.native_bundle.wrapper.nextValidId(readiness_order_id)
    connect_result = controller.complete_connect()
    disconnect_result = controller.disconnect()

    return IBKRLifecycleConnectEvidence(
        connect_result=_lifecycle_result_payload(connect_result),
        connection_completion_source="next_valid_id",
        next_valid_id=readiness_order_id,
        run_thread_state="not_started",
        disconnect_joined=False,
        disconnect_result=_lifecycle_result_payload(disconnect_result),
        shutdown_state="no_runtime_thread_started",
    )


def _lifecycle_result_payload(result: BrokerLifecycleResult) -> dict:
    return {
        "passed": result.passed,
        "reason": result.reason,
        "message": result.message,
        "connected": result.connected,
        "retryable": result.retryable,
        "elapsed_ms": result.elapsed_ms,
    }
