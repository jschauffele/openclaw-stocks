from __future__ import annotations

from broker_interface import (
    BrokerExecutionFill,
    BrokerExecutionSnapshotState,
    BrokerOpenOrderState,
    BrokerPositionState,
    BrokerReconciliationResult,
    BrokerSubmitIntent,
)


class IBKRBrokerReconciler:
    def reconcile(
        self,
        *,
        intent: BrokerSubmitIntent,
        execution_snapshot: BrokerExecutionSnapshotState,
        open_order_snapshot: BrokerOpenOrderState,
        position_snapshot: BrokerPositionState | None = None,
    ) -> BrokerReconciliationResult:
        matched_fills = _matched_fills(intent, execution_snapshot)
        filled_qty = sum(fill.shares for fill in matched_fills)
        matched_exec_ids = tuple(fill.exec_id for fill in matched_fills)
        avg_fill_price = _weighted_avg_fill_price(matched_fills)
        working_qty = _working_qty(open_order_snapshot)

        evidence = {
            "intent": intent,
            "execution_snapshot": execution_snapshot,
            "open_order_snapshot": open_order_snapshot,
            "position_snapshot": position_snapshot,
            "matched_fills": matched_fills,
        }

        if execution_snapshot.passed and execution_snapshot.fill_count and _ambiguous_execution_evidence(
            intent,
            execution_snapshot,
            matched_fills,
        ):
            return _result(
                intent,
                status="unresolved",
                filled_qty=0.0,
                working_qty=None,
                avg_fill_price=None,
                matched_exec_ids=(),
                reason="ambiguous_execution_evidence",
                ambiguous=True,
                raw_evidence=evidence,
            )

        if filled_qty >= intent.qty and intent.qty > 0:
            return _result(
                intent,
                status="filled",
                filled_qty=filled_qty,
                working_qty=0.0,
                avg_fill_price=avg_fill_price,
                matched_exec_ids=matched_exec_ids,
                reason="matched_executions_fill_intended_qty",
                raw_evidence=evidence,
            )

        if filled_qty > 0:
            if working_qty is not None and working_qty > 0:
                return _result(
                    intent,
                    status="partially_filled_working",
                    filled_qty=filled_qty,
                    working_qty=working_qty,
                    avg_fill_price=avg_fill_price,
                    matched_exec_ids=matched_exec_ids,
                    reason="matched_executions_with_open_order_residual",
                    raw_evidence=evidence,
                )
            return _result(
                intent,
                status="partially_filled_unresolved",
                filled_qty=filled_qty,
                working_qty=None,
                avg_fill_price=avg_fill_price,
                matched_exec_ids=matched_exec_ids,
                reason="matched_executions_without_working_residual",
                ambiguous=True,
                raw_evidence=evidence,
            )

        if working_qty is not None and working_qty > 0:
            return _result(
                intent,
                status="accepted_unfilled",
                filled_qty=0.0,
                working_qty=working_qty,
                avg_fill_price=None,
                matched_exec_ids=(),
                reason="open_order_snapshot_shows_working_order",
                raw_evidence=evidence,
            )

        if _position_only_evidence(position_snapshot):
            return _result(
                intent,
                status="unresolved",
                filled_qty=0.0,
                working_qty=None,
                avg_fill_price=None,
                matched_exec_ids=(),
                reason="position_only_evidence_is_ambiguous",
                ambiguous=True,
                raw_evidence=evidence,
            )

        return _result(
            intent,
            status="unresolved",
            filled_qty=0.0,
            working_qty=None,
            avg_fill_price=None,
            matched_exec_ids=(),
            reason="no_deterministic_broker_evidence",
            ambiguous=True,
            raw_evidence=evidence,
        )


def _matched_fills(
    intent: BrokerSubmitIntent,
    execution_snapshot: BrokerExecutionSnapshotState,
) -> tuple[BrokerExecutionFill, ...]:
    if not execution_snapshot.passed:
        return ()
    return tuple(
        fill for fill in execution_snapshot.fills if _fill_matches_intent(intent, fill)
    )


def _fill_matches_intent(intent: BrokerSubmitIntent, fill: BrokerExecutionFill) -> bool:
    if fill.symbol.upper() != intent.symbol.upper():
        return False
    if _normalize_side(fill.side) != _normalize_side(intent.side):
        return False
    if intent.perm_id is not None and fill.perm_id is not None:
        return fill.perm_id == intent.perm_id
    if intent.order_id is not None and fill.order_id is not None:
        if fill.order_id != intent.order_id:
            return False
        if intent.client_id is not None and fill.client_id is not None:
            return fill.client_id == intent.client_id
        return True
    return False


def _ambiguous_execution_evidence(
    intent: BrokerSubmitIntent,
    execution_snapshot: BrokerExecutionSnapshotState,
    matched_fills: tuple[BrokerExecutionFill, ...],
) -> bool:
    unmatched_relevant = [
        fill
        for fill in execution_snapshot.fills
        if fill.symbol.upper() == intent.symbol.upper()
        and _normalize_side(fill.side) == _normalize_side(intent.side)
        and fill not in matched_fills
    ]
    return bool(unmatched_relevant and not matched_fills)


def _working_qty(open_order_snapshot: BrokerOpenOrderState) -> float | None:
    if not open_order_snapshot.passed:
        return None
    if open_order_snapshot.open_buy_order_qty is None:
        return None
    return float(open_order_snapshot.open_buy_order_qty)


def _weighted_avg_fill_price(fills: tuple[BrokerExecutionFill, ...]) -> float | None:
    priced = [
        (fill.avg_price if fill.avg_price is not None else fill.price, fill.shares)
        for fill in fills
        if fill.avg_price is not None or fill.price is not None
    ]
    total_shares = sum(shares for _price, shares in priced)
    if not priced or not total_shares:
        return None
    return sum(price * shares for price, shares in priced) / total_shares


def _position_only_evidence(position_snapshot: BrokerPositionState | None) -> bool:
    return bool(
        position_snapshot is not None
        and position_snapshot.found is True
        and position_snapshot.qty is not None
        and position_snapshot.qty > 0
    )


def _normalize_side(side: str) -> str:
    side = side.upper()
    if side in {"BUY", "BOT"}:
        return "BUY"
    if side in {"SELL", "SLD"}:
        return "SELL"
    return side


def _result(
    intent: BrokerSubmitIntent,
    *,
    status: str,
    filled_qty: float,
    working_qty: float | None,
    avg_fill_price: float | None,
    matched_exec_ids: tuple[str, ...],
    reason: str,
    ambiguous: bool = False,
    raw_evidence: object | None = None,
) -> BrokerReconciliationResult:
    return BrokerReconciliationResult(
        broker_name="ibkr",
        status=status,
        order_id=intent.order_id,
        perm_id=intent.perm_id,
        symbol=intent.symbol,
        side=intent.side,
        intended_qty=intent.qty,
        filled_qty=filled_qty,
        working_qty=working_qty,
        avg_fill_price=avg_fill_price,
        matched_exec_ids=matched_exec_ids,
        reason=reason,
        ambiguous=ambiguous,
        raw_evidence=raw_evidence,
    )
