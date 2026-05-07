from __future__ import annotations

import unittest
from unittest.mock import patch

from broker_interface import BrokerCapabilities
from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_timeout_injector import IBKRTimeoutInjector


class IBKRBrokerAdapterTests(unittest.TestCase):
    def test_capabilities_return_expected_ibkr_metadata(self) -> None:
        adapter = IBKRBrokerAdapter()

        self.assertEqual(
            adapter.get_capabilities(),
            BrokerCapabilities(
                broker_name="ibkr",
                supports_market_orders=False,
                supports_account_read=False,
                supports_positions_read=False,
                supports_open_orders_read=False,
                supports_paper_trading=True,
                lifecycle_async=True,
            ),
        )

    def test_skeleton_methods_fail_explicitly(self) -> None:
        adapter = IBKRBrokerAdapter()

        expected_message = "IBKR adapter skeleton only; not runtime-enabled"

        for method_name, args in [
            ("connect", ()),
            ("health_check", ()),
            ("disconnect", ()),
            ("get_account_buying_power", ()),
            ("get_existing_position", ("AAPL",)),
            ("get_open_buy_order_qty", ("AAPL",)),
            ("build_market_order", ("AAPL", 1)),
            ("submit_market_order", (object(),)),
            ("normalize_order_response", (object(),)),
        ]:
            with self.subTest(method=method_name):
                with self.assertRaisesRegex(NotImplementedError, expected_message):
                    getattr(adapter, method_name)(*args)

    def test_timeout_parameters_are_accepted_on_lifecycle_methods(self) -> None:
        adapter = IBKRBrokerAdapter()

        for method_name in ["connect", "health_check", "disconnect"]:
            with self.subTest(method=method_name):
                with self.assertRaisesRegex(
                    NotImplementedError,
                    "IBKR adapter skeleton only; not runtime-enabled",
                ):
                    getattr(adapter, method_name)(timeout_seconds=1.5)

    def test_constructor_stores_injected_dependencies_without_enabling_runtime(
        self,
    ) -> None:
        client = object()
        native_api = object()
        bridge = object()
        registry = object()
        timeout_injector = object()

        adapter = IBKRBrokerAdapter(
            client,
            native_api=native_api,
            bridge=bridge,
            registry=registry,
            timeout_injector=timeout_injector,
        )

        self.assertIs(adapter.client, client)
        self.assertIs(adapter.native_api, native_api)
        self.assertIs(adapter.bridge, bridge)
        self.assertIs(adapter.registry, registry)
        self.assertIs(adapter.timeout_injector, timeout_injector)
        self.assertEqual(adapter.enabled, False)

        with self.assertRaisesRegex(
            NotImplementedError,
            "IBKR adapter skeleton only; not runtime-enabled",
        ):
            adapter.connect()

    def test_constructor_builds_default_callback_scaffolding(self) -> None:
        adapter = IBKRBrokerAdapter()

        self.assertIsInstance(adapter.registry, IBKRPendingRequestRegistry)
        self.assertIsInstance(adapter.bridge, IBKRCallbackBridge)
        self.assertIsInstance(adapter.timeout_injector, IBKRTimeoutInjector)
        self.assertIs(adapter.bridge.registry, adapter.registry)
        self.assertIs(adapter.timeout_injector.registry, adapter.registry)

    def test_constructor_preserves_injected_registry_with_default_bridge_and_timeout(
        self,
    ) -> None:
        registry = IBKRPendingRequestRegistry()

        adapter = IBKRBrokerAdapter(registry=registry)

        self.assertIs(adapter.registry, registry)
        self.assertIs(adapter.bridge.registry, registry)
        self.assertIs(adapter.timeout_injector.registry, registry)

    def test_enabled_true_alone_does_not_implement_runtime_behavior(self) -> None:
        adapter = IBKRBrokerAdapter(enabled=True)

        self.assertEqual(adapter.enabled, True)
        with self.assertRaisesRegex(
            NotImplementedError,
            "IBKR adapter skeleton only; not runtime-enabled",
        ):
            adapter.connect()

    def test_constructor_does_not_call_native_import_loader(self) -> None:
        with patch(
            "ibkr_native_imports.load_ibkr_native_api",
            side_effect=AssertionError("native loader should not be called"),
        ):
            adapter = IBKRBrokerAdapter()

        self.assertEqual(adapter.enabled, False)


if __name__ == "__main__":
    unittest.main()
