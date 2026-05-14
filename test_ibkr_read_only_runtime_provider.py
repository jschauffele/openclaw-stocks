from __future__ import annotations

import unittest

from ibkr_read_only_runtime_provider import (
    IBKRReadOnlyRuntimeProvider,
    IBKRReadOnlyRuntimeProviderConfig,
)


class IBKRReadOnlyRuntimeProviderTests(unittest.TestCase):
    def test_disabled_provider_does_not_call_diagnostics(self) -> None:
        calls = []

        def diagnostics_runner(**kwargs):
            calls.append(kwargs)
            raise AssertionError("disabled provider must not call diagnostics")

        provider = IBKRReadOnlyRuntimeProvider(
            IBKRReadOnlyRuntimeProviderConfig(enabled=False),
            diagnostics_runner=diagnostics_runner,
        )

        result = provider.get_runtime_diagnostics()

        self.assertEqual(calls, [])
        self.assertEqual(result["provider_status"], "disabled")
        self.assertEqual(result["enabled"], False)
        self.assertEqual(result["broker_state"], "unknown")
        self.assertIsNone(result["connection_result"])

    def test_enabled_provider_calls_diagnostics_with_config_values(self) -> None:
        calls = []

        def diagnostics_runner(**kwargs):
            calls.append(kwargs)
            return {
                "connection_result": {"passed": True},
                "connection_completion_source": "callback",
                "next_valid_id": 701,
                "open_order_snapshot": {"open_buy_order_count": 0},
                "position_snapshot": {"qty": 0},
                "broker_state": "clean",
                "disconnect_result": {"passed": True},
                "connect_state": "disconnected",
                "shutdown_state": "complete",
                "thread_state": {"thread_state": "stopped"},
            }

        config = IBKRReadOnlyRuntimeProviderConfig(
            enabled=True,
            host="localhost",
            port=4002,
            client_id=9234,
            timeout=1.25,
            disconnect_timeout=0.75,
            symbol="MSFT",
            include_executions=True,
            execution_since="20260512 09:30:00",
        )
        provider = IBKRReadOnlyRuntimeProvider(
            config,
            diagnostics_runner=diagnostics_runner,
        )

        result = provider.get_runtime_diagnostics()

        self.assertEqual(
            calls,
            [
                {
                    "host": "localhost",
                    "port": 4002,
                    "client_id": 9234,
                    "timeout": 1.25,
                    "disconnect_timeout": 0.75,
                    "symbol": "MSFT",
                    "include_execution_snapshot": True,
                    "execution_since": "20260512 09:30:00",
                    "print_output": False,
                }
            ],
        )
        self.assertEqual(result["provider_status"], "enabled")
        self.assertEqual(result["enabled"], True)
        self.assertEqual(result["broker_state"], "clean")

    def test_non_clean_broker_state_is_returned_not_cleaned(self) -> None:
        def diagnostics_runner(**kwargs):
            return {
                "connection_result": {"passed": True},
                "connection_completion_source": "callback",
                "next_valid_id": 701,
                "open_order_snapshot": {
                    "open_buy_order_count": 1,
                    "open_buy_order_qty": 3,
                },
                "position_snapshot": {"qty": 0},
                "broker_state": "open_orders",
                "disconnect_result": {"passed": True},
                "connect_state": "disconnected",
                "shutdown_state": "complete",
                "thread_state": {"thread_state": "stopped"},
            }

        provider = IBKRReadOnlyRuntimeProvider(
            IBKRReadOnlyRuntimeProviderConfig(enabled=True),
            diagnostics_runner=diagnostics_runner,
        )

        result = provider.read_broker_state()

        self.assertEqual(result["broker_state"], "open_orders")
        self.assertEqual(result["open_order_snapshot"]["open_buy_order_qty"], 3)
        self.assertFalse(hasattr(provider, "build_market_order"))
        self.assertFalse(hasattr(provider, "submit_market_order"))
        self.assertFalse(hasattr(provider, "cancel_order"))
        self.assertFalse(hasattr(provider, "flatten"))

    def test_provider_exposes_no_submit_build_cancel_flatten_methods(self) -> None:
        provider = IBKRReadOnlyRuntimeProvider()

        for method_name in [
            "build_market_order",
            "submit_market_order",
            "cancel_order",
            "cancel",
            "flatten",
            "flatten_position",
        ]:
            with self.subTest(method=method_name):
                self.assertFalse(hasattr(provider, method_name))

    def test_diagnostics_exception_returns_unknown_error_state(self) -> None:
        def diagnostics_runner(**kwargs):
            raise TimeoutError("diagnostics timed out")

        provider = IBKRReadOnlyRuntimeProvider(
            IBKRReadOnlyRuntimeProviderConfig(
                enabled=True,
                include_executions=True,
            ),
            diagnostics_runner=diagnostics_runner,
        )

        result = provider.get_runtime_diagnostics()

        self.assertEqual(result["provider_status"], "error")
        self.assertEqual(result["enabled"], True)
        self.assertEqual(result["broker_state"], "unknown")
        self.assertEqual(result["error"]["type"], "TimeoutError")
        self.assertEqual(result["error"]["message"], "diagnostics timed out")
        self.assertIn("execution_snapshot", result)
        self.assertIsNone(result["execution_snapshot"])


if __name__ == "__main__":
    unittest.main()
