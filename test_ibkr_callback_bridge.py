from __future__ import annotations

import unittest

from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_timeout_injector import IBKRTimeoutInjector


class IBKRCallbackBridgeTests(unittest.TestCase):
    def test_request_registry_correlates_position_snapshots_by_request_id(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_position_snapshot(request_id="pos-a", symbol="AAPL")
        bridge.begin_position_snapshot(request_id="pos-b", symbol="MSFT")

        self.assertTrue(
            bridge.position(request_id="pos-a", symbol="AAPL", qty="3", side="long")
        )
        self.assertTrue(
            bridge.position(request_id="pos-b", symbol="MSFT", qty="5", side="long")
        )
        self.assertTrue(bridge.position_end(request_id="pos-a"))
        self.assertTrue(bridge.position_end(request_id="pos-b"))

        aapl = bridge.complete_position_snapshot(request_id="pos-a")
        msft = bridge.complete_position_snapshot(request_id="pos-b")

        self.assertEqual(aapl.found, True)
        self.assertEqual(aapl.qty, 3)
        self.assertEqual(msft.found, True)
        self.assertEqual(msft.qty, 5)

    def test_timeout_injection_routes_to_lifecycle_snapshot_and_order(self) -> None:
        bridge = IBKRCallbackBridge()
        timeout_injector = IBKRTimeoutInjector(bridge.registry)
        bridge.begin_lifecycle(operation="connect")
        bridge.begin_position_snapshot(request_id="pos-1", symbol="AAPL")
        bridge.begin_order_status(order_id=101)
        bridge.order_status(order_id=101, status="Submitted")

        lifecycle = timeout_injector.inject_lifecycle_timeout(
            operation="connect",
            message="no ready callback",
            elapsed_ms=5000,
        )
        position = timeout_injector.inject_snapshot_timeout(request_id="pos-1")
        order = timeout_injector.inject_order_timeout(
            order_id=101,
            message="no terminal callback",
        )

        self.assertEqual(lifecycle.passed, False)
        self.assertEqual(lifecycle.reason, "connect_timeout")
        self.assertEqual(lifecycle.message, "no ready callback")
        self.assertEqual(position.error, "position_snapshot_incomplete")
        self.assertEqual(order.order_status, "timeout")
        self.assertEqual(order.broker_status, "Submitted")

    def test_callback_to_aggregator_routing_builds_account_and_open_order_results(
        self,
    ) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_account_snapshot(request_id="acct-1")
        bridge.begin_open_orders_snapshot(request_id="open-1", symbol="AAPL")

        self.assertTrue(
            bridge.account_summary(request_id="acct-1", buying_power="12345.67")
        )
        self.assertTrue(bridge.account_summary_end(request_id="acct-1"))
        self.assertTrue(
            bridge.open_order(
                request_id="open-1",
                order_id=50,
                symbol="AAPL",
                side="BUY",
                qty="2",
                status="Submitted",
            )
        )
        self.assertTrue(
            bridge.open_order(
                request_id="open-1",
                order_id=51,
                symbol="AAPL",
                side="BUY",
                qty="1",
                status="PreSubmitted",
            )
        )
        self.assertTrue(bridge.open_order_end(request_id="open-1"))

        account = bridge.complete_account_snapshot(request_id="acct-1")
        open_orders = bridge.complete_open_orders_snapshot(request_id="open-1")

        self.assertEqual(account.buying_power, 12345.67)
        self.assertEqual(open_orders.open_buy_order_qty, 3)
        self.assertEqual(open_orders.open_buy_order_count, 2)

    def test_account_summary_strict_req_id_routing(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_account_snapshot(request_id="acct-1")

        self.assertFalse(
            bridge.account_summary(request_id="other", buying_power="999.99")
        )
        self.assertFalse(bridge.account_summary(request_id=None, buying_power="888.88"))
        self.assertFalse(bridge.account_summary_end(request_id="other"))
        self.assertFalse(bridge.account_summary_end(request_id=None))

        self.assertTrue(
            bridge.account_summary(request_id="acct-1", buying_power="12345.67")
        )
        self.assertTrue(bridge.account_summary_end(request_id="acct-1"))

        account = bridge.complete_account_snapshot(request_id="acct-1")

        self.assertEqual(account.buying_power, 12345.67)

    def test_account_summary_requires_matching_end_marker(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_account_snapshot(request_id="acct-1")

        self.assertTrue(
            bridge.account_summary(request_id="acct-1", buying_power="12345.67")
        )

        with self.assertRaisesRegex(ValueError, "matching end marker"):
            bridge.complete_account_snapshot(request_id="acct-1")

    def test_concurrent_account_summary_requests_are_isolated(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_account_snapshot(request_id="acct-a")
        bridge.begin_account_snapshot(request_id="acct-b")

        self.assertTrue(
            bridge.account_summary(request_id="acct-b", buying_power="222.22")
        )
        self.assertTrue(
            bridge.account_summary(request_id="acct-a", buying_power="111.11")
        )
        self.assertTrue(bridge.account_summary_end(request_id="acct-a"))
        self.assertTrue(bridge.account_summary_end(request_id="acct-b"))

        account_a = bridge.complete_account_snapshot(request_id="acct-a")
        account_b = bridge.complete_account_snapshot(request_id="acct-b")

        self.assertEqual(account_a.buying_power, 111.11)
        self.assertEqual(account_b.buying_power, 222.22)

    def test_late_account_summary_callbacks_after_timeout_are_ignored(self) -> None:
        bridge = IBKRCallbackBridge()
        timeout_injector = IBKRTimeoutInjector(bridge.registry)
        bridge.begin_account_snapshot(request_id="acct-1")

        with self.assertRaisesRegex(ValueError, "matching end marker"):
            timeout_injector.inject_snapshot_timeout(request_id="acct-1")

        self.assertFalse(
            bridge.account_summary(request_id="acct-1", buying_power="12345.67")
        )
        self.assertFalse(bridge.account_summary_end(request_id="acct-1"))
        self.assertFalse(bridge.registry.has_request("acct-1"))

    def test_duplicate_account_summary_end_marker_is_ignored_after_completion(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_account_snapshot(request_id="acct-1")

        self.assertTrue(
            bridge.account_summary(request_id="acct-1", buying_power="12345.67")
        )
        self.assertTrue(bridge.account_summary_end(request_id="acct-1"))

        account = bridge.complete_account_snapshot(request_id="acct-1")

        self.assertEqual(account.buying_power, 12345.67)
        self.assertFalse(bridge.account_summary_end(request_id="acct-1"))

    def test_account_summary_end_completes_request_coordinator_when_injected(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_account_snapshot(request_id="acct-1")

        self.assertTrue(
            bridge.account_summary(
                request_id="acct-1",
                account="DU123",
                tag="BuyingPower",
                value="12345.67",
                currency="USD",
            )
        )
        self.assertTrue(bridge.account_summary_end(request_id="acct-1"))
        self.assertFalse(bridge.account_summary_end(request_id="acct-1"))

        account = bridge.complete_account_snapshot(request_id="acct-1")

        self.assertEqual(account.buying_power, 12345.67)
        self.assertEqual(request_coordinator.completed_by("acct-1"), "callback")
        self.assertFalse(request_coordinator.has_pending_request("acct-1"))

    def test_late_callbacks_are_isolated_after_timeout_completion(self) -> None:
        bridge = IBKRCallbackBridge()
        timeout_injector = IBKRTimeoutInjector(bridge.registry)
        bridge.begin_position_snapshot(request_id="pos-1", symbol="AAPL")

        result = timeout_injector.inject_snapshot_timeout(request_id="pos-1")

        self.assertEqual(result.error, "position_snapshot_incomplete")
        self.assertFalse(
            bridge.position(request_id="pos-1", symbol="AAPL", qty="9", side="long")
        )
        self.assertFalse(bridge.position_end(request_id="pos-1"))
        self.assertFalse(bridge.registry.has_request("pos-1"))

    def test_unrelated_request_and_order_callbacks_are_ignored(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_open_orders_snapshot(request_id="open-1", symbol="AAPL")
        bridge.begin_order_status(order_id=101)

        self.assertFalse(
            bridge.open_order(
                request_id="other",
                order_id=50,
                symbol="AAPL",
                side="BUY",
                qty="10",
                status="Submitted",
            )
        )
        self.assertFalse(bridge.order_status(order_id=202, status="Filled"))
        self.assertTrue(bridge.open_order_end(request_id="open-1"))

        open_orders = bridge.complete_open_orders_snapshot(request_id="open-1")
        order = bridge.complete_order_status(order_id=101)

        self.assertEqual(open_orders.open_buy_order_qty, 0)
        self.assertEqual(open_orders.open_buy_order_count, 0)
        self.assertEqual(order.order_status, "submitted")
        self.assertEqual(order.broker_status, None)

    def test_order_callback_routing_tracks_terminal_status_by_order_id(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_order_status(order_id=101)

        self.assertTrue(bridge.order_status(order_id=101, status="Submitted"))
        self.assertTrue(bridge.order_status(order_id=101, status="Filled"))

        result = bridge.complete_order_status(order_id=101)

        self.assertEqual(result.order_id, "101")
        self.assertEqual(result.order_status, "filled")
        self.assertEqual(result.broker_status, "Filled")
        self.assertEqual(result.is_terminal, True)


if __name__ == "__main__":
    unittest.main()
