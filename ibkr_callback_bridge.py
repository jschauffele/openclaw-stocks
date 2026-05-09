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
    def __init__(
        self,
        registry: IBKRPendingRequestRegistry | None = None,
        *,
        request_coordinator=None,
    ) -> None:
        self.request_coordinator = request_coordinator
        if registry is None and request_coordinator is not None:
            registry = request_coordinator.registry
        self.registry = registry or IBKRPendingRequestRegistry()
        self._open_orders_generation = 0
        self._active_open_orders_generation: int | None = None
        self._latest_completed_open_orders_generation: int | None = None
        self._completed_open_orders_results: dict[int, BrokerOpenOrderState] = {}

    def begin_lifecycle(self, *, operation: str = "connect") -> None:
        self.registry.register_lifecycle(
            operation,
            IBKRLifecycleAggregator(operation=operation),
        )

    def begin_account_snapshot(self, *, request_id: object) -> None:
        aggregator = IBKRAccountSnapshotAggregator(request_id=str(request_id))
        if self.request_coordinator is not None:
            self.request_coordinator.register_request(request_id, aggregator)
            return
        self.registry.register_request(request_id, aggregator)

    def begin_position_snapshot(self, *, request_id: object, symbol: str) -> None:
        aggregator = IBKRPositionSnapshotAggregator(
            symbol=symbol,
            request_id=str(request_id),
        )
        if self.request_coordinator is not None:
            self.request_coordinator.register_request(request_id, aggregator)
            return
        self.registry.register_request(request_id, aggregator)

    def begin_open_orders_snapshot(
        self,
        *,
        symbol: str,
        request_id: object | None = None,
    ) -> int:
        if self._active_open_orders_generation is not None:
            raise RuntimeError("IBKR open-order snapshot already active")
        self._open_orders_generation += 1
        generation = self._open_orders_generation
        self._active_open_orders_generation = generation
        self.registry.register_request(
            generation,
            IBKROpenOrdersSnapshotAggregator(symbol=symbol, generation=generation),
        )
        return generation

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
        if self.request_coordinator is not None:
            result = self.request_coordinator.result(request_id)
            if result is None:
                raise KeyError(f"No completed IBKR account request: {request_id}")
            if isinstance(result, Exception):
                raise result
            return result
        aggregator = self.registry.pop_request(request_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR account request: {request_id}")
        return aggregator.result()

    def complete_position_snapshot(self, *, request_id: object) -> BrokerPositionState:
        if self.request_coordinator is not None:
            result = self.request_coordinator.result(request_id)
            if result is None:
                raise KeyError(f"No completed IBKR position request: {request_id}")
            if isinstance(result, Exception):
                raise result
            return result
        aggregator = self.registry.pop_request(request_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR position request: {request_id}")
        return aggregator.result()

    def complete_open_orders_snapshot(
        self,
        *,
        generation: object | None = None,
        request_id: object | None = None,
    ) -> BrokerOpenOrderState:
        if generation is None:
            generation = self._latest_completed_open_orders_generation
        if generation is None:
            raise KeyError("No completed IBKR open-order snapshot")
        generation_key = int(generation)
        result = self._completed_open_orders_results.get(generation_key)
        if result is None:
            raise KeyError(f"No completed IBKR open-order snapshot: {generation}")
        return result

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

    def account_summary(
        self,
        *,
        request_id: object,
        buying_power: object | None = None,
        account: object | None = None,
        tag: object | None = None,
        value: object | None = None,
        currency: object | None = None,
    ) -> bool:
        if request_id is None or not self.registry.has_request(request_id):
            return False
        if buying_power is None:
            if tag != "BuyingPower":
                return False
            buying_power = value
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "account_summary",
                "request_id": request_id,
                "account": account,
                "tag": tag,
                "value": value,
                "currency": currency,
                "buying_power": buying_power,
            },
        )

    def account_summary_end(self, *, request_id: object) -> bool:
        if request_id is None or not self.registry.has_request(request_id):
            return False
        routed = self.registry.route_request_event(
            request_id,
            {
                "event_type": "account_summary_end",
                "request_id": request_id,
            },
        )
        if routed and self.request_coordinator is not None:
            return self.request_coordinator.complete_from_callback(request_id)
        return routed

    def position_multi(
        self,
        *,
        request_id: object,
        symbol: str,
        qty: object,
        side: str = "long",
        account: object | None = None,
        model_code: object | None = None,
        avg_cost: object | None = None,
    ) -> bool:
        if request_id is None or not self.registry.has_request(request_id):
            return False
        return self.registry.route_request_event(
            request_id,
            {
                "event_type": "position_multi",
                "request_id": request_id,
                "account": account,
                "model_code": model_code,
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "avg_cost": avg_cost,
            },
        )

    def position_multi_end(self, *, request_id: object) -> bool:
        if request_id is None or not self.registry.has_request(request_id):
            return False
        routed = self.registry.route_request_event(
            request_id,
            {
                "event_type": "position_multi_end",
                "request_id": request_id,
            },
        )
        if routed and self.request_coordinator is not None:
            return self.request_coordinator.complete_from_callback(request_id)
        return routed

    def position(
        self,
        *,
        request_id: object,
        symbol: str,
        qty: object,
        side: str = "long",
    ) -> bool:
        return self.position_multi(
            request_id=request_id,
            symbol=symbol,
            qty=qty,
            side=side,
        )

    def position_end(self, *, request_id: object) -> bool:
        return self.position_multi_end(request_id=request_id)

    def open_order(
        self,
        *,
        order_id: object,
        symbol: str,
        side: str,
        qty: object,
        status: str,
        perm_id: object | None = None,
        request_id: object | None = None,
    ) -> bool:
        generation = self._active_open_orders_generation
        if generation is None:
            return False
        return self.registry.route_request_event(
            generation,
            {
                "event_type": "open_order",
                "generation": generation,
                "order_id": order_id,
                "perm_id": perm_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "status": status,
            },
        )

    def open_order_status_update(
        self,
        *,
        order_id: object,
        status: str,
        perm_id: object | None = None,
    ) -> bool:
        generation = self._active_open_orders_generation
        if generation is None:
            return False
        return self.registry.route_request_event(
            generation,
            {
                "event_type": "order_status",
                "generation": generation,
                "order_id": order_id,
                "perm_id": perm_id,
                "status": status,
            },
        )

    def open_order_end(self, *, request_id: object | None = None) -> bool:
        generation = self._active_open_orders_generation
        if generation is None:
            return False
        routed = self.registry.route_request_event(
            generation,
            {
                "event_type": "open_order_end",
                "generation": generation,
            },
        )
        if not routed:
            return False
        aggregator = self.registry.pop_request(generation)
        if aggregator is None:
            return False
        self._completed_open_orders_results[generation] = aggregator.result()
        self._latest_completed_open_orders_generation = generation
        self._active_open_orders_generation = None
        return True

    def timeout_open_orders_snapshot(self) -> BrokerOpenOrderState:
        generation = self._active_open_orders_generation
        if generation is None:
            raise KeyError("No active IBKR open-order snapshot")
        aggregator = self.registry.pop_request(generation)
        if aggregator is None:
            raise KeyError(f"No pending IBKR open-order snapshot: {generation}")
        result = aggregator.result()
        self._completed_open_orders_results[generation] = result
        self._latest_completed_open_orders_generation = generation
        self._active_open_orders_generation = None
        return result

    def order_status(self, *, order_id: object, status: str) -> bool:
        return self.registry.route_order_event(
            order_id,
            {
                "event_type": "order_status",
                "order_id": order_id,
                "status": status,
            },
        )
