from __future__ import annotations

import unittest

from ibkr_lifecycle_connect_evidence import (
    record_fake_native_lifecycle_connect_evidence,
)
from ibkr_native_imports import IBKRNativeAPI
from ibkr_runtime_assembly import IBKRRuntimeAssemblyConfig, assemble_ibkr_runtime


class FakeEClient:
    side_effect_calls: list[str] = []

    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper
        self.connect_calls = []
        self.run_calls = 0
        self.disconnect_calls = 0
        self.connected = False

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


class IBKRLifecycleConnectEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeEClient.side_effect_calls = []

    def test_records_truthful_fake_native_lifecycle_connect_evidence(self) -> None:
        assembly = assemble_ibkr_runtime(
            IBKRRuntimeAssemblyConfig(
                enabled=True,
                host="127.0.0.1",
                port=7497,
                client_id=9171,
                order_id_start=601,
            ),
            native_api=fake_native_api(),
        )

        evidence = record_fake_native_lifecycle_connect_evidence(assembly)
        fields = evidence.as_report_fields()

        self.assertEqual(
            assembly.native_bundle.client.connect_calls,
            [(("127.0.0.1", 7497, 9171), {})],
        )
        self.assertEqual(assembly.bridge.latest_next_valid_id, 601)
        self.assertEqual(assembly.native_bundle.client.disconnect_calls, 1)
        self.assertEqual(assembly.native_bundle.client.run_calls, 0)
        self.assertEqual(FakeEClient.side_effect_calls, [])
        self.assertEqual(fields["connect_result"]["passed"], True)
        self.assertEqual(fields["connect_result"]["reason"], "connect_ready")
        self.assertEqual(fields["connect_result"]["message"], "next_valid_id")
        self.assertEqual(fields["connect_result"]["connected"], True)
        self.assertEqual(fields["connection_completion_source"], "next_valid_id")
        self.assertEqual(fields["next_valid_id"], 601)
        self.assertEqual(fields["run_thread_state"], "not_started")
        self.assertEqual(fields["disconnect_joined"], False)
        self.assertEqual(fields["disconnect_result"]["passed"], True)
        self.assertEqual(
            fields["disconnect_result"]["reason"],
            "ibkr_client_disconnected",
        )
        self.assertEqual(fields["disconnect_result"]["connected"], False)
        self.assertEqual(fields["shutdown_state"], "no_runtime_thread_started")

    def test_custom_next_valid_id_is_used_for_fake_readiness(self) -> None:
        assembly = assemble_ibkr_runtime(
            IBKRRuntimeAssemblyConfig(enabled=True),
            native_api=fake_native_api(),
        )

        evidence = record_fake_native_lifecycle_connect_evidence(
            assembly,
            next_valid_id=812,
        )

        self.assertEqual(assembly.bridge.latest_next_valid_id, 812)
        self.assertEqual(evidence.next_valid_id, 812)
        self.assertEqual(evidence.connection_completion_source, "next_valid_id")

    def test_rejects_disabled_assembly_before_fake_lifecycle_calls(self) -> None:
        assembly = assemble_ibkr_runtime(native_api=fake_native_api())

        with self.assertRaisesRegex(ValueError, "requires enabled fake-native assembly"):
            record_fake_native_lifecycle_connect_evidence(assembly)

        self.assertIsNone(assembly.native_bundle)
        self.assertIsNone(assembly.runtime_coordinator)

    def test_helper_does_not_load_real_ibapi(self) -> None:
        def fail_loader() -> IBKRNativeAPI:
            raise AssertionError("helper test must not load real ibapi")

        assembly = assemble_ibkr_runtime(
            IBKRRuntimeAssemblyConfig(enabled=True),
            native_api=fake_native_api(),
            native_api_loader=fail_loader,
        )

        evidence = record_fake_native_lifecycle_connect_evidence(assembly)

        self.assertEqual(evidence.connect_result["passed"], True)


if __name__ == "__main__":
    unittest.main()
