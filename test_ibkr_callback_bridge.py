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
            bridge.position_multi(request_id="pos-a", symbol="AAPL", qty="3", side="long")
        )
        self.assertTrue(
            bridge.position_multi(request_id="pos-b", symbol="MSFT", qty="5", side="long")
        )
        self.assertTrue(bridge.position_multi_end(request_id="pos-a"))
        self.assertTrue(bridge.position_multi_end(request_id="pos-b"))

        aapl = bridge.complete_position_snapshot(request_id="pos-a")
        msft = bridge.complete_position_snapshot(request_id="pos-b")

        self.assertEqual(aapl.found, True)
        self.assertEqual(aapl.qty, 3)
        self.assertEqual(msft.found, True)
        self.assertEqual(msft.qty, 5)

    def test_position_multi_strict_req_id_routing(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_position_snapshot(request_id="pos-1", symbol="AAPL")

        self.assertFalse(
            bridge.position_multi(request_id="other", symbol="AAPL", qty="9")
        )
        self.assertFalse(
            bridge.position_multi(request_id=None, symbol="AAPL", qty="8")
        )
        self.assertFalse(bridge.position_multi_end(request_id="other"))
        self.assertFalse(bridge.position_multi_end(request_id=None))

        self.assertTrue(
            bridge.position_multi(request_id="pos-1", symbol="AAPL", qty="3")
        )
        self.assertTrue(bridge.position_multi_end(request_id="pos-1"))

        result = bridge.complete_position_snapshot(request_id="pos-1")

        self.assertEqual(result.found, True)
        self.assertEqual(result.qty, 3)

    def test_position_multi_requires_matching_end_marker(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_position_snapshot(request_id="pos-1", symbol="AAPL")

        self.assertTrue(
            bridge.position_multi(request_id="pos-1", symbol="AAPL", qty="3")
        )

        result = bridge.complete_position_snapshot(request_id="pos-1")

        self.assertEqual(result.found, None)
        self.assertEqual(result.error, "position_snapshot_incomplete")

    def test_position_multi_no_matching_symbol_returns_no_position_after_end(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_position_snapshot(request_id="pos-1", symbol="AAPL")

        self.assertTrue(
            bridge.position_multi(request_id="pos-1", symbol="MSFT", qty="3")
        )
        self.assertTrue(bridge.position_multi_end(request_id="pos-1"))

        result = bridge.complete_position_snapshot(request_id="pos-1")

        self.assertEqual(result.found, False)
        self.assertEqual(result.qty, 0)
        self.assertEqual(result.reason, "no_position")

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
        generation = bridge.begin_open_orders_snapshot(symbol="AAPL")

        self.assertTrue(
            bridge.account_summary(request_id="acct-1", buying_power="12345.67")
        )
        self.assertTrue(bridge.account_summary_end(request_id="acct-1"))
        self.assertTrue(
            bridge.open_order(
                order_id=50,
                perm_id=1001,
                symbol="AAPL",
                side="BUY",
                qty="2",
                status="Submitted",
            )
        )
        self.assertTrue(
            bridge.open_order(
                order_id=51,
                perm_id=1002,
                symbol="AAPL",
                side="BUY",
                qty="1",
                status="PreSubmitted",
            )
        )
        self.assertTrue(bridge.open_order_end())

        account = bridge.complete_account_snapshot(request_id="acct-1")
        open_orders = bridge.complete_open_orders_snapshot(generation=generation)

        self.assertEqual(account.buying_power, 12345.67)
        self.assertEqual(open_orders.open_buy_order_qty, 3)
        self.assertEqual(open_orders.open_buy_order_count, 2)

    def test_open_orders_ignored_when_no_snapshot_active(self) -> None:
        bridge = IBKRCallbackBridge()

        self.assertFalse(
            bridge.open_order(
                order_id=50,
                symbol="AAPL",
                side="BUY",
                qty="2",
                status="Submitted",
            )
        )
        self.assertFalse(bridge.open_order_end())

    def test_open_order_singleton_filters_and_dedupes(self) -> None:
        bridge = IBKRCallbackBridge()
        generation = bridge.begin_open_orders_snapshot(symbol="AAPL")

        self.assertTrue(
            bridge.open_order(
                order_id=50,
                perm_id=1001,
                symbol="AAPL",
                side="BUY",
                qty="2",
                status="Submitted",
            )
        )
        self.assertTrue(
            bridge.open_order(
                order_id=51,
                perm_id=1001,
                symbol="AAPL",
                side="BUY",
                qty="2",
                status="Submitted",
            )
        )
        self.assertTrue(
            bridge.open_order(
                order_id=52,
                symbol="MSFT",
                side="BUY",
                qty="9",
                status="Submitted",
            )
        )
        self.assertTrue(
            bridge.open_order(
                order_id=53,
                symbol="AAPL",
                side="SELL",
                qty="9",
                status="Submitted",
            )
        )
        self.assertTrue(
            bridge.open_order(
                order_id=54,
                symbol="AAPL",
                side="BUY",
                qty="9",
                status="Filled",
            )
        )
        self.assertTrue(bridge.open_order_end())

        result = bridge.complete_open_orders_snapshot(generation=generation)

        self.assertEqual(result.passed, True)
        self.assertEqual(result.open_buy_order_qty, 2)
        self.assertEqual(result.open_buy_order_count, 1)

    def test_open_order_status_enriches_existing_order_only(self) -> None:
        bridge = IBKRCallbackBridge()
        generation = bridge.begin_open_orders_snapshot(symbol="AAPL")

        self.assertTrue(
            bridge.open_order_status_update(order_id=999, status="Filled")
        )
        self.assertTrue(
            bridge.open_order(
                order_id=50,
                symbol="AAPL",
                side="BUY",
                qty="2",
                status="Submitted",
            )
        )
        self.assertTrue(
            bridge.open_order_status_update(order_id=50, status="Filled")
        )
        self.assertTrue(bridge.open_order_end())

        result = bridge.complete_open_orders_snapshot(generation=generation)

        self.assertEqual(result.open_buy_order_qty, 0)
        self.assertEqual(result.open_buy_order_count, 0)

    def test_open_order_duplicate_end_and_late_callbacks_are_ignored(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_open_orders_snapshot(symbol="AAPL")

        self.assertTrue(
            bridge.open_order(
                order_id=50,
                symbol="AAPL",
                side="BUY",
                qty="2",
                status="Submitted",
            )
        )
        self.assertTrue(bridge.open_order_end())
        self.assertFalse(bridge.open_order_end())
        self.assertFalse(
            bridge.open_order(
                order_id=51,
                symbol="AAPL",
                side="BUY",
                qty="9",
                status="Submitted",
            )
        )

    def test_open_order_timeout_closes_generation_and_late_callbacks_are_ignored(self) -> None:
        bridge = IBKRCallbackBridge()
        generation = bridge.begin_open_orders_snapshot(symbol="AAPL")

        result = bridge.timeout_open_orders_snapshot()

        self.assertEqual(result.error, "open_order_snapshot_incomplete")
        self.assertFalse(
            bridge.open_order(
                order_id=51,
                symbol="AAPL",
                side="BUY",
                qty="9",
                status="Submitted",
            )
        )
        self.assertFalse(bridge.open_order_end())
        self.assertIs(bridge.complete_open_orders_snapshot(generation=generation), result)

    def test_concurrent_open_order_snapshot_rejected(self) -> None:
        bridge = IBKRCallbackBridge()
        bridge.begin_open_orders_snapshot(symbol="AAPL")

        with self.assertRaisesRegex(RuntimeError, "already active"):
            bridge.begin_open_orders_snapshot(symbol="MSFT")

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

    def test_position_multi_end_completes_request_coordinator_when_injected(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_position_snapshot(request_id="pos-1", symbol="AAPL")

        self.assertTrue(
            bridge.position_multi(request_id="pos-1", symbol="AAPL", qty="-4")
        )
        self.assertTrue(bridge.position_multi_end(request_id="pos-1"))
        self.assertFalse(bridge.position_multi_end(request_id="pos-1"))

        result = bridge.complete_position_snapshot(request_id="pos-1")

        self.assertEqual(result.found, True)
        self.assertEqual(result.qty, 4)
        self.assertEqual(result.side, "long")
        self.assertEqual(request_coordinator.completed_by("pos-1"), "callback")
        self.assertFalse(request_coordinator.has_pending_request("pos-1"))

    def test_late_callbacks_are_isolated_after_timeout_completion(self) -> None:
        bridge = IBKRCallbackBridge()
        timeout_injector = IBKRTimeoutInjector(bridge.registry)
        bridge.begin_position_snapshot(request_id="pos-1", symbol="AAPL")

        result = timeout_injector.inject_snapshot_timeout(request_id="pos-1")

        self.assertEqual(result.error, "position_snapshot_incomplete")
        self.assertFalse(
            bridge.position_multi(request_id="pos-1", symbol="AAPL", qty="9", side="long")
        )
        self.assertFalse(bridge.position_multi_end(request_id="pos-1"))
        self.assertFalse(bridge.registry.has_request("pos-1"))

    def test_unrelated_request_and_order_callbacks_are_ignored(self) -> None:
        bridge = IBKRCallbackBridge()
        generation = bridge.begin_open_orders_snapshot(symbol="AAPL")
        bridge.begin_order_status(order_id=101)

        self.assertTrue(
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
        self.assertTrue(bridge.open_order_end())

        open_orders = bridge.complete_open_orders_snapshot(generation=generation)
        order = bridge.complete_order_status(order_id=101)

        self.assertEqual(open_orders.open_buy_order_qty, 10)
        self.assertEqual(open_orders.open_buy_order_count, 1)
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
