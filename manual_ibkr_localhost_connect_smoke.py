from __future__ import annotations

from dataclasses import dataclass

from ibkr_native_imports import load_ibkr_native_api
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 9107
DEFAULT_TIMEOUT = 5.0
SMOKE_EXECUTIONS = 0
NON_FATAL_CONNECT_STATUS_CODES = frozenset({2104, 2106, 2158})


class CoordinatorReadinessWrapper:
    def __init__(self, coordinator: IBKRRuntimeArbitrationCoordinator) -> None:
        self.coordinator = coordinator

    def nextValidId(self, order_id) -> bool:
        return self.coordinator.callback_connect_ready(
            message="next_valid_id",
        )

    def error(self, reqId, code, msg, *args) -> bool:
        if code in NON_FATAL_CONNECT_STATUS_CODES:
            return False
        return self.coordinator.callback_connect_error(
            message=str(msg),
            retryable=True,
        )

    def connectAck(self) -> bool:
        return False

    def connectionClosed(self) -> bool:
        return False


def build_native_readiness_wrapper_class(native_wrapper_class):
    class NativeCoordinatorReadinessWrapper(
        CoordinatorReadinessWrapper,
        native_wrapper_class,
    ):
        def __init__(self, coordinator: IBKRRuntimeArbitrationCoordinator) -> None:
            native_wrapper_class.__init__(self)
            CoordinatorReadinessWrapper.__init__(self, coordinator)

    return NativeCoordinatorReadinessWrapper


@dataclass(frozen=True, slots=True)
class ManualIBKRConnectSmokeBundle:
    coordinator: IBKRRuntimeArbitrationCoordinator
    wrapper: object
    client: object


def build_manual_smoke_bundle(
    *,
    native_api_loader=load_ibkr_native_api,
    coordinator_factory=IBKRRuntimeArbitrationCoordinator,
) -> ManualIBKRConnectSmokeBundle:
    native_api = native_api_loader()
    coordinator = coordinator_factory(enabled=True)
    wrapper_class = build_native_readiness_wrapper_class(native_api.e_wrapper)
    wrapper = wrapper_class(coordinator)
    client = native_api.e_client(wrapper)
    coordinator.client = client
    return ManualIBKRConnectSmokeBundle(
        coordinator=coordinator,
        wrapper=wrapper,
        client=client,
    )


def run_localhost_connect_smoke(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    timeout: float = DEFAULT_TIMEOUT,
    native_api_loader=load_ibkr_native_api,
    coordinator_factory=IBKRRuntimeArbitrationCoordinator,
):
    global SMOKE_EXECUTIONS
    SMOKE_EXECUTIONS += 1

    bundle = build_manual_smoke_bundle(
        native_api_loader=native_api_loader,
        coordinator_factory=coordinator_factory,
    )
    coordinator = bundle.coordinator

    print(f"IBKR manual localhost connect smoke host={host} port={port} client_id={client_id}")
    try:
        coordinator.connect(
            host=host,
            port=port,
            client_id=client_id,
            timeout=timeout,
        )
        if not coordinator.wait_for_completion(timeout=timeout):
            coordinator.timeout_connect(
                message="manual smoke timed out waiting for nextValidId",
                elapsed_ms=int(timeout * 1000),
            )
        result = coordinator.connect_result()
        print(f"terminal_result={result}")
        return result
    finally:
        joined = coordinator.disconnect(timeout=timeout)
        print(f"disconnect_joined={joined}")
        print(f"connect_state={coordinator.connect_state}")
        print(f"shutdown_state={coordinator.shutdown_state}")
        print(f"thread_state={coordinator.thread_owner.thread_state}")


if __name__ == "__main__":
    run_localhost_connect_smoke()
