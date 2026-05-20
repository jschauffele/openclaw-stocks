from __future__ import annotations

import json

from ibkr_fake_native_lifecycle_boundary import (
    build_fake_native_lifecycle_connect_report_fields,
)
from ibkr_native_imports import IBKRNativeAPI
from ibkr_runtime_assembly import IBKRRuntimeAssemblyConfig


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7497
DEFAULT_CLIENT_ID = 9107
DEFAULT_NEXT_VALID_ID = 601


class FakeLifecycleEClient:
    side_effect_calls: list[str] = []
    instances: list["FakeLifecycleEClient"] = []

    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper
        self.connect_calls = []
        self.run_calls = 0
        self.disconnect_calls = 0
        self.connected = False
        self.__class__.instances.append(self)

    def connect(self, *args, **kwargs) -> None:
        self.connect_calls.append((args, kwargs))
        self.connected = True

    def run(self) -> None:
        self.run_calls += 1

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        self.connected = False

    def isConnected(self) -> bool:
        return self.connected

    def placeOrder(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("placeOrder")

    def reqExecutions(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqExecutions")

    def reqAllOpenOrders(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqAllOpenOrders")

    def reqPositionsMulti(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqPositionsMulti")

    def reqAccountSummary(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqAccountSummary")


class FakeLifecycleEWrapper:
    pass


class FakeLifecycleContract:
    pass


class FakeLifecycleOrder:
    pass


class FakeLifecycleExecutionFilter:
    pass


def build_fake_native_api() -> IBKRNativeAPI:
    return IBKRNativeAPI(
        e_client=FakeLifecycleEClient,
        e_wrapper=FakeLifecycleEWrapper,
        contract=FakeLifecycleContract,
        order=FakeLifecycleOrder,
        execution_filter=FakeLifecycleExecutionFilter,
    )


def run_fake_native_lifecycle_evidence_smoke(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    client_id: int = DEFAULT_CLIENT_ID,
    next_valid_id: int = DEFAULT_NEXT_VALID_ID,
    fake_native_api: IBKRNativeAPI | None = None,
) -> dict:
    native_api = fake_native_api or build_fake_native_api()
    _reset_fake_client_observability(native_api.e_client)

    evidence = build_fake_native_lifecycle_connect_report_fields(
        IBKRRuntimeAssemblyConfig(
            enabled=True,
            host=host,
            port=port,
            client_id=client_id,
            order_id_start=next_valid_id,
        ),
        fake_native_api=native_api,
        next_valid_id=next_valid_id,
    )
    client = _latest_fake_client(native_api.e_client)

    return {
        "broker_name": "ibkr",
        "runtime_mode": "fake_native_manual_smoke",
        "host": host,
        "port": port,
        "client_id": client_id,
        "result": "blocked",
        "reason": "ibkr_runtime_submit_not_approved",
        "submit_approved": False,
        "reconciliation_approved": False,
        "submit_attempted": False,
        "reconciliation_attempted": False,
        "fake_connect_calls": client.connect_calls,
        "fake_disconnect_calls": client.disconnect_calls,
        "fake_run_calls": client.run_calls,
        "fake_side_effect_calls": list(
            getattr(native_api.e_client, "side_effect_calls", [])
        ),
        **evidence,
    }


def _reset_fake_client_observability(client_class: type) -> None:
    if hasattr(client_class, "side_effect_calls"):
        client_class.side_effect_calls = []
    if hasattr(client_class, "instances"):
        client_class.instances = []


def _latest_fake_client(client_class: type):
    instances = getattr(client_class, "instances", [])
    if not instances:
        raise RuntimeError("fake-native smoke did not construct a fake client")
    return instances[-1]


def main() -> None:
    report = run_fake_native_lifecycle_evidence_smoke()
    print(json.dumps(report, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
