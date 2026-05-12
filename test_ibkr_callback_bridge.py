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

    def test_order_submission_open_order_ack_completes_request_coordinator(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=101)

        self.assertTrue(
            bridge.open_order(
                order_id=101,
                symbol="AAPL",
                side="BUY",
                qty="1",
                status="Submitted",
            )
        )
        self.assertFalse(
            bridge.open_order(
                order_id=101,
                symbol="AAPL",
                side="BUY",
                qty="1",
                status="Filled",
            )
        )

        result = request_coordinator.result(101)

        self.assertEqual(result.order_status, "submitted")
        self.assertEqual(result.broker_status, "Submitted")
        self.assertEqual(result.is_terminal, False)
        self.assertEqual(request_coordinator.completed_by(101), "callback")
        self.assertFalse(request_coordinator.has_pending_request(101))

    def test_order_submission_status_ack_completes_request_coordinator(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=102)

        self.assertTrue(bridge.order_status(order_id=102, status="PreSubmitted"))
        self.assertFalse(bridge.order_status(order_id=102, status="Filled"))

        result = request_coordinator.result(102)

        self.assertEqual(result.order_status, "submitted")
        self.assertEqual(result.broker_status, "PreSubmitted")
        self.assertFalse(result.is_terminal)

    def test_order_submission_api_cancelled_is_terminal_canceled(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=105)

        self.assertTrue(bridge.order_status(order_id=105, status="ApiCancelled"))

        result = request_coordinator.result(105)

        self.assertEqual(result.order_status, "canceled")
        self.assertEqual(result.broker_status, "ApiCancelled")
        self.assertTrue(result.is_terminal)

    def test_order_submission_timeout_is_reconciliation_required(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=103)

        result = bridge.timeout_order_submission(order_id=103)

        self.assertEqual(result.order_status, "reconciliation_required")
        self.assertEqual(result.order_id, "103")
        self.assertFalse(result.is_terminal)
        self.assertEqual(request_coordinator.completed_by(103), "timeout")
        self.assertFalse(request_coordinator.has_pending_request(103))
        self.assertFalse(bridge.order_status(order_id=103, status="Submitted"))

    def test_order_submission_error_completes_as_rejected(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=106)

        self.assertTrue(
            bridge.order_error(
                order_id=106,
                code=321,
                message="The API interface is currently in Read-Only mode.",
            )
        )

        result = request_coordinator.result(106)

        self.assertEqual(result.order_id, "106")
        self.assertEqual(result.order_status, "rejected")
        self.assertEqual(result.broker_status, "error")
        self.assertTrue(result.is_terminal)
        self.assertEqual(result.raw_response["code"], 321)
        self.assertEqual(request_coordinator.completed_by(106), "callback")
        self.assertFalse(request_coordinator.has_pending_request(106))

    def test_order_submission_etradeonly_warning_does_not_complete(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=109)

        self.assertTrue(
            bridge.order_error(
                order_id=109,
                code=10268,
                message="The 'EtradeOnly' order attribute is not supported.",
            )
        )

        self.assertIsNone(request_coordinator.result(109))
        self.assertIsNone(request_coordinator.completed_by(109))
        self.assertTrue(request_coordinator.has_pending_request(109))

    def test_order_submission_etradeonly_warning_then_filled_completes_filled(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=110)

        self.assertTrue(
            bridge.order_error(
                order_id=110,
                code=10268,
                message="The 'EtradeOnly' order attribute is not supported.",
            )
        )
        self.assertTrue(bridge.order_status(order_id=110, status="Filled"))

        result = request_coordinator.result(110)

        self.assertEqual(result.order_status, "filled")
        self.assertEqual(result.broker_status, "Filled")
        self.assertTrue(result.is_terminal)
        self.assertEqual(result.raw_response["warnings"][0]["code"], 10268)
        self.assertEqual(request_coordinator.completed_by(110), "callback")

    def test_order_submission_etradeonly_warning_then_submitted_completes_submitted(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=111)

        self.assertTrue(
            bridge.order_error(
                order_id=111,
                code=10268,
                message="The 'EtradeOnly' order attribute is not supported.",
            )
        )
        self.assertTrue(bridge.order_status(order_id=111, status="Submitted"))

        result = request_coordinator.result(111)

        self.assertEqual(result.order_status, "submitted")
        self.assertEqual(result.broker_status, "Submitted")
        self.assertFalse(result.is_terminal)
        self.assertEqual(result.raw_response["warnings"][0]["code"], 10268)

    def test_wrong_order_error_is_ignored(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=107)

        self.assertFalse(
            bridge.order_error(
                order_id=999,
                code=321,
                message="The API interface is currently in Read-Only mode.",
            )
        )
        result = bridge.timeout_order_submission(order_id=107)

        self.assertEqual(result.order_status, "reconciliation_required")
        self.assertFalse(result.is_terminal)

    def test_timeout_after_only_etradeonly_warning_requires_reconciliation(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=112)

        self.assertTrue(
            bridge.order_error(
                order_id=112,
                code=10268,
                message="The 'EtradeOnly' order attribute is not supported.",
            )
        )
        result = bridge.timeout_order_submission(order_id=112)

        self.assertEqual(result.order_status, "reconciliation_required")
        self.assertFalse(result.is_terminal)
        self.assertNotEqual(result.order_status, "rejected")

    def test_late_order_status_after_error_rejection_does_not_mutate_result(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=108)

        self.assertTrue(
            bridge.order_error(
                order_id=108,
                code=321,
                message="The API interface is currently in Read-Only mode.",
            )
        )
        before = request_coordinator.result(108)
        self.assertFalse(bridge.order_status(order_id=108, status="Submitted"))
        after = request_coordinator.result(108)

        self.assertIs(after, before)
        self.assertEqual(after.order_status, "rejected")
        self.assertEqual(after.broker_status, "error")

    def test_order_submission_stale_callback_is_ignored(self) -> None:
        request_coordinator = IBKRRequestCoordinator()
        bridge = IBKRCallbackBridge(request_coordinator=request_coordinator)
        bridge.begin_order_submission(order_id=104)

        self.assertFalse(bridge.order_status(order_id=999, status="Submitted"))
        self.assertFalse(bridge.stale_order_submission(order_id=104))
        result = bridge.timeout_order_submission(order_id=104)

        self.assertEqual(result.order_status, "reconciliation_required")
        self.assertFalse(result.is_terminal)


if __name__ == "__main__":
    unittest.main()
