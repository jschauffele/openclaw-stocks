from __future__ import annotations

from dataclasses import dataclass, field

from broker_interface import BrokerSubmitIntent


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    run_id: str
    broker_name: str
    mode: str
    symbol: str
    side: str
    qty: int
    order_type: str
    trigger_source: str | None
    strategy_reason: str | None
    signal: str | None
    decision: str | None


@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    result: str
    reason: str
    mode: str
    broker_name: str
    order_status: str | None = None
    submit_state: str | None = None
    reconciliation_status: str | None = None
    manual_review_required: bool | None = None
    terminal_for_run: bool | None = None
    reconciliation_ambiguous: bool | None = None
    filled_qty: float | None = None
    working_qty: float | None = None
    notes: list[str] = field(default_factory=list)
    raw_submit_result: object | None = None
    raw_reconciliation_result: object | None = None


def execute_prevalidated_market_order(
    request: ExecutionRequest,
    broker,
    reconciliation_workflow=None,
    clock=None,
) -> ExecutionOutcome:
    order = broker.build_market_order(request.symbol, request.qty)
    notes = _request_notes(request)

    if request.mode == "dry_run":
        return ExecutionOutcome(
            result="success",
            reason="dry_run_completed",
            mode=request.mode,
            broker_name=request.broker_name,
            notes=notes,
        )

    try:
        submit_result = broker.submit_market_order(order)
    except Exception:
        return ExecutionOutcome(
            result="error",
            reason="order_submission_failed",
            mode=request.mode,
            broker_name=request.broker_name,
            notes=notes,
        )

    if submit_result.order_status == "reconciliation_required":
        if reconciliation_workflow is None:
            return ExecutionOutcome(
                result="manual_review_required",
                reason="reconciliation_workflow_missing",
                mode=request.mode,
                broker_name=request.broker_name,
                order_status=submit_result.order_status,
                manual_review_required=True,
                terminal_for_run=True,
                reconciliation_ambiguous=True,
                notes=notes,
                raw_submit_result=submit_result,
            )

        workflow_result = reconciliation_workflow.reconcile_if_required(
            broker=broker,
            submit_result=submit_result,
            intent=BrokerSubmitIntent(
                broker_name=request.broker_name,
                order_id=submit_result.order_id,
                client_id=None,
                perm_id=None,
                symbol=request.symbol,
                side=request.side,
                qty=request.qty,
                submitted_at=_submitted_at(clock),
            ),
        )
        return _outcome_from_reconciliation(
            request=request,
            submit_result=submit_result,
            workflow_result=workflow_result,
            notes=notes,
        )

    return ExecutionOutcome(
        result="success",
        reason="paper_order_submitted",
        mode=request.mode,
        broker_name=request.broker_name,
        order_status=submit_result.order_status,
        notes=notes,
        raw_submit_result=submit_result,
    )


def _outcome_from_reconciliation(
    *,
    request: ExecutionRequest,
    submit_result,
    workflow_result,
    notes: list[str],
) -> ExecutionOutcome:
    return ExecutionOutcome(
        result=(
            "manual_review_required"
            if workflow_result.manual_review_required
            else "reconciled"
        ),
        reason=workflow_result.reason,
        mode=request.mode,
        broker_name=request.broker_name,
        order_status=submit_result.order_status,
        submit_state=workflow_result.submit_state,
        reconciliation_status=workflow_result.reconciliation_status,
        manual_review_required=workflow_result.manual_review_required,
        terminal_for_run=workflow_result.terminal_for_run,
        reconciliation_ambiguous=workflow_result.ambiguous,
        filled_qty=workflow_result.filled_qty,
        working_qty=workflow_result.working_qty,
        notes=notes,
        raw_submit_result=submit_result,
        raw_reconciliation_result=workflow_result,
    )


def _request_notes(request: ExecutionRequest) -> list[str]:
    notes = []
    if request.strategy_reason is not None:
        notes.append(f"Strategy reason={request.strategy_reason}")
    if request.signal is not None:
        notes.append(f"signal={request.signal}")
    if request.decision is not None:
        notes.append(f"decision={request.decision}")
    return notes


def _submitted_at(clock) -> str | None:
    if clock is None:
        return None
    now = getattr(clock, "now", None)
    if not callable(now):
        return None
    value = now()
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    return str(value)
