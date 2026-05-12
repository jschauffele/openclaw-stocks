from __future__ import annotations

import threading

from broker_interface import (
    BrokerAccountState,
    BrokerExecutionSnapshotState,
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from fake_ibkr_callback_state_machine import (
    IBKRAccountSnapshotAggregator,
    IBKRExecutionSnapshotAggregator,
    IBKRLifecycleAggregator,
    IBKROpenOrdersSnapshotAggregator,
    IBKROrderSubmissionAckAggregator,
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
        self._position_generation = 0
        self._active_position_generation: int | None = None
        self._active_position_request_id: str | None = None
        self._latest_completed_position_generation: int | None = None
        self._completed_position_results: dict[str, BrokerPositionState] = {}
        self._position_generation_keys: dict[int, str] = {}
        self._position_lock = threading.RLock()
        self._open_orders_generation = 0
        self._active_open_orders_generation: int | None = None
        self._latest_completed_open_orders_generation: int | None = None
        self._completed_open_orders_results: dict[int, BrokerOpenOrderState] = {}
        self._open_orders_lock = threading.RLock()
        self._execution_generation = 0
        self._active_execution_generation: int | None = None
        self._latest_completed_execution_generation: int | None = None
        self._completed_execution_results: dict[int, BrokerExecutionSnapshotState] = {}
        self._execution_lock = threading.RLock()
        self._latest_next_valid_id: int | None = None

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

    def begin_position_snapshot(self, *, request_id: object, symbol: str) -> int:
        with self._position_lock:
            if self._active_position_generation is not None:
                raise RuntimeError("IBKR position snapshot already active")
            self._position_generation += 1
            generation = self._position_generation
            request_key = str(request_id)
            aggregator = IBKRPositionSnapshotAggregator(
                symbol=symbol,
                request_id=request_key,
                generation=generation,
            )
            if self.request_coordinator is not None:
                self.request_coordinator.register_request(request_id, aggregator)
            else:
                self.registry.register_request(request_id, aggregator)
            self._active_position_generation = generation
            self._active_position_request_id = request_key
            self._position_generation_keys[generation] = request_key
            return generation

    def begin_open_orders_snapshot(
        self,
        *,
        symbol: str,
        request_id: object | None = None,
    ) -> int:
        with self._open_orders_lock:
            if self._active_open_orders_generation is not None:
                raise RuntimeError("IBKR open-order snapshot already active")
            self._open_orders_generation += 1
            generation = self._open_orders_generation
            aggregator = IBKROpenOrdersSnapshotAggregator(
                symbol=symbol,
                generation=generation,
            )
            if self.request_coordinator is not None:
                self.request_coordinator.register_request(generation, aggregator)
            else:
                self.registry.register_request(generation, aggregator)
            self._active_open_orders_generation = generation
            return generation

    def begin_execution_snapshot(
        self,
        *,
        request_id: object | None = None,
        symbol: str | None = None,
    ) -> int:
        with self._execution_lock:
            if self._active_execution_generation is not None:
                raise RuntimeError("IBKR execution snapshot already active")
            if request_id is None:
                self._execution_generation += 1
                generation = self._execution_generation
            else:
                generation = int(request_id)
                self._execution_generation = max(self._execution_generation, generation)
            aggregator = IBKRExecutionSnapshotAggregator(
                generation=generation,
                symbol=symbol,
            )
            if self.request_coordinator is not None:
                self.request_coordinator.register_request(generation, aggregator)
            else:
                self.registry.register_request(generation, aggregator)
            self._active_execution_generation = generation
            return generation

    def begin_order_status(self, *, order_id: object) -> None:
        self.registry.register_order(
            order_id,
            IBKROrderStatusAggregator(order_id=str(order_id)),
        )

    def begin_order_submission(self, *, order_id: object) -> None:
        aggregator = IBKROrderSubmissionAckAggregator(order_id=str(order_id))
        if self.request_coordinator is not None:
            self.request_coordinator.register_request(order_id, aggregator)
            return
        self.registry.register_request(order_id, aggregator)

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

    def complete_position_snapshot(
        self,
        *,
        request_id: object | None = None,
        generation: object | None = None,
    ) -> BrokerPositionState:
        request_key = self._position_result_key(
            request_id=request_id,
            generation=generation,
        )
        if request_key is None:
            raise KeyError("No completed IBKR position snapshot")
        result = self._completed_position_results.get(request_key)
        if result is None:
            raise KeyError(f"No completed IBKR position snapshot: {request_key}")
        return result

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

    def complete_execution_snapshot(
        self,
        *,
        generation: object | None = None,
        request_id: object | None = None,
    ) -> BrokerExecutionSnapshotState:
        if generation is None:
            generation = request_id
        if generation is None:
            generation = self._latest_completed_execution_generation
        if generation is None:
            raise KeyError("No completed IBKR execution snapshot")
        generation_key = int(generation)
        result = self._completed_execution_results.get(generation_key)
        if result is None:
            raise KeyError(f"No completed IBKR execution snapshot: {generation}")
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
        try:
            self._latest_next_valid_id = int(order_id)
        except (TypeError, ValueError):
            pass
        routed = self.connect_ready(message="next_valid_id")
        routed_order = self.registry.route_order_event(
            order_id,
            {"event_type": "next_valid_id", "order_id": order_id},
        )
        return routed or routed_order

    @property
    def latest_next_valid_id(self) -> int | None:
        return self._latest_next_valid_id

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
        with self._position_lock:
            generation = self._active_position_generation
            if (
                request_id is None
                or generation is None
                or self._active_position_request_id != str(request_id)
                or not self.registry.has_request(request_id)
            ):
                return False
            event = {
                "event_type": "position_multi",
                "generation": generation,
                "request_id": request_id,
                "account": account,
                "model_code": model_code,
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "avg_cost": avg_cost,
            }
            if self.request_coordinator is not None:
                return self.request_coordinator.route_callback(request_id, event)
            return self.registry.route_request_event(request_id, event)

    def position_multi_end(self, *, request_id: object) -> bool:
        with self._position_lock:
            generation = self._active_position_generation
            if (
                request_id is None
                or generation is None
                or self._active_position_request_id != str(request_id)
                or not self.registry.has_request(request_id)
            ):
                return False
            event = {
                "event_type": "position_multi_end",
                "generation": generation,
                "request_id": request_id,
            }
            if self.request_coordinator is not None:
                routed = self.request_coordinator.route_callback(request_id, event)
                if not routed:
                    return False
                completed = self.request_coordinator.complete_from_callback(request_id)
                if not completed:
                    return False
                result = self.request_coordinator.result(request_id)
            else:
                routed = self.registry.route_request_event(request_id, event)
                if not routed:
                    return False
                aggregator = self.registry.pop_request(request_id)
                if aggregator is None:
                    return False
                result = aggregator.result()
            self._store_completed_position_result(
                generation=generation,
                request_id=request_id,
                result=result,
            )
            return True

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

    def timeout_position_snapshot(self) -> BrokerPositionState:
        with self._position_lock:
            generation = self._active_position_generation
            request_id = self._active_position_request_id
            if generation is None or request_id is None:
                raise KeyError("No active IBKR position snapshot")
            if self.request_coordinator is not None:
                timed_out = self.request_coordinator.timeout_request(request_id)
                if not timed_out:
                    raise KeyError(f"No pending IBKR position snapshot: {request_id}")
                result = self.request_coordinator.result(request_id)
            else:
                aggregator = self.registry.pop_request(request_id)
                if aggregator is None:
                    raise KeyError(f"No pending IBKR position snapshot: {request_id}")
                result = aggregator.result()
            self._store_completed_position_result(
                generation=generation,
                request_id=request_id,
                result=result,
            )
            return result

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
        with self._open_orders_lock:
            generation = self._active_open_orders_generation
            routed_snapshot = False
            routed_submission = self._route_order_submission_event(
                order_id,
                {
                    "event_type": "open_order",
                    "order_id": order_id,
                    "perm_id": perm_id,
                    "symbol": symbol,
                    "side": side,
                    "qty": qty,
                    "status": status,
                },
            )
            if generation is None:
                return routed_submission
            event = {
                "event_type": "open_order",
                "generation": generation,
                "order_id": order_id,
                "perm_id": perm_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "status": status,
            }
            if self.request_coordinator is not None:
                routed_snapshot = self.request_coordinator.route_callback(
                    generation,
                    event,
                )
            else:
                routed_snapshot = self.registry.route_request_event(generation, event)
            return routed_snapshot or routed_submission

    def open_order_status_update(
        self,
        *,
        order_id: object,
        status: str,
        perm_id: object | None = None,
    ) -> bool:
        with self._open_orders_lock:
            generation = self._active_open_orders_generation
            routed_snapshot = False
            routed_submission = self._route_order_submission_event(
                order_id,
                {
                    "event_type": "order_status",
                    "order_id": order_id,
                    "perm_id": perm_id,
                    "status": status,
                },
            )
            if generation is None:
                return routed_submission
            event = {
                "event_type": "order_status",
                "generation": generation,
                "order_id": order_id,
                "perm_id": perm_id,
                "status": status,
            }
            if self.request_coordinator is not None:
                routed_snapshot = self.request_coordinator.route_callback(
                    generation,
                    event,
                )
            else:
                routed_snapshot = self.registry.route_request_event(generation, event)
            return routed_snapshot or routed_submission

    def open_order_end(self, *, request_id: object | None = None) -> bool:
        with self._open_orders_lock:
            generation = self._active_open_orders_generation
            if generation is None:
                return False
            event = {
                "event_type": "open_order_end",
                "generation": generation,
            }
            if self.request_coordinator is not None:
                routed = self.request_coordinator.route_callback(generation, event)
                if not routed:
                    return False
                completed = self.request_coordinator.complete_from_callback(generation)
                if not completed:
                    return False
                result = self.request_coordinator.result(generation)
            else:
                routed = self.registry.route_request_event(generation, event)
                if not routed:
                    return False
                aggregator = self.registry.pop_request(generation)
                if aggregator is None:
                    return False
                result = aggregator.result()
            self._completed_open_orders_results[generation] = result
            self._latest_completed_open_orders_generation = generation
            self._active_open_orders_generation = None
            return True

    def timeout_open_orders_snapshot(self) -> BrokerOpenOrderState:
        with self._open_orders_lock:
            generation = self._active_open_orders_generation
            if generation is None:
                raise KeyError("No active IBKR open-order snapshot")
            if self.request_coordinator is not None:
                timed_out = self.request_coordinator.timeout_request(generation)
                if not timed_out:
                    raise KeyError(f"No pending IBKR open-order snapshot: {generation}")
                result = self.request_coordinator.result(generation)
            else:
                aggregator = self.registry.pop_request(generation)
                if aggregator is None:
                    raise KeyError(f"No pending IBKR open-order snapshot: {generation}")
                result = aggregator.result()
            self._completed_open_orders_results[generation] = result
            self._latest_completed_open_orders_generation = generation
            self._active_open_orders_generation = None
            return result

    def exec_details(
        self,
        *,
        request_id: object,
        order_id: object | None = None,
        client_id: object | None = None,
        perm_id: object | None = None,
        symbol: str = "",
        side: str = "",
        shares: object | None = None,
        cumulative_qty: object | None = None,
        avg_price: object | None = None,
        price: object | None = None,
        time: object | None = None,
        exec_id: object | None = None,
        raw_execution: object | None = None,
    ) -> bool:
        with self._execution_lock:
            generation = self._active_execution_generation
            if generation is None or str(request_id) != str(generation):
                return False
            event = {
                "event_type": "exec_details",
                "generation": generation,
                "request_id": request_id,
                "order_id": order_id,
                "client_id": client_id,
                "perm_id": perm_id,
                "symbol": symbol,
                "side": side,
                "shares": shares,
                "cumulative_qty": cumulative_qty,
                "avg_price": avg_price,
                "price": price,
                "time": time,
                "exec_id": exec_id,
                "raw_execution": raw_execution,
            }
            if self.request_coordinator is not None:
                return self.request_coordinator.route_callback(generation, event)
            return self.registry.route_request_event(generation, event)

    def exec_details_end(self, *, request_id: object) -> bool:
        with self._execution_lock:
            generation = self._active_execution_generation
            if generation is None or str(request_id) != str(generation):
                return False
            event = {
                "event_type": "exec_details_end",
                "generation": generation,
                "request_id": request_id,
            }
            if self.request_coordinator is not None:
                routed = self.request_coordinator.route_callback(generation, event)
                if not routed:
                    return False
                completed = self.request_coordinator.complete_from_callback(generation)
                if not completed:
                    return False
                result = self.request_coordinator.result(generation)
            else:
                routed = self.registry.route_request_event(generation, event)
                if not routed:
                    return False
                aggregator = self.registry.pop_request(generation)
                if aggregator is None:
                    return False
                result = aggregator.result()
            self._completed_execution_results[generation] = result
            self._latest_completed_execution_generation = generation
            self._active_execution_generation = None
            return True

    def timeout_execution_snapshot(self) -> BrokerExecutionSnapshotState:
        with self._execution_lock:
            generation = self._active_execution_generation
            if generation is None:
                raise KeyError("No active IBKR execution snapshot")
            if self.request_coordinator is not None:
                timed_out = self.request_coordinator.timeout_request(generation)
                if not timed_out:
                    raise KeyError(f"No pending IBKR execution snapshot: {generation}")
                result = self.request_coordinator.result(generation)
            else:
                aggregator = self.registry.pop_request(generation)
                if aggregator is None:
                    raise KeyError(f"No pending IBKR execution snapshot: {generation}")
                result = aggregator.result()
            self._completed_execution_results[generation] = result
            self._latest_completed_execution_generation = generation
            self._active_execution_generation = None
            return result

    def order_status(self, *, order_id: object, status: str) -> bool:
        routed_submission = self._route_order_submission_event(
            order_id,
            {
                "event_type": "order_status",
                "order_id": order_id,
                "status": status,
            },
        )
        routed_order = self.registry.route_order_event(
            order_id,
            {
                "event_type": "order_status",
                "order_id": order_id,
                "status": status,
            },
        )
        return routed_submission or routed_order

    def order_error(
        self,
        *,
        order_id: object,
        code: object,
        message: str,
        advanced_order_reject_json: object | None = None,
    ) -> bool:
        return self._route_order_submission_event(
            order_id,
            {
                "event_type": "order_error",
                "order_id": order_id,
                "code": code,
                "message": message,
                "advanced_order_reject_json": advanced_order_reject_json,
            },
        )

    def timeout_order_submission(self, *, order_id: object) -> BrokerOrderResult:
        event = {
            "event_type": "timeout",
            "operation": "submit_market_order",
            "order_id": order_id,
        }
        if self.request_coordinator is not None:
            routed = self.request_coordinator.route_callback(order_id, event)
            if not routed:
                raise KeyError(f"No pending IBKR order submission: {order_id}")
            timed_out = self.request_coordinator.timeout_request(order_id)
            if not timed_out:
                raise KeyError(f"No pending IBKR order submission: {order_id}")
            result = self.request_coordinator.result(order_id)
            if isinstance(result, Exception):
                raise result
            return result
        aggregator = self.registry.pop_request(order_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR order submission: {order_id}")
        aggregator.on_event(event)
        return aggregator.result()

    def stale_order_submission(self, *, order_id: object) -> bool:
        return False

    def _store_completed_position_result(
        self,
        *,
        generation: int,
        request_id: object,
        result: BrokerPositionState,
    ) -> None:
        request_key = str(request_id)
        self._completed_position_results[request_key] = result
        self._position_generation_keys[generation] = request_key
        self._latest_completed_position_generation = generation
        self._active_position_generation = None
        self._active_position_request_id = None

    def _position_result_key(
        self,
        *,
        request_id: object | None,
        generation: object | None,
    ) -> str | None:
        if request_id is not None:
            return str(request_id)
        if generation is None:
            generation = self._latest_completed_position_generation
        if generation is None:
            return None
        return self._position_generation_keys.get(int(generation))

    def _route_order_submission_event(
        self,
        order_id: object,
        event: dict[str, object],
    ) -> bool:
        if order_id is None:
            return False
        if self.request_coordinator is not None:
            routed = self.request_coordinator.route_callback(order_id, event)
            if not routed:
                return False
            aggregator = self.registry.get_request(order_id)
            if getattr(aggregator, "acknowledged", False):
                return self.request_coordinator.complete_from_callback(order_id)
            return True
        aggregator = self.registry.get_request(order_id)
        if aggregator is None:
            return False
        aggregator.on_event(event)
        return True
