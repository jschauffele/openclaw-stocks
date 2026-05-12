from __future__ import annotations

import unittest

from broker_interface import (
    BrokerExecutionFill,
    BrokerExecutionSnapshotState,
    BrokerOpenOrderState,
    BrokerPositionState,
    BrokerSubmitIntent,
)
from ibkr_broker_reconciler import IBKRBrokerReconciler


def intent(**overrides) -> BrokerSubmitIntent:
    fields = {
        "broker_name": "ibkr",
        "order_id": "101",
        "client_id": "7",
        "perm_id": "9001",
        "symbol": "AAPL",
        "side": "BUY",
        "qty": 3.0,
        "submitted_at": "20260512 10:00:00",
    }
    fields.update(overrides)
    return BrokerSubmitIntent(**fields)


def fill(**overrides) -> BrokerExecutionFill:
    fields = {
        "exec_id": "exec-1",
        "order_id": "101",
        "client_id": "7",
        "perm_id": "9001",
        "symbol": "AAPL",
        "side": "BOT",
        "shares": 3.0,
        "cumulative_qty": 3.0,
        "avg_price": 185.0,
        "price": 185.0,
        "time": "20260512 10:00:05",
    }
    fields.update(overrides)
    return BrokerExecutionFill(**fields)


def executions(*fills: BrokerExecutionFill, passed: bool = True) -> BrokerExecutionSnapshotState:
    total_shares = sum(item.shares for item in fills)
    return BrokerExecutionSnapshotState(
        broker_name="ibkr",
        passed=passed,
        fills=tuple(fills),
        fill_count=len(fills),
        total_shares=total_shares,
        cumulative_qty=total_shares if fills else None,
        avg_fill_price=None,
        reason="executions_loaded" if passed else "execution_lookup_failed",
        error=None if passed else "execution_snapshot_incomplete",
    )


def open_orders(qty: int | None, *, passed: bool = True) -> BrokerOpenOrderState:
    return BrokerOpenOrderState(
        broker_name="ibkr",
        passed=passed,
        open_buy_order_qty=qty,
        open_buy_order_count=1 if qty else 0,
        reason="open_buy_orders_loaded" if passed else "open_buy_order_lookup_failed",
        error=None if passed else "open_order_snapshot_incomplete",
    )


def position(qty: int = 3) -> BrokerPositionState:
    return BrokerPositionState(
        broker_name="ibkr",
        found=True,
        qty=qty,
        raw_qty=str(qty),
        side="long",
        reason="position_found",
    )


class IBKRBrokerReconcilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reconciler = IBKRBrokerReconciler()

    def test_filled_from_executions(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(),
            execution_snapshot=executions(fill()),
            open_order_snapshot=open_orders(0),
        )

        self.assertEqual(result.status, "filled")
        self.assertEqual(result.filled_qty, 3.0)
        self.assertEqual(result.working_qty, 0.0)
        self.assertEqual(result.matched_exec_ids, ("exec-1",))
        self.assertFalse(result.ambiguous)

    def test_partial_fill_with_open_order_residual(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(qty=3.0),
            execution_snapshot=executions(
                fill(exec_id="exec-1", shares=1.0, cumulative_qty=1.0),
            ),
            open_order_snapshot=open_orders(2),
        )

        self.assertEqual(result.status, "partially_filled_working")
        self.assertEqual(result.filled_qty, 1.0)
        self.assertEqual(result.working_qty, 2.0)

    def test_accepted_unfilled_from_open_order_only(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(),
            execution_snapshot=executions(),
            open_order_snapshot=open_orders(3),
        )

        self.assertEqual(result.status, "accepted_unfilled")
        self.assertEqual(result.filled_qty, 0.0)
        self.assertEqual(result.working_qty, 3.0)

    def test_unresolved_from_no_evidence(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(),
            execution_snapshot=executions(),
            open_order_snapshot=open_orders(0),
        )

        self.assertEqual(result.status, "unresolved")
        self.assertTrue(result.ambiguous)
        self.assertEqual(result.reason, "no_deterministic_broker_evidence")

    def test_conflicting_truths_resolved_by_execution_precedence(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(qty=3.0),
            execution_snapshot=executions(fill(shares=3.0, cumulative_qty=3.0)),
            open_order_snapshot=open_orders(3),
            position_snapshot=position(0),
        )

        self.assertEqual(result.status, "filled")
        self.assertEqual(result.filled_qty, 3.0)
        self.assertEqual(result.working_qty, 0.0)

    def test_delayed_fill_handling(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(submitted_at="20260512 10:00:00"),
            execution_snapshot=executions(fill(time="20260512 10:04:30")),
            open_order_snapshot=open_orders(0),
        )

        self.assertEqual(result.status, "filled")
        self.assertEqual(result.matched_exec_ids, ("exec-1",))

    def test_ambiguous_position_only_evidence_is_unresolved(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(),
            execution_snapshot=executions(),
            open_order_snapshot=open_orders(0),
            position_snapshot=position(3),
        )

        self.assertEqual(result.status, "unresolved")
        self.assertTrue(result.ambiguous)
        self.assertEqual(result.reason, "position_only_evidence_is_ambiguous")

    def test_ambiguous_execution_evidence_is_unresolved(self) -> None:
        result = self.reconciler.reconcile(
            intent=intent(order_id=None, client_id=None, perm_id=None),
            execution_snapshot=executions(
                fill(order_id=None, client_id=None, perm_id=None),
            ),
            open_order_snapshot=open_orders(0),
        )

        self.assertEqual(result.status, "unresolved")
        self.assertTrue(result.ambiguous)
        self.assertEqual(result.reason, "ambiguous_execution_evidence")


if __name__ == "__main__":
    unittest.main()
