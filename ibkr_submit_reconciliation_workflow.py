from __future__ import annotations

from broker_interface import (
    BrokerExecutionSnapshotState,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
    BrokerSubmitIntent,
    BrokerSubmitReconciliationResult,
)
from ibkr_broker_reconciler import IBKRBrokerReconciler


class IBKRSubmitReconciliationWorkflow:
    def __init__(self, *, reconciler: IBKRBrokerReconciler | None = None) -> None:
        self.reconciler = reconciler or IBKRBrokerReconciler()

    def reconcile_if_required(
        self,
        *,
        broker,
        submit_result: BrokerOrderResult,
        intent: BrokerSubmitIntent,
        timeout_seconds: float | None = None,
    ) -> BrokerSubmitReconciliationResult:
        if submit_result.order_status != "reconciliation_required":
            return BrokerSubmitReconciliationResult(
                broker_name="ibkr",
                submit_state="submit_acknowledged",
                reconciliation_status=None,
                terminal_for_run=True,
                manual_review_required=False,
                order_id=submit_result.order_id,
                perm_id=intent.perm_id,
                filled_qty=0.0,
                working_qty=None,
                reason="submit_reconciliation_not_required",
                ambiguous=False,
                submit_result=submit_result,
            )

        try:
            execution_snapshot = broker.get_execution_snapshot(
                symbol=intent.symbol,
                since=intent.submitted_at,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            execution_snapshot = _failed_execution_snapshot(exc)

        try:
            open_order_snapshot = broker.get_open_buy_order_qty(
                intent.symbol,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            open_order_snapshot = _failed_open_order_snapshot(exc)

        try:
            position_snapshot = broker.get_existing_position(
                intent.symbol,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            position_snapshot = _failed_position_snapshot(exc)

        reconciliation = self.reconciler.reconcile(
            intent=intent,
            execution_snapshot=execution_snapshot,
            open_order_snapshot=open_order_snapshot,
            position_snapshot=position_snapshot,
        )

        manual_review_required = reconciliation.status in {
            "unresolved",
            "partially_filled_unresolved",
        }
        return BrokerSubmitReconciliationResult(
            broker_name="ibkr",
            submit_state="submit_uncertain_reconciliation_required",
            reconciliation_status=reconciliation.status,
            terminal_for_run=True,
            manual_review_required=manual_review_required,
            order_id=reconciliation.order_id,
            perm_id=reconciliation.perm_id,
            filled_qty=reconciliation.filled_qty,
            working_qty=reconciliation.working_qty,
            reason=reconciliation.reason,
            ambiguous=reconciliation.ambiguous,
            submit_result=submit_result,
            reconciliation_result=reconciliation,
        )


def _execution_side(side: str) -> str:
    normalized = side.upper()
    if normalized == "BUY":
        return "BOT"
    if normalized == "SELL":
        return "SLD"
    return normalized


def _failed_execution_snapshot(exc: Exception) -> BrokerExecutionSnapshotState:
    return BrokerExecutionSnapshotState(
        broker_name="ibkr",
        passed=False,
        fills=(),
        fill_count=0,
        total_shares=0.0,
        cumulative_qty=None,
        avg_fill_price=None,
        reason="execution_lookup_failed",
        error=str(exc) or type(exc).__name__,
    )


def _failed_open_order_snapshot(exc: Exception) -> BrokerOpenOrderState:
    return BrokerOpenOrderState(
        broker_name="ibkr",
        passed=False,
        open_buy_order_qty=None,
        open_buy_order_count=None,
        reason="open_buy_order_lookup_failed",
        error=str(exc) or type(exc).__name__,
    )


def _failed_position_snapshot(exc: Exception) -> BrokerPositionState:
    return BrokerPositionState(
        broker_name="ibkr",
        found=None,
        qty=None,
        raw_qty=None,
        side=None,
        reason="position_lookup_error",
        error=str(exc) or type(exc).__name__,
    )
