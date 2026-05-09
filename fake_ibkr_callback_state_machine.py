from __future__ import annotations

from collections.abc import Iterable, Mapping

from broker_interface import (
    BrokerAccountState,
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from fake_ibkr_callback_normalization import (
    is_open_order_status,
    is_terminal_order_status,
    normalize_order_status,
    optional_int,
    parse_buying_power,
    parse_int_qty,
)


Event = Mapping[str, object]


class IBKRLifecycleAggregator:
    def __init__(self, *, operation: str = "connect") -> None:
        self.operation = operation
        self._result: BrokerLifecycleResult | None = None

    def on_event(self, event: Event) -> None:
        if self._result is not None:
            return

        event_type = event.get("event_type")
        if event_type == "connect_ready":
            self._result = BrokerLifecycleResult(
                broker_name="ibkr",
                operation=self.operation,
                passed=True,
                reason="connect_ready",
                message=str(event.get("message", "connect_ready")),
                connected=True,
                retryable=False,
                elapsed_ms=optional_int(event.get("elapsed_ms")),
                raw_error=None,
            )
            return

        if event_type == "connect_error":
            self._result = BrokerLifecycleResult(
                broker_name="ibkr",
                operation=self.operation,
                passed=False,
                reason="connect_error",
                message=str(event.get("message", "connect_error")),
                connected=False,
                retryable=bool(event.get("retryable", True)),
                elapsed_ms=optional_int(event.get("elapsed_ms")),
                raw_error=event,
            )
            return

        if event_type == "timeout" and event.get("operation", self.operation) == self.operation:
            self._result = BrokerLifecycleResult(
                broker_name="ibkr",
                operation=self.operation,
                passed=False,
                reason=f"{self.operation}_timeout",
                message=str(event.get("message", f"{self.operation}_timeout")),
                connected=False,
                retryable=True,
                elapsed_ms=optional_int(event.get("elapsed_ms")),
                raw_error=event,
            )

    def result(self) -> BrokerLifecycleResult:
        if self._result is not None:
            return self._result

        return BrokerLifecycleResult(
            broker_name="ibkr",
            operation=self.operation,
            passed=False,
            reason=f"{self.operation}_timeout",
            message=f"{self.operation}_timeout",
            connected=False,
            retryable=True,
            elapsed_ms=None,
            raw_error=None,
        )


class IBKRAccountSnapshotAggregator:
    def __init__(self, *, request_id: str | None = None) -> None:
        self.request_id = request_id
        self._account_event: Event | None = None
        self._complete = False
        self._error: str | None = None

    def on_event(self, event: Event) -> None:
        if not _strict_matches_request(event, self.request_id):
            return

        event_type = event.get("event_type")
        if event_type == "account_summary":
            if "buying_power" not in event:
                return
            self._account_event = event
            return

        if event_type == "account_summary_end":
            self._complete = True

    def result(self) -> BrokerAccountState:
        if not self._complete:
            raise ValueError("IBKR account summary did not receive matching end marker")
        if self._account_event is None:
            raise ValueError("No fake IBKR account buying_power callback received")

        try:
            buying_power = parse_buying_power(self._account_event["buying_power"])
        except (TypeError, ValueError) as exc:
            self._error = "invalid_account_buying_power"
            raise ValueError("Invalid fake IBKR account buying_power callback") from exc

        return BrokerAccountState(
            broker_name="ibkr",
            buying_power=buying_power,
            raw_account=self._account_event,
        )


class IBKRPositionSnapshotAggregator:
    def __init__(self, *, symbol: str, request_id: str | None = None) -> None:
        self.symbol = symbol.upper()
        self.request_id = request_id
        self._matched_position: BrokerPositionState | None = None
        self._complete = False
        self._error_result: BrokerPositionState | None = None

    def on_event(self, event: Event) -> None:
        if self._error_result is not None:
            return
        if not _matches_request(event, self.request_id):
            return

        event_type = event.get("event_type")
        if event_type == "position":
            if str(event.get("symbol", "")).upper() != self.symbol:
                return
            raw_qty = str(event.get("qty", "0"))
            try:
                qty = parse_int_qty(raw_qty)
            except (TypeError, ValueError):
                self._error_result = BrokerPositionState(
                    broker_name="ibkr",
                    found=None,
                    qty=None,
                    raw_qty=raw_qty,
                    side=None,
                    reason="position_lookup_error",
                    error="invalid_position_qty",
                )
                return

            if qty == 0:
                self._matched_position = BrokerPositionState(
                    broker_name="ibkr",
                    found=False,
                    qty=0,
                    raw_qty=raw_qty,
                    side=None,
                    reason="no_position",
                )
                return

            self._matched_position = BrokerPositionState(
                broker_name="ibkr",
                found=True,
                qty=abs(qty),
                raw_qty=raw_qty,
                side=str(event.get("side", "long")),
                reason="position_found",
            )
            return

        if event_type == "position_end":
            self._complete = True

    def result(self) -> BrokerPositionState:
        if self._error_result is not None:
            return self._error_result
        if not self._complete:
            return BrokerPositionState(
                broker_name="ibkr",
                found=None,
                qty=None,
                raw_qty=None,
                side=None,
                reason="position_lookup_error",
                error="position_snapshot_incomplete",
            )
        if self._matched_position is not None:
            return self._matched_position
        return BrokerPositionState(
            broker_name="ibkr",
            found=False,
            qty=0,
            raw_qty="0",
            side=None,
            reason="no_position",
        )


class IBKROpenOrdersSnapshotAggregator:
    def __init__(self, *, symbol: str, request_id: str | None = None) -> None:
        self.symbol = symbol.upper()
        self.request_id = request_id
        self._total_qty = 0
        self._order_count = 0
        self._seen_order_ids: set[str] = set()
        self._complete = False
        self._error_result: BrokerOpenOrderState | None = None

    def on_event(self, event: Event) -> None:
        if self._error_result is not None:
            return
        if not _matches_request(event, self.request_id):
            return

        event_type = event.get("event_type")
        if event_type == "open_order":
            if str(event.get("symbol", "")).upper() != self.symbol:
                return
            if str(event.get("side", "")).upper() != "BUY":
                return
            if not is_open_order_status(event.get("status", "")):
                return

            order_id = event.get("order_id")
            if order_id is not None:
                order_id_text = str(order_id)
                if order_id_text in self._seen_order_ids:
                    return
                self._seen_order_ids.add(order_id_text)

            raw_qty = str(event.get("qty", "0"))
            try:
                qty = parse_int_qty(raw_qty)
            except (TypeError, ValueError):
                self._error_result = BrokerOpenOrderState(
                    broker_name="ibkr",
                    passed=False,
                    open_buy_order_qty=None,
                    open_buy_order_count=None,
                    reason="open_buy_order_lookup_failed",
                    error="invalid_open_order_qty",
                )
                return

            self._total_qty += qty
            self._order_count += 1
            return

        if event_type == "open_order_end":
            self._complete = True

    def result(self) -> BrokerOpenOrderState:
        if self._error_result is not None:
            return self._error_result
        if not self._complete:
            return BrokerOpenOrderState(
                broker_name="ibkr",
                passed=False,
                open_buy_order_qty=None,
                open_buy_order_count=None,
                reason="open_buy_order_lookup_failed",
                error="open_order_snapshot_incomplete",
            )
        return BrokerOpenOrderState(
            broker_name="ibkr",
            passed=True,
            open_buy_order_qty=self._total_qty,
            open_buy_order_count=self._order_count,
            reason="open_buy_orders_loaded",
        )


class IBKROrderStatusAggregator:
    def __init__(self, *, order_id: str | None = None) -> None:
        self.order_id = order_id
        self._last_broker_status: str | None = None
        self._last_order_status: str | None = None
        self._is_terminal = False
        self._last_raw_event: Event | None = None
        self._terminal_status: str | None = None
        self._conflict_result: BrokerOrderResult | None = None
        self._timeout_result: BrokerOrderResult | None = None

    def on_event(self, event: Event) -> None:
        if self._conflict_result is not None or self._timeout_result is not None:
            return

        event_type = event.get("event_type")
        if event_type == "next_valid_id" and self.order_id is None:
            self.order_id = str(event.get("order_id"))
            self._last_raw_event = event
            return

        if event_type == "order_status":
            event_order_id = event.get("order_id")
            if event_order_id is not None:
                event_order_id_text = str(event_order_id)
                if self.order_id is None:
                    self.order_id = event_order_id_text
                elif event_order_id_text != self.order_id:
                    return

            self._last_raw_event = event
            self._last_broker_status = str(event.get("status"))
            normalized_status = normalize_order_status(self._last_broker_status)

            if self._terminal_status is not None:
                if normalized_status != self._terminal_status:
                    self._conflict_result = BrokerOrderResult(
                        broker_name="ibkr",
                        order_id=self.order_id,
                        order_status="conflicting_terminal_status",
                        broker_status=self._last_broker_status,
                        is_terminal=True,
                        raw_response=event,
                    )
                return

            self._last_order_status = normalized_status
            self._is_terminal = is_terminal_order_status(normalized_status)
            if self._is_terminal:
                self._terminal_status = normalized_status
            return

        if event_type == "timeout" and event.get("operation") == "submit_market_order":
            self._timeout_result = BrokerOrderResult(
                broker_name="ibkr",
                order_id=self.order_id,
                order_status="timeout",
                broker_status=self._last_broker_status if self.order_id is not None else None,
                is_terminal=True,
                raw_response=event,
            )

    def result(self) -> BrokerOrderResult:
        if self._conflict_result is not None:
            return self._conflict_result
        if self._timeout_result is not None:
            return self._timeout_result
        if self.order_id is None:
            return BrokerOrderResult(
                broker_name="ibkr",
                order_id=None,
                order_status="timeout",
                broker_status=self._last_broker_status,
                is_terminal=True,
                raw_response=self._last_raw_event,
            )
        return BrokerOrderResult(
            broker_name="ibkr",
            order_id=self.order_id,
            order_status=self._last_order_status or "submitted",
            broker_status=self._last_broker_status,
            is_terminal=self._is_terminal,
            raw_response=self._last_raw_event,
        )


def replay(aggregator, events: Iterable[Event]):
    for event in events:
        aggregator.on_event(event)
    return aggregator.result()


def _matches_request(event: Event, request_id: str | None) -> bool:
    if request_id is None:
        return True
    event_request_id = event.get("request_id")
    return event_request_id is None or str(event_request_id) == request_id


def _strict_matches_request(event: Event, request_id: str | None) -> bool:
    if request_id is None:
        return False
    event_request_id = event.get("request_id")
    if event_request_id is None:
        return False
    return str(event_request_id) == request_id
