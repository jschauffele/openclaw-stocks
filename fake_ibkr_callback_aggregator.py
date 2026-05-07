from __future__ import annotations

from collections.abc import Iterable, Mapping

from broker_interface import (
    BrokerAccountState,
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)


Event = Mapping[str, object]

_OPEN_ORDER_STATUSES = {
    "apisent",
    "pendingcancel",
    "pendingsubmit",
    "presubmitted",
    "submitted",
}

_TERMINAL_ORDER_STATUS_MAP = {
    "filled": "filled",
    "cancelled": "canceled",
    "canceled": "canceled",
    "inactive": "rejected",
    "rejected": "rejected",
}

_NON_TERMINAL_ORDER_STATUS_MAP = {
    "apisent": "submitted",
    "pendingcancel": "submitted",
    "pendingsubmit": "submitted",
    "presubmitted": "submitted",
    "submitted": "submitted",
}


def aggregate_lifecycle(
    events: Iterable[Event],
    *,
    operation: str = "connect",
) -> BrokerLifecycleResult:
    for event in events:
        event_type = event.get("event_type")
        if event_type == "connect_ready":
            return BrokerLifecycleResult(
                broker_name="ibkr",
                operation=operation,
                passed=True,
                reason="connect_ready",
                message=str(event.get("message", "connect_ready")),
                connected=True,
                retryable=False,
                elapsed_ms=_optional_int(event.get("elapsed_ms")),
                raw_error=None,
            )
        if event_type == "connect_error":
            return BrokerLifecycleResult(
                broker_name="ibkr",
                operation=operation,
                passed=False,
                reason="connect_error",
                message=str(event.get("message", "connect_error")),
                connected=False,
                retryable=bool(event.get("retryable", True)),
                elapsed_ms=_optional_int(event.get("elapsed_ms")),
                raw_error=event,
            )
        if event_type == "timeout" and event.get("operation", operation) == operation:
            return BrokerLifecycleResult(
                broker_name="ibkr",
                operation=operation,
                passed=False,
                reason=f"{operation}_timeout",
                message=str(event.get("message", f"{operation}_timeout")),
                connected=False,
                retryable=True,
                elapsed_ms=_optional_int(event.get("elapsed_ms")),
                raw_error=event,
            )

    return BrokerLifecycleResult(
        broker_name="ibkr",
        operation=operation,
        passed=False,
        reason=f"{operation}_timeout",
        message=f"{operation}_timeout",
        connected=False,
        retryable=True,
        elapsed_ms=None,
        raw_error=None,
    )


