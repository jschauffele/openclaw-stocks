from __future__ import annotations

import sys
import unittest
from dataclasses import fields
from types import SimpleNamespace

from broker_interface import BrokerOrderResult, BrokerSubmitReconciliationResult
from execution_use_case import (
    ExecutionOutcome,
    ExecutionRequest,
    execute_prevalidated_market_order,
)


IBKR_MODULES = (
    "ibkr_broker_adapter",
    "ibkr_read_only_runtime_provider",
    "ibkr_runtime_diagnostics",
    "ibkr_submit_reconciliation_workflow",
)


class FakeBroker:
    def __init__(
        self,
        *,
        submit_result: BrokerOrderResult | None = None,
        submit_exception: Exception | None = None,
    ) -> None:
        self.build_calls = []
        self.submit_calls = []
        self.submit_result = submit_result or order_result("submitted")
        self.submit_exception = submit_exception

    def build_market_order(self, symbol: str, qty: int):
        order = SimpleNamespace(symbol=symbol, qty=qty)
        self.build_calls.append({"symbol": symbol, "qty": qty, "order": order})
        return order

    def submit_market_order(self, order):
        self.submit_calls.append(order)
        if self.submit_exception is not None:
            raise self.submit_exception
        return self.submit_result


class FakeReconciliationWorkflow:
    def __init__(self, result: BrokerSubmitReconciliationResult) -> None:
        self.result = result
        self.calls = []

    def reconcile_if_required(self, *, broker, submit_result, intent):
        self.calls.append(
            {
                "broker": broker,
                "submit_result": submit_result,
                "intent": intent,
            }
        )
        return self.result


def request(**overrides) -> ExecutionRequest:
    fields_ = {
        "run_id": "run-test",
        "broker_name": "fake",
        "mode": "paper_submit",
        "symbol": "AAPL",
        "side": "buy",
        "qty": 1,
        "order_type": "market",
        "trigger_source": "test",
        "strategy_reason": "test_submit",
        "signal": "buy",
        "decision": "buy",
    }
    fields_.update(overrides)
    return ExecutionRequest(**fields_)


def order_result(status: str) -> BrokerOrderResult:
    return BrokerOrderResult(
        broker_name="fake",
        order_id="101",
        order_status=status,
        broker_status=status,
        is_terminal=status in {"filled", "rejected", "canceled"},
    )


def workflow_result(
    status: str,
    *,
    manual_review_required: bool,
) -> BrokerSubmitReconciliationResult:
    return BrokerSubmitReconciliationResult(
        broker_name="fake",
        submit_state="submit_uncertain_reconciliation_required",
        reconciliation_status=status,
        terminal_for_run=True,
        manual_review_required=manual_review_required,
        order_id="101",
        perm_id=None,
        filled_qty=1.0 if status in {"filled", "partially_filled_unresolved"} else 0.0,
        working_qty=2.0 if status == "accepted_unfilled" else None,
        reason=f"{status}_reason",
        ambiguous=manual_review_required,
    )


class ExecutionUseCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        for module_name in IBKR_MODULES:
            sys.modules.pop(module_name, None)

    def test_request_and_outcome_shape(self) -> None:
        self.assertEqual(
            [field.name for field in fields(ExecutionRequest)],
            [
                "run_id",
                "broker_name",
                "mode",
                "symbol",
                "side",
                "qty",
                "order_type",
                "trigger_source",
                "strategy_reason",
                "signal",
                "decision",
            ],
        )
        self.assertEqual(
            [field.name for field in fields(ExecutionOutcome)],
            [
                "result",
                "reason",
                "mode",
                "broker_name",
                "order_status",
                "submit_state",
                "reconciliation_status",
                "manual_review_required",
                "terminal_for_run",
                "reconciliation_ambiguous",
                "filled_qty",
                "working_qty",
                "notes",
                "raw_submit_result",
                "raw_reconciliation_result",
            ],
        )

    def test_dry_run_builds_order_once_and_submits_zero_times(self) -> None:
        broker = FakeBroker()

        outcome = execute_prevalidated_market_order(
            request(mode="dry_run"),
            broker,
        )

        self.assertEqual(len(broker.build_calls), 1)
        self.assertEqual(broker.build_calls[0]["symbol"], "AAPL")
        self.assertEqual(broker.build_calls[0]["qty"], 1)
        self.assertEqual(broker.submit_calls, [])
        self.assertEqual(outcome.result, "success")
        self.assertEqual(outcome.reason, "dry_run_completed")
        self.assertEqual(outcome.notes, ["Strategy reason=test_submit", "signal=buy", "decision=buy"])

    def test_paper_submit_builds_once_and_submits_once(self) -> None:
        broker = FakeBroker(submit_result=order_result("submitted"))

        outcome = execute_prevalidated_market_order(request(), broker)

        self.assertEqual(len(broker.build_calls), 1)
        self.assertEqual(broker.submit_calls, [broker.build_calls[0]["order"]])
        self.assertEqual(outcome.result, "success")
        self.assertEqual(outcome.reason, "paper_order_submitted")
        self.assertEqual(outcome.order_status, "submitted")

    def test_submit_exception_maps_error(self) -> None:
        broker = FakeBroker(submit_exception=RuntimeError("submit failed"))

        outcome = execute_prevalidated_market_order(request(), broker)

        self.assertEqual(len(broker.build_calls), 1)
        self.assertEqual(len(broker.submit_calls), 1)
        self.assertEqual(outcome.result, "error")
        self.assertEqual(outcome.reason, "order_submission_failed")
        self.assertIsNone(outcome.order_status)

    def test_reconciliation_required_calls_workflow_once_with_submit_intent(self) -> None:
        broker = FakeBroker(submit_result=order_result("reconciliation_required"))
        workflow = FakeReconciliationWorkflow(
            workflow_result("unresolved", manual_review_required=True)
        )

        outcome = execute_prevalidated_market_order(
            request(),
            broker,
            reconciliation_workflow=workflow,
        )

        self.assertEqual(len(workflow.calls), 1)
        call = workflow.calls[0]
        self.assertIs(call["broker"], broker)
        self.assertEqual(call["submit_result"].order_status, "reconciliation_required")
        self.assertEqual(call["intent"].broker_name, "fake")
        self.assertEqual(call["intent"].order_id, "101")
        self.assertIsNone(call["intent"].client_id)
        self.assertIsNone(call["intent"].perm_id)
        self.assertEqual(call["intent"].symbol, "AAPL")
        self.assertEqual(call["intent"].side, "buy")
        self.assertEqual(call["intent"].qty, 1)
        self.assertIsNone(call["intent"].submitted_at)
        self.assertEqual(outcome.result, "manual_review_required")

    def test_manual_review_workflow_maps_manual_review_required(self) -> None:
        workflow_value = workflow_result(
            "partially_filled_unresolved",
            manual_review_required=True,
        )
        broker = FakeBroker(submit_result=order_result("reconciliation_required"))

        outcome = execute_prevalidated_market_order(
            request(),
            broker,
            reconciliation_workflow=FakeReconciliationWorkflow(workflow_value),
        )

        self.assertEqual(outcome.result, "manual_review_required")
        self.assertEqual(outcome.reason, "partially_filled_unresolved_reason")
        self.assertEqual(outcome.submit_state, "submit_uncertain_reconciliation_required")
        self.assertEqual(outcome.reconciliation_status, "partially_filled_unresolved")
        self.assertEqual(outcome.manual_review_required, True)
        self.assertEqual(outcome.terminal_for_run, True)
        self.assertEqual(outcome.reconciliation_ambiguous, True)
        self.assertEqual(outcome.filled_qty, 1.0)
        self.assertIsNone(outcome.working_qty)
        self.assertIs(outcome.raw_reconciliation_result, workflow_value)

    def test_non_manual_workflow_maps_reconciled(self) -> None:
        workflow_value = workflow_result("accepted_unfilled", manual_review_required=False)
        broker = FakeBroker(submit_result=order_result("reconciliation_required"))

        outcome = execute_prevalidated_market_order(
            request(),
            broker,
            reconciliation_workflow=FakeReconciliationWorkflow(workflow_value),
        )

        self.assertEqual(outcome.result, "reconciled")
        self.assertEqual(outcome.reason, "accepted_unfilled_reason")
        self.assertEqual(outcome.reconciliation_status, "accepted_unfilled")
        self.assertEqual(outcome.manual_review_required, False)
        self.assertEqual(outcome.working_qty, 2.0)

    def test_missing_workflow_maps_manual_review_required(self) -> None:
        submit_result = order_result("reconciliation_required")
        broker = FakeBroker(submit_result=submit_result)

        outcome = execute_prevalidated_market_order(request(), broker)

        self.assertEqual(outcome.result, "manual_review_required")
        self.assertEqual(outcome.reason, "reconciliation_workflow_missing")
        self.assertEqual(outcome.order_status, "reconciliation_required")
        self.assertEqual(outcome.manual_review_required, True)
        self.assertEqual(outcome.terminal_for_run, True)
        self.assertEqual(outcome.reconciliation_ambiguous, True)
        self.assertIs(outcome.raw_submit_result, submit_result)

    def test_no_ibkr_imports(self) -> None:
        execute_prevalidated_market_order(
            request(),
            FakeBroker(submit_result=order_result("submitted")),
        )

        for module_name in IBKR_MODULES:
            self.assertNotIn(module_name, sys.modules)

    def test_fake_broker_does_not_require_cancel_flatten_retry_or_resubmit(self) -> None:
        broker = FakeBroker(submit_result=order_result("submitted"))

        execute_prevalidated_market_order(request(), broker)

        for method_name in ["cancel", "cancel_order", "flatten", "retry", "resubmit"]:
            with self.subTest(method=method_name):
                self.assertFalse(hasattr(broker, method_name))


if __name__ == "__main__":
    unittest.main()
