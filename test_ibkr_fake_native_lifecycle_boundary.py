from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from ibkr_fake_native_lifecycle_boundary import (
    build_fake_native_lifecycle_connect_report_fields,
    build_fake_native_lifecycle_connect_report_fields_from_config,
)
from ibkr_native_imports import IBKRNativeAPI
from ibkr_runtime_assembly import IBKRRuntimeAssemblyConfig


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


class IBKRFakeNativeLifecycleBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeEClient.side_effect_calls = []

    def test_builds_report_ready_fields_from_fake_native_lifecycle_evidence(self):
        fields = build_fake_native_lifecycle_connect_report_fields(
            IBKRRuntimeAssemblyConfig(
                enabled=True,
                host="127.0.0.1",
                port=7497,
                client_id=9188,
                order_id_start=700,
            ),
            fake_native_api=fake_native_api(),
        )

        self.assertEqual(
            fields,
            {
                "assembly_enabled": True,
                "fake_native": True,
                "connect_attempted": True,
                "run_loop_started": False,
                "connect_result": {
                    "passed": True,
                    "reason": "connect_ready",
                    "message": "next_valid_id",
                    "connected": True,
                    "retryable": False,
                    "elapsed_ms": None,
                },
                "connection_completion_source": "next_valid_id",
                "next_valid_id": 700,
                "run_thread_state": "not_started",
                "disconnect_joined": False,
                "disconnect_result": {
                    "passed": True,
                    "reason": "ibkr_client_disconnected",
                    "message": "IBKR fake client disconnect requested",
                    "connected": False,
                    "retryable": False,
                    "elapsed_ms": 0,
                },
                "shutdown_state": "no_runtime_thread_started",
            },
        )
        self.assertEqual(FakeEClient.side_effect_calls, [])

    def test_custom_next_valid_id_overrides_config_order_id_start(self):
        fields = build_fake_native_lifecycle_connect_report_fields(
            IBKRRuntimeAssemblyConfig(
                enabled=True,
                order_id_start=700,
            ),
            fake_native_api=fake_native_api(),
            next_valid_id=711,
        )

        self.assertEqual(fields["next_valid_id"], 711)
        self.assertEqual(fields["connection_completion_source"], "next_valid_id")

    def test_config_module_boundary_maps_to_fake_native_report_fields(self):
        config_module = type(
            "FakeConfig",
            (),
            {
                "OPENCLAW_IBKR_RUNTIME_ENABLED": True,
                "OPENCLAW_IBKR_RUNTIME_MODE": "paper_localhost",
                "OPENCLAW_IBKR_RUNTIME_HOST": "127.0.0.1",
                "OPENCLAW_IBKR_RUNTIME_PORT": 7497,
                "OPENCLAW_IBKR_RUNTIME_CLIENT_ID": 9188,
                "OPENCLAW_IBKR_RUNTIME_ACCOUNT": "",
                "OPENCLAW_IBKR_RUNTIME_MODEL_CODE": "",
                "OPENCLAW_IBKR_RUNTIME_ORDER_ID_START": 901,
                "OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS": 5.0,
            },
        )

        fields = build_fake_native_lifecycle_connect_report_fields_from_config(
            config_module,
            fake_native_api=fake_native_api(),
        )

        self.assertEqual(fields["next_valid_id"], 901)
        self.assertEqual(fields["connect_result"]["reason"], "connect_ready")
        self.assertEqual(
            fields["disconnect_result"]["reason"],
            "ibkr_client_disconnected",
        )

    def test_disabled_config_rejects_before_fake_lifecycle_evidence(self):
        with self.assertRaisesRegex(ValueError, "requires enabled fake-native assembly"):
            build_fake_native_lifecycle_connect_report_fields(
                IBKRRuntimeAssemblyConfig(enabled=False),
                fake_native_api=fake_native_api(),
            )

        self.assertEqual(FakeEClient.side_effect_calls, [])

    def test_boundary_does_not_expose_default_native_loading_path(self):
        with patch(
            "ibkr_fake_native_lifecycle_boundary._reject_native_api_load",
            side_effect=AssertionError("real native loader must not be called"),
        ):
            fields = build_fake_native_lifecycle_connect_report_fields(
                IBKRRuntimeAssemblyConfig(enabled=True),
                fake_native_api=fake_native_api(),
            )

        self.assertEqual(fields["connect_result"]["passed"], True)

    def test_boundary_requires_injected_fake_native_api(self):
        with self.assertRaisesRegex(
            ValueError,
            "requires injected native API",
        ):
            build_fake_native_lifecycle_connect_report_fields(
                IBKRRuntimeAssemblyConfig(enabled=True),
                fake_native_api=None,
            )

    def test_boundary_does_not_import_main_or_runtime_orchestration_modules(self):
        source = Path(__file__).with_name(
            "ibkr_fake_native_lifecycle_boundary.py"
        ).read_text(encoding="utf-8")

        prohibited_imports = (
            "import main",
            "from main",
            "broker_factory",
            "market_data",
            "strategy_engine",
            "risk_engine",
            "state_manager",
            "observation_logger",
            "ibkr_submit_reconciliation_workflow",
        )
        for prohibited_import in prohibited_imports:
            with self.subTest(prohibited_import=prohibited_import):
                self.assertNotIn(prohibited_import, source)

        with patch(
            "ibkr_fake_native_lifecycle_boundary.record_fake_native_lifecycle_connect_evidence",
            side_effect=AssertionError("stop after assembly construction"),
        ):
            with self.assertRaisesRegex(AssertionError, "stop after assembly"):
                build_fake_native_lifecycle_connect_report_fields(
                    IBKRRuntimeAssemblyConfig(enabled=True),
                    fake_native_api=fake_native_api(),
                )

        self.assertEqual(FakeEClient.side_effect_calls, [])


if __name__ == "__main__":
    unittest.main()
