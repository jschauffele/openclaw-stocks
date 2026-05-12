from __future__ import annotations

from collections.abc import Iterable, Mapping

from broker_interface import (
    BrokerAccountState,
    BrokerExecutionFill,
    BrokerExecutionSnapshotState,
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
    def __init__(
        self,
        *,
        symbol: str,
        request_id: str | None = None,
        generation: object | None = None,
    ) -> None:
        self.symbol = symbol.upper()
        self.request_id = request_id
        self.generation = str(generation) if generation is not None else None
        self._matched_position: BrokerPositionState | None = None
        self._complete = False
        self._error_result: BrokerPositionState | None = None

    def on_event(self, event: Event) -> None:
        if self._error_result is not None:
            return
        if not _strict_matches_request(event, self.request_id):
            return
        if self.generation is not None and not _strict_matches_generation(
            event,
            self.generation,
        ):
            return

        event_type = event.get("event_type")
        if event_type == "position_multi":
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

        if event_type == "position_multi_end":
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
    def __init__(
        self,
        *,
        symbol: str,
        generation: object | None = None,
    ) -> None:
        self.symbol = symbol.upper()
        self.generation = str(generation) if generation is not None else None
        self._orders: dict[str, dict[str, object]] = {}
        self._complete = False
        self._error_result: BrokerOpenOrderState | None = None

    def on_event(self, event: Event) -> None:
        if self._error_result is not None:
            return
        if not _strict_matches_generation(event, self.generation):
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
            order_key = _open_order_key(event)
            if order_key is None:
                return
            if order_key in self._orders:
                return

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

            self._orders[order_key] = {
                "qty": qty,
                "status": str(event.get("status", "")),
                "order_id": order_id,
                "perm_id": event.get("perm_id"),
            }
            return

        if event_type == "order_status":
            order_key = _open_order_key(event)
            if order_key is None or order_key not in self._orders:
                return
            self._orders[order_key]["status"] = str(event.get("status", ""))
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
        open_orders = [
            order
            for order in self._orders.values()
            if is_open_order_status(order.get("status", ""))
        ]
        return BrokerOpenOrderState(
            broker_name="ibkr",
            passed=True,
            open_buy_order_qty=sum(int(order["qty"]) for order in open_orders),
            open_buy_order_count=len(open_orders),
            reason="open_buy_orders_loaded",
        )


class IBKRExecutionSnapshotAggregator:
    def __init__(
        self,
        *,
        generation: object | None = None,
        symbol: str | None = None,
    ) -> None:
        self.generation = str(generation) if generation is not None else None
        self.symbol = symbol.upper() if symbol is not None else None
        self._fills_by_correction_key: dict[str, BrokerExecutionFill] = {}
        self._exec_ids: set[str] = set()
        self._complete = False
        self._error_result: BrokerExecutionSnapshotState | None = None

    def on_event(self, event: Event) -> None:
        if self._error_result is not None:
            return
        if not _strict_matches_generation(event, self.generation):
            return

        event_type = event.get("event_type")
        if event_type == "exec_details":
            if self.symbol is not None and str(event.get("symbol", "")).upper() != self.symbol:
                return
            exec_id = str(event.get("exec_id") or "")
            if not exec_id:
                return
            if exec_id in self._exec_ids:
                return

            try:
                shares = _optional_float(event.get("shares"))
                cumulative_qty = _optional_float(event.get("cumulative_qty"))
                avg_price = _optional_float(event.get("avg_price"))
                price = _optional_float(event.get("price"))
            except (TypeError, ValueError):
                self._error_result = _execution_snapshot_error(
                    error="invalid_execution_numeric_field",
                )
                return
            if shares is None:
                self._error_result = _execution_snapshot_error(
                    error="missing_execution_shares",
                )
                return

            fill = BrokerExecutionFill(
                exec_id=exec_id,
                order_id=_optional_text(event.get("order_id")),
                client_id=_optional_text(event.get("client_id")),
                perm_id=_optional_text(event.get("perm_id")),
                symbol=str(event.get("symbol", "")),
                side=str(event.get("side", "")),
                shares=shares,
                cumulative_qty=cumulative_qty,
                avg_price=avg_price,
                price=price,
                time=_optional_text(event.get("time")),
                raw_execution=event.get("raw_execution", event),
            )
            correction_key = _execution_correction_key(exec_id)
            previous = self._fills_by_correction_key.get(correction_key)
            if previous is not None:
                self._exec_ids.discard(previous.exec_id)
            self._fills_by_correction_key[correction_key] = fill
            self._exec_ids.add(exec_id)
            return

        if event_type == "exec_details_end":
            self._complete = True

    def result(self) -> BrokerExecutionSnapshotState:
        if self._error_result is not None:
            return self._error_result
        if not self._complete:
            return _execution_snapshot_error(error="execution_snapshot_incomplete")

        fills = tuple(
            sorted(
                self._fills_by_correction_key.values(),
                key=lambda fill: (fill.time or "", fill.exec_id),
            )
        )
        total_shares = sum(fill.shares for fill in fills)
        cumulative_values = [
            fill.cumulative_qty for fill in fills if fill.cumulative_qty is not None
        ]
        cumulative_qty = max(cumulative_values) if cumulative_values else None
        weighted_prices = [
            (fill.avg_price if fill.avg_price is not None else fill.price, fill.shares)
            for fill in fills
            if fill.avg_price is not None or fill.price is not None
        ]
        avg_fill_price = None
        if weighted_prices and total_shares:
            avg_fill_price = sum(price * shares for price, shares in weighted_prices) / sum(
                shares for _price, shares in weighted_prices
            )

        return BrokerExecutionSnapshotState(
            broker_name="ibkr",
            passed=True,
            fills=fills,
            fill_count=len(fills),
            total_shares=total_shares,
            cumulative_qty=cumulative_qty,
            avg_fill_price=avg_fill_price,
            reason="executions_loaded",
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


class IBKROrderSubmissionAckAggregator:
    def __init__(self, *, order_id: str) -> None:
        self.order_id = str(order_id)
        self._last_broker_status: str | None = None
        self._last_order_status: str | None = None
        self._last_raw_event: Event | None = None
        self._is_terminal = False
        self._acknowledged = False
        self._timeout = False
        self._stale = False
        self._rejected = False
        self._warning_events: list[Event] = []

    def on_event(self, event: Event) -> None:
        if self._acknowledged or self._timeout or self._stale:
            return
        if not _strict_matches_order_id(event, self.order_id):
            return

        event_type = event.get("event_type")
        if event_type == "stale":
            self._stale = True
            self._last_raw_event = event
            return

        if event_type == "timeout" and event.get("operation") == "submit_market_order":
            self._timeout = True
            self._last_raw_event = event
            return

        if event_type == "order_error":
            if _is_non_terminal_order_warning(event):
                self._warning_events.append(event)
                self._last_raw_event = self._raw_response(event)
                return
            self._last_raw_event = event
            self._last_broker_status = "error"
            self._last_order_status = "rejected"
            self._is_terminal = True
            self._rejected = True
            self._acknowledged = True
            return

        if event_type == "open_order":
            self._last_raw_event = self._raw_response(event)
            self._last_broker_status = str(event.get("status") or "Submitted")
            self._last_order_status = normalize_order_status(self._last_broker_status)
            self._is_terminal = is_terminal_order_status(self._last_order_status)
            self._acknowledged = True
            return

        if event_type == "order_status":
            self._last_raw_event = self._raw_response(event)
            self._last_broker_status = str(event.get("status"))
            self._last_order_status = normalize_order_status(self._last_broker_status)
            self._is_terminal = is_terminal_order_status(self._last_order_status)
            self._acknowledged = True

    def result(self) -> BrokerOrderResult:
        if self._timeout:
            return BrokerOrderResult(
                broker_name="ibkr",
                order_id=self.order_id,
                order_status="reconciliation_required",
                broker_status=self._last_broker_status,
                is_terminal=False,
                raw_response=self._last_raw_event,
            )
        if self._stale:
            return BrokerOrderResult(
                broker_name="ibkr",
                order_id=self.order_id,
                order_status="stale_callback_ignored",
                broker_status=self._last_broker_status,
                is_terminal=False,
                raw_response=self._last_raw_event,
            )
        if self._rejected:
            return BrokerOrderResult(
                broker_name="ibkr",
                order_id=self.order_id,
                order_status="rejected",
                broker_status="error",
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

    @property
    def acknowledged(self) -> bool:
        return self._acknowledged

    def _raw_response(self, event: Event) -> Event:
        if not self._warning_events:
            return event
        return {
            "event": event,
            "warnings": list(self._warning_events),
        }


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


def _strict_matches_generation(event: Event, generation: str | None) -> bool:
    if generation is None:
        return False
    event_generation = event.get("generation")
    if event_generation is None:
        return False
    return str(event_generation) == generation


def _strict_matches_order_id(event: Event, order_id: str | None) -> bool:
    if order_id is None:
        return False
    event_order_id = event.get("order_id")
    if event_order_id is None:
        return False
    return str(event_order_id) == order_id


def _is_non_terminal_order_warning(event: Event) -> bool:
    try:
        code = int(event.get("code"))
    except (TypeError, ValueError):
        code = None
    message = str(event.get("message", "")).lower()
    if code == 10268:
        return True
    if "etradeonly" in message and "not supported" in message:
        return True
    return False


def _optional_text(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(str(value))


def _execution_correction_key(exec_id: str) -> str:
    prefix, separator, suffix = exec_id.rpartition(".")
    if separator and suffix.isdigit():
        return prefix
    return exec_id


def _execution_snapshot_error(*, error: str) -> BrokerExecutionSnapshotState:
    return BrokerExecutionSnapshotState(
        broker_name="ibkr",
        passed=False,
        fills=(),
        fill_count=0,
        total_shares=0.0,
        cumulative_qty=None,
        avg_fill_price=None,
        reason="execution_lookup_failed",
        error=error,
    )


def _open_order_key(event: Event) -> str | None:
    perm_id = event.get("perm_id")
    if perm_id not in {None, "", 0, "0"}:
        return f"perm:{perm_id}"
    order_id = event.get("order_id")
    if order_id is None:
        return None
    return f"order:{order_id}"