def aggregate_account(events: Iterable[Event]) -> BrokerAccountState:
    for event in events:
        if event.get("event_type") != "account_value":
            continue
        if "buying_power" not in event:
            continue
        try:
            buying_power = float(event["buying_power"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid fake IBKR account buying_power callback") from exc
        return BrokerAccountState(
            broker_name="ibkr",
            buying_power=buying_power,
            raw_account=event,
        )

    raise ValueError("No fake IBKR account buying_power callback received")


def aggregate_position(events: Iterable[Event], *, symbol: str) -> BrokerPositionState:
    normalized_symbol = symbol.upper()
    matched_position: BrokerPositionState | None = None

    for event in events:
        event_type = event.get("event_type")
        if event_type == "position":
            if str(event.get("symbol", "")).upper() != normalized_symbol:
                continue
            raw_qty = str(event.get("qty", "0"))
            try:
                qty = int(float(raw_qty))
            except (TypeError, ValueError):
                return BrokerPositionState(
                    broker_name="ibkr",
                    found=None,
                    qty=None,
                    raw_qty=raw_qty,
                    side=None,
                    reason="position_lookup_error",
                    error="invalid_position_qty",
                )
            if qty == 0:
                matched_position = BrokerPositionState(
                    broker_name="ibkr",
                    found=False,
                    qty=0,
                    raw_qty=raw_qty,
                    side=None,
                    reason="no_position",
                )
                continue
            matched_position = BrokerPositionState(
                broker_name="ibkr",
                found=True,
                qty=abs(qty),
                raw_qty=raw_qty,
                side=str(event.get("side", "long")),
                reason="position_found",
            )
        if event_type == "position_end":
            if matched_position is not None:
                return matched_position
            return BrokerPositionState(
                broker_name="ibkr",
                found=False,
                qty=0,
                raw_qty="0",
                side=None,
                reason="no_position",
            )

    return BrokerPositionState(
        broker_name="ibkr",
        found=None,
        qty=None,
        raw_qty=None,
        side=None,
        reason="position_lookup_error",
        error="position_snapshot_incomplete",
    )


def aggregate_open_buy_orders(
    events: Iterable[Event],
    *,
    symbol: str,
) -> BrokerOpenOrderState:
    normalized_symbol = symbol.upper()
    total_qty = 0
    order_count = 0
    seen_order_ids: set[str] = set()

    for event in events:
        event_type = event.get("event_type")
        if event_type == "open_order":
            if str(event.get("symbol", "")).upper() != normalized_symbol:
                continue
            if str(event.get("side", "")).upper() != "BUY":
                continue
            status = str(event.get("status", "")).lower()
            if status not in _OPEN_ORDER_STATUSES:
                continue
            order_id = event.get("order_id")
            if order_id is not None:
                order_id_text = str(order_id)
                if order_id_text in seen_order_ids:
                    continue
                seen_order_ids.add(order_id_text)
            raw_qty = str(event.get("qty", "0"))
            try:
                qty = int(float(raw_qty))
            except (TypeError, ValueError):
                return BrokerOpenOrderState(
                    broker_name="ibkr",
                    passed=False,
                    open_buy_order_qty=None,
                    open_buy_order_count=None,
                    reason="open_buy_order_lookup_failed",
                    error="invalid_open_order_qty",
                )
            total_qty += qty
            order_count += 1
        if event_type == "open_order_end":
            return BrokerOpenOrderState(
                broker_name="ibkr",
                passed=True,
                open_buy_order_qty=total_qty,
                open_buy_order_count=order_count,
                reason="open_buy_orders_loaded",
            )

    return BrokerOpenOrderState(
        broker_name="ibkr",
        passed=False,
        open_buy_order_qty=None,
        open_buy_order_count=None,
        reason="open_buy_order_lookup_failed",
        error="open_order_snapshot_incomplete",
    )


def aggregate_order_result(events: Iterable[Event]) -> BrokerOrderResult:
    order_id: str | None = None
    last_broker_status: str | None = None
    last_order_status: str | None = None
    is_terminal = False
    last_raw_event: Event | None = None
    terminal_status: str | None = None

    for event in events:
        event_type = event.get("event_type")
        if event_type == "next_valid_id" and order_id is None:
            order_id = str(event.get("order_id"))
            last_raw_event = event
            continue

        if event_type == "order_status":
            event_order_id = event.get("order_id")
            if event_order_id is not None:
                event_order_id_text = str(event_order_id)
                if order_id is None:
                    order_id = event_order_id_text
                elif event_order_id_text != order_id:
                    continue

            last_raw_event = event
            last_broker_status = str(event.get("status"))
            normalized_status = _normalize_order_status(last_broker_status)
            if terminal_status is not None:
                if normalized_status != terminal_status:
                    return BrokerOrderResult(
                        broker_name="ibkr",
                        order_id=order_id,
                        order_status="conflicting_terminal_status",
                        broker_status=last_broker_status,
                        is_terminal=True,
                        raw_response=event,
                    )
                continue
            last_order_status = normalized_status
            is_terminal = normalized_status in {"filled", "canceled", "rejected"}
            if is_terminal:
                terminal_status = normalized_status
                continue

        if event_type == "timeout" and event.get("operation") == "submit_market_order":
            if order_id is None:
                return BrokerOrderResult(
                    broker_name="ibkr",
                    order_id=None,
                    order_status="timeout",
                    broker_status=None,
                    is_terminal=True,
                    raw_response=event,
                )
            return BrokerOrderResult(
                broker_name="ibkr",
                order_id=order_id,
                order_status="timeout",
                broker_status=last_broker_status,
                is_terminal=True,
                raw_response=event,
            )

    if order_id is None:
        return BrokerOrderResult(
            broker_name="ibkr",
            order_id=None,
            order_status="timeout",
            broker_status=last_broker_status,
            is_terminal=True,
            raw_response=last_raw_event,
        )

    return BrokerOrderResult(
        broker_name="ibkr",
        order_id=order_id,
        order_status=last_order_status or "submitted",
        broker_status=last_broker_status,
        is_terminal=is_terminal,
        raw_response=last_raw_event,
    )


def _normalize_order_status(broker_status: str) -> str:
    normalized = broker_status.lower()
    if normalized in _TERMINAL_ORDER_STATUS_MAP:
        return _TERMINAL_ORDER_STATUS_MAP[normalized]
    if normalized in _NON_TERMINAL_ORDER_STATUS_MAP:
        return _NON_TERMINAL_ORDER_STATUS_MAP[normalized]
    return normalized


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
