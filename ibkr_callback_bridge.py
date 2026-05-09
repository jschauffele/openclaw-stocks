from __future__ import annotations

from broker_interface import (
    BrokerAccountState,
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from fake_ibkr_callback_state_machine import (
    IBKRAccountSnapshotAggregator,
    IBKRLifecycleAggregator,
    IBKROpenOrdersSnapshotAggregator,
    IBKROrderStatusAggregator,
    IBKRPositionSnapshotAggregator,
)
from ibkr_pending_request_registry import IBKRPendingRequestRegistry


class IBKRCallbackBridge:
    def __init__(self, registry: IBKRPendingRequestRegistry | None = None) -> None:
        self.registry = registry or IBKRPendingRequestRegistry()

    def begin_lifecycle(self, *, operation: str = "connect") -> None:
        self.registry.register_lifecycle(
            operation,
            IBKRLifecycleAggregator(operation=operation),
        )

    def begin_account_snapshot(self, *, request_id: object) -> None:
        self.registry.register_request(
            request_id,
            IBKRAccountSnapshotAggregator(request_id=str(request_id)),
        )

    def begin_position_snapshot(self, *, request_id: object, symbol: str) -> None:
        self.registry.register_request(
            request_id,
            IBKRPositionSnapshotAggregator(symbol=symbol, request_id=str(request_id)),
        )

    def begin_open_orders_snapshot(self, *, request_id: object, symbol: str) -> None:
        self.registry.register_request(
            request_id,
            IBKROpenOrdersSnapshotAggregator(symbol=symbol, request_id=str(request_id)),
        )

    def begin_order_status(self, *, order_id: object) -> None:
        self.registry.register_order(
            order_id,
            IBKROrderStatusAggregator(order_id=str(order_id)),
        )

    def complete_lifecycle(self, *, operation: str = "connect") -> BrokerLifecycleResult:
        aggregator = self.registry.pop_lifecycle(operation)
        if aggregator is None:
            raise KeyError(f"No pending IBKR lifecycle operation: {operation}")
        return aggregator.result()

    def complete_account_snapshot(self, *, request_id: object) -> BrokerAccountState:
        aggregator = self.registry.pop_request(request_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR account request: {request_id}")
        return aggregator.result()

    def complete_position_snapshot(self, *, request_id: object) -> BrokerPositionState:
        aggregator = self.registry.pop_request(request_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR position request: {request_id}")
        return aggregator.result()

    def complete_open_orders_snapshot(self, *, request_id: object) -> BrokerOpenOrderState:
        aggregator = self.registry.pop_request(request_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR open orders request: {request_id}")
        return aggregator.result()

    def complete_order_status(self, *, order_id: object) -> BrokerOrderResult:
        aggregator = self.registry.pop_order(order_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR order: {order_id}")
        return aggregator.result()

    def connect_ready(
        self,
        *,
        operation: str = "connect",
        message: str = "connect_ready",
        elapsed_ms: int | None = None,
    ) -> bool:
        return self.registry.route_lifecycle_event(
            operation,
            {
                "event_type": "connect_ready",
                "message": message,
                "elapsed_ms": elapsed_ms,
            },
        )

    def connect_error(
        self,
        *,
        operation: str = "connect",
        message: str = "connect_error",
        retryable: bool = True,
        elapsed_ms: int | None = None,
    ) -> bool:
        return self.registry.route_lifecycle_event(
            operation,
            {
                "event_type": "connect_error",
                "message": message,
                "retryable": retryable,
                "elapsed_ms": elapsed_ms,
            },
        )

    def next_valid_id(self, *, order_id: object) -> bool:
        routed = self.connect_ready(message="next_valid_id")
        routed_order = self.registry.route_order_event(
            order_id,
            {"event_type": "next_valid_id", "order_id": order_id},
        )
        return routed or routed_order

    def account_value(self, *, request_id: object, buying_power: object) -> bool:
        return self.account_summary(request_id=request_id, buying_power=buying_power)

    def account_summary(self, *, request_id: object, buying_power: object) -> bool:
        if request_id is None or not self.registry.has_request(request_id):
            return False
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "account_summary",
                "request_id": request_id,
                "buying_power": buying_power,
            },
        )

    def account_summary_end(self, *, request_id: object) -> bool:
        if request_id is None or not self.registry.has_request(request_id):
            return False
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "account_summary_end",
                "request_id": request_id,
            },
        )

    def position(
        self,
        *,
        request_id: object,
        symbol: str,
        qty: object,
        side: str = "long",
    ) -> bool:
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "position",
                "request_id": request_id,
                "symbol": symbol,
                "qty": qty,
                "side": side,
            },
        )

    def position_end(self, *, request_id: object) -> bool:
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "position_end",
                "request_id": request_id,
            },
        )

    def open_order(
        self,
        *,
        request_id: object,
        order_id: object,
        symbol: str,
        side: str,
        qty: object,
        status: str,
    ) -> bool:
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "open_order",
                "request_id": request_id,
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "status": status,
            },
        )

    def open_order_end(self, *, request_id: object) -> bool:
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "open_order_end",
                "request_id": request_id,
            },
        )

    def order_status(self, *, order_id: object, status: str) -> bool:
        return self.registry.route_order_event(
            order_id,
            {
                "event_type": "order_status",
                "order_id": order_id,
                "status": status,
            },
        )
