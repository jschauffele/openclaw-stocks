from __future__ import annotations

import unittest

from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import IBKRNativeAPI
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_runtime_assembly import (
    IBKRRuntimeAssemblyConfig,
    assemble_ibkr_runtime,
)
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator
from ibkr_timeout_injector import IBKRTimeoutInjector


class FakeEClient:
    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper
        self.connect_calls = []
        self.run_calls = 0
        self.disconnect_calls = 0

    def connect(self, *args, **kwargs) -> None:
        self.connect_calls.append((args, kwargs))

    def run(self) -> None:
        self.run_calls += 1

    def disconnect(self) -> None:
        self.disconnect_calls += 1

    def isConnected(self) -> bool:
        return False


class FakeEWrapper:
    pass


class FakeContract:
    pass


class FakeOrder:
    pass


class FakeExecutionFilter:
    pass


def fake_native_api() -> IBKRNativeAPI:
    return IBKRNativeAPI(
        e_client=FakeEClient,
        e_wrapper=FakeEWrapper,
        contract=FakeContract,
        order=FakeOrder,
        execution_filter=FakeExecutionFilter,
    )


class IBKRRuntimeAssemblyTests(unittest.TestCase):
    def test_disabled_default_assembles_without_loading_native_api(self) -> None:
        def fail_loader() -> IBKRNativeAPI:
            raise AssertionError("disabled assembly must not load native IBKR API")

        assembly = assemble_ibkr_runtime(native_api_loader=fail_loader)

        self.assertFalse(assembly.enabled)
        self.assertIsNone(assembly.native_api)
        self.assertIsNone(assembly.native_bundle)
        self.assertIsNone(assembly.runtime_coordinator)
        self.assertIsInstance(assembly.adapter, IBKRBrokerAdapter)
        self.assertIsNone(assembly.adapter.client)
        self.assertIsNone(assembly.adapter.coordinator)

    def test_disabled_default_wires_shared_non_runtime_components(self) -> None:
        assembly = assemble_ibkr_runtime()

        self.assertIsInstance(assembly.registry, IBKRPendingRequestRegistry)
        self.assertIsInstance(assembly.request_coordinator, IBKRRequestCoordinator)
        self.assertIsInstance(assembly.bridge, IBKRCallbackBridge)
        self.assertIsInstance(assembly.timeout_injector, IBKRTimeoutInjector)
        self.assertIs(assembly.adapter.registry, assembly.registry)
        self.assertIs(assembly.adapter.request_coordinator, assembly.request_coordinator)
        self.assertIs(assembly.adapter.bridge, assembly.bridge)
        self.assertIs(assembly.adapter.timeout_injector, assembly.timeout_injector)
        self.assertIs(assembly.request_coordinator.registry, assembly.registry)
        self.assertIs(assembly.bridge.registry, assembly.registry)
        self.assertIs(assembly.bridge.request_coordinator, assembly.request_coordinator)

    def test_enabled_fake_native_assembles_runtime_without_connecting(self) -> None:
        config = IBKRRuntimeAssemblyConfig(
            enabled=True,
            host="127.0.0.1",
            port=7497,
            client_id=9120,
            order_id_start=100,
        )

        assembly = assemble_ibkr_runtime(
            config,
            native_api=fake_native_api(),
        )

        self.assertTrue(assembly.enabled)
        self.assertIsNotNone(assembly.native_bundle)
        self.assertIsInstance(
            assembly.runtime_coordinator,
            IBKRRuntimeArbitrationCoordinator,
        )
        self.assertIs(assembly.adapter.client, assembly.native_bundle.client)
        self.assertIs(assembly.adapter.native_api, assembly.native_api)
        self.assertIs(assembly.adapter.coordinator, assembly.runtime_coordinator)
        self.assertEqual(assembly.adapter.host, "127.0.0.1")
        self.assertEqual(assembly.adapter.port, 7497)
        self.assertEqual(assembly.adapter.client_id, 9120)
        self.assertEqual(assembly.native_bundle.client.connect_calls, [])
        self.assertEqual(assembly.native_bundle.client.run_calls, 0)
        self.assertEqual(assembly.native_bundle.client.disconnect_calls, 0)

    def test_enabled_loader_is_called_once_when_native_api_not_injected(self) -> None:
        calls = []

        def loader() -> IBKRNativeAPI:
            calls.append("called")
            return fake_native_api()

        assembly = assemble_ibkr_runtime(
            IBKRRuntimeAssemblyConfig(enabled=True),
            native_api_loader=loader,
        )

        self.assertEqual(calls, ["called"])
        self.assertIsNotNone(assembly.native_api)
        self.assertIsNotNone(assembly.native_bundle)

    def test_localhost_and_paper_port_guardrails_apply_before_native_load(self) -> None:
        def fail_loader() -> IBKRNativeAPI:
            raise AssertionError("invalid config must fail before native API load")

        with self.assertRaisesRegex(ValueError, "restricted to localhost"):
            assemble_ibkr_runtime(
                IBKRRuntimeAssemblyConfig(enabled=True, host="example.com"),
                native_api_loader=fail_loader,
            )

        with self.assertRaisesRegex(ValueError, "restricted to paper ports"):
            assemble_ibkr_runtime(
                IBKRRuntimeAssemblyConfig(enabled=True, port=7496),
                native_api_loader=fail_loader,
            )

    def test_timeout_guardrail_is_deterministic(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite positive timeout"):
            assemble_ibkr_runtime(
                IBKRRuntimeAssemblyConfig(connect_timeout_seconds=0),
            )


if __name__ == "__main__":
    unittest.main()
