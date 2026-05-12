from __future__ import annotations

import unittest

from broker_interface import (
    BrokerExecutionFill,
    BrokerExecutionSnapshotState,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
    BrokerSubmitIntent,
)
from ibkr_submit_reconciliation_workflow import IBKRSubmitReconciliationWorkflow


class FakeBroker:
    def __init__(
        self,
        *,
        execution_snapshot=None,
        open_order_snapshot=None,
        position_snapshot=None,
    ) -> None:
        self.execution_snapshot = execution_snapshot or executions()
        self.open_order_snapshot = open_order_snapshot or open_orders(0)
        self.position_snapshot = position(0) if position_snapshot is None else position_snapshot
        self.execution_calls = []
        self.open_order_calls = []
        self.position_calls = []

    def get_execution_snapshot(self, **kwargs):
        self.execution_calls.append(kwargs)
        if isinstance(self.execution_snapshot, Exception):
            raise self.execution_snapshot
        return self.execution_snapshot

    def get_open_buy_order_qty(self, symbol, timeout_seconds=None):
        self.open_order_calls.append(
            {"symbol": symbol, "timeout_seconds": timeout_seconds}
        )
        if isinstance(self.open_order_snapshot, Exception):
            raise self.open_order_snapshot
        return self.open_order_snapshot

    def get_existing_position(self, symbol, timeout_seconds=None):
        self.position_calls.append(
            {"symbol": symbol, "timeout_seconds": timeout_seconds}
        )
        if isinstance(self.position_snapshot, Exception):
            raise self.position_snapshot
        return self.position_snapshot


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


def submit_result(status: str) -> BrokerOrderResult:
    return BrokerOrderResult(
        broker_name="ibkr",
        order_id="101",
        order_status=status,
        broker_status=status,
        is_terminal=status in {"filled", "rejected", "canceled"},
    )


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
    }
    fields.update(overrides)
    return BrokerExecutionFill(**fields)


def executions(*fills: BrokerExecutionFill) -> BrokerExecutionSnapshotState:
    total_shares = sum(item.shares for item in fills)
    return BrokerExecutionSnapshotState(
        broker_name="ibkr",
        passed=True,
        fills=tuple(fills),
        fill_count=len(fills),
        total_shares=total_shares,
        cumulative_qty=total_shares if fills else None,
        avg_fill_price=None,
        reason="executions_loaded",
    )


def open_orders(qty: int | None) -> BrokerOpenOrderState:
    return BrokerOpenOrderState(
        broker_name="ibkr",
        passed=True,
        open_buy_order_qty=qty,
        open_buy_order_count=1 if qty else 0,
        reason="open_buy_orders_loaded",
    )


def position(qty: int) -> BrokerPositionState:
    return BrokerPositionState(
        broker_name="ibkr",
        found=qty > 0,
        qty=qty,
        raw_qty=str(qty),
        side="long" if qty > 0 else None,
        reason="position_found" if qty > 0 else "no_position",
    )


class IBKRSubmitReconciliationWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = IBKRSubmitReconciliationWorkflow()

    def test_no_reconciliation_when_submit_acknowledged(self) -> None:
        broker = FakeBroker()

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("submitted"),
            intent=intent(),
        )

        self.assertEqual(result.submit_state, "submit_acknowledged")
        self.assertIsNone(result.reconciliation_status)
        self.assertEqual(broker.execution_calls, [])
        self.assertEqual(broker.open_order_calls, [])
        self.assertEqual(broker.position_calls, [])

    def test_reconciliation_invoked_only_on_reconciliation_required(self) -> None:
        broker = FakeBroker(open_order_snapshot=open_orders(3))

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("reconciliation_required"),
            intent=intent(),
            timeout_seconds=0.5,
        )

        self.assertEqual(result.submit_state, "submit_uncertain_reconciliation_required")
        self.assertEqual(result.reconciliation_status, "accepted_unfilled")
        self.assertEqual(len(broker.execution_calls), 1)
        self.assertEqual(len(broker.open_order_calls), 1)
        self.assertEqual(len(broker.position_calls), 1)
        self.assertEqual(broker.execution_calls[0]["side"], "BOT")
        self.assertEqual(broker.execution_calls[0]["since"], "20260512 10:00:00")

    def test_filled_result(self) -> None:
        broker = FakeBroker(execution_snapshot=executions(fill()))

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("reconciliation_required"),
            intent=intent(),
        )

        self.assertEqual(result.reconciliation_status, "filled")
        self.assertEqual(result.filled_qty, 3.0)
        self.assertFalse(result.manual_review_required)
        self.assertTrue(result.terminal_for_run)

    def test_accepted_unfilled_result(self) -> None:
        broker = FakeBroker(open_order_snapshot=open_orders(3))

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("reconciliation_required"),
            intent=intent(),
        )

        self.assertEqual(result.reconciliation_status, "accepted_unfilled")
        self.assertEqual(result.working_qty, 3.0)
        self.assertFalse(result.manual_review_required)

    def test_unresolved_requires_manual_review(self) -> None:
        broker = FakeBroker()

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("reconciliation_required"),
            intent=intent(),
        )

        self.assertEqual(result.reconciliation_status, "unresolved")
        self.assertTrue(result.manual_review_required)
        self.assertTrue(result.ambiguous)

    def test_partially_filled_unresolved_requires_manual_review(self) -> None:
        broker = FakeBroker(
            execution_snapshot=executions(
                fill(shares=1.0, cumulative_qty=1.0),
            ),
            open_order_snapshot=open_orders(0),
        )

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("reconciliation_required"),
            intent=intent(),
        )

        self.assertEqual(result.reconciliation_status, "partially_filled_unresolved")
        self.assertEqual(result.filled_qty, 1.0)
        self.assertTrue(result.manual_review_required)

    def test_no_retry_field_or_behavior_exists(self) -> None:
        broker = FakeBroker()

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("reconciliation_required"),
            intent=intent(),
        )

        self.assertFalse(hasattr(result, "safe_to_retry"))
        self.assertFalse(hasattr(self.workflow, "retry"))

    def test_snapshot_failure_leads_unresolved_manual_review(self) -> None:
        broker = FakeBroker(
            execution_snapshot=TimeoutError("execution timeout"),
            open_order_snapshot=TimeoutError("open order timeout"),
            position_snapshot=TimeoutError("position timeout"),
        )

        result = self.workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result("reconciliation_required"),
            intent=intent(),
        )

        self.assertEqual(result.reconciliation_status, "unresolved")
        self.assertTrue(result.manual_review_required)
        self.assertEqual(result.reason, "no_deterministic_broker_evidence")


if __name__ == "__main__":
    unittest.main()
