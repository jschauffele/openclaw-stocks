from __future__ import annotations

import threading
import unittest
from types import SimpleNamespace

from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import IBKRDependencyUnavailable, load_ibkr_native_api
from ibkr_native_lifecycle import (
    IBKRWrapperBridge,
    build_ibkr_native_client_bundle,
)


class CompatibilityFakeEClient:
    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper
        self.connect_calls = 0
        self.run_calls = 0

    def connect(self, *args, **kwargs) -> None:
        self.connect_calls += 1

    def run(self) -> None:
        self.run_calls += 1

    def isConnected(self) -> bool:
        return False


class IBKRWrapperCompatibilityTests(unittest.TestCase):
    def test_fake_eclient_accepts_current_wrapper_shape(self) -> None:
        bridge = IBKRCallbackBridge()
        bundle = build_ibkr_native_client_bundle(
            native_api=SimpleNamespace(e_client=CompatibilityFakeEClient),
            bridge=bridge,
        )

        self.assertIsInstance(bundle.wrapper, IBKRWrapperBridge)
        self.assertIsInstance(bundle.client, CompatibilityFakeEClient)
        self.assertIs(bundle.client.wrapper, bundle.wrapper)
        self.assertEqual(bundle.client.connect_calls, 0)
        self.assertEqual(bundle.client.run_calls, 0)

    def test_callback_attribute_lookup_is_explicit_and_callable(self) -> None:
        wrapper = IBKRWrapperBridge(IBKRCallbackBridge())

        for callback_name in [
            "nextValidId",
            "error",
            "accountSummary",
            "accountSummaryEnd",
            "positionMulti",
            "positionMultiEnd",
            "openOrder",
            "openOrderEnd",
            "orderStatus",
            "connect_ready",
            "connect_error",
        ]:
            with self.subTest(callback=callback_name):
                self.assertTrue(callable(getattr(wrapper, callback_name)))

    def test_native_account_summary_callbacks_route_to_bridge(self) -> None:
        wrapper = IBKRWrapperBridge(IBKRCallbackBridge())

        self.assertFalse(
            wrapper.accountSummary(101, "DU123", "BuyingPower", "123.45", "USD")
        )
        self.assertFalse(wrapper.accountSummaryEnd(101))

    def test_native_position_multi_callbacks_route_to_bridge(self) -> None:
        wrapper = IBKRWrapperBridge(IBKRCallbackBridge())
        contract = SimpleNamespace(symbol="AAPL")

        self.assertFalse(wrapper.positionMulti(201, "DU123", "", contract, "3", 100.0))
        self.assertFalse(wrapper.positionMultiEnd(201))

    def test_native_open_order_callbacks_route_only_with_active_snapshot(self) -> None:
        bridge = IBKRCallbackBridge()
        wrapper = IBKRWrapperBridge(bridge)
        contract = SimpleNamespace(symbol="AAPL")
        order = SimpleNamespace(action="BUY", totalQuantity="2", permId=1001)
        order_state = SimpleNamespace(status="Submitted")

        self.assertFalse(wrapper.openOrder(50, contract, order, order_state))
        self.assertFalse(wrapper.openOrderEnd())
        generation = bridge.begin_open_orders_snapshot(symbol="AAPL")

        self.assertTrue(wrapper.openOrder(50, contract, order, order_state))
        self.assertTrue(
            wrapper.orderStatus(
                50,
                "PreSubmitted",
                0,
                2,
                0.0,
                1001,
                0,
                0.0,
                1,
                "",
                0.0,
            )
        )
        self.assertTrue(wrapper.openOrderEnd())

        result = bridge.complete_open_orders_snapshot(generation=generation)

        self.assertEqual(result.open_buy_order_qty, 2)
        self.assertEqual(result.open_buy_order_count, 1)

    def test_wrapper_integrity_is_preserved_after_fake_client_construction(self) -> None:
        bridge = IBKRCallbackBridge()
        bundle = build_ibkr_native_client_bundle(
            native_api=SimpleNamespace(e_client=CompatibilityFakeEClient),
            bridge=bridge,
        )
        bridge.begin_lifecycle(operation="connect")

        routed = bundle.wrapper.nextValidId(101)
        result = bridge.complete_lifecycle(operation="connect")

        self.assertTrue(routed)
        self.assertIs(bundle.wrapper.bridge, bridge)
        self.assertEqual(result.passed, True)
        self.assertEqual(result.message, "next_valid_id")

    def test_real_ibapi_eclient_accepts_wrapper_without_runtime_side_effects(
        self,
    ) -> None:
        try:
            native_api = load_ibkr_native_api()
        except IBKRDependencyUnavailable as exc:
            self.skipTest(str(exc))

        before_threads = {thread.ident for thread in threading.enumerate()}
        bundle = build_ibkr_native_client_bundle(
            native_api=native_api,
            bridge=IBKRCallbackBridge(),
        )
        after_threads = {thread.ident for thread in threading.enumerate()}

        self.assertEqual(type(bundle.wrapper).__name__, "IBKRWrapperBridge")
        self.assertEqual(type(bundle.client).__name__, "EClient")
        self.assertTrue(callable(getattr(bundle.wrapper, "nextValidId")))
        self.assertTrue(callable(getattr(bundle.wrapper, "error")))
        self.assertTrue(callable(getattr(bundle.wrapper, "accountSummary")))
        self.assertTrue(callable(getattr(bundle.wrapper, "accountSummaryEnd")))
        self.assertTrue(callable(getattr(bundle.wrapper, "positionMulti")))
        self.assertTrue(callable(getattr(bundle.wrapper, "positionMultiEnd")))
        self.assertTrue(callable(getattr(bundle.wrapper, "openOrder")))
        self.assertTrue(callable(getattr(bundle.wrapper, "openOrderEnd")))
        self.assertTrue(callable(getattr(bundle.wrapper, "orderStatus")))
        self.assertEqual(bundle.client.isConnected(), False)
        self.assertEqual(after_threads, before_threads)


if __name__ == "__main__":
    unittest.main()
