from __future__ import annotations

from broker_interface import (
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from ibkr_pending_request_registry import IBKRPendingRequestRegistry


class IBKRTimeoutInjector:
    def __init__(self, registry: IBKRPendingRequestRegistry) -> None:
        self.registry = registry

    def inject_lifecycle_timeout(
        self,
        *,
        operation: str,
        message: str | None = None,
        elapsed_ms: int | None = None,
    ) -> BrokerLifecycleResult:
        aggregator = self.registry.pop_lifecycle(operation)
        if aggregator is None:
            raise KeyError(f"No pending IBKR lifecycle operation: {operation}")
        event = {
            "event_type": "timeout",
            "operation": operation,
            "message": message or f"{operation}_timeout",
            "elapsed_ms": elapsed_ms,
        }
        aggregator.on_event(event)
        return aggregator.result()

    def inject_snapshot_timeout(
        self,
        *,
        request_id: object,
    ) -> BrokerPositionState | BrokerOpenOrderState:
        aggregator = self.registry.pop_request(request_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR snapshot request: {request_id}")
        return aggregator.result()

    def inject_order_timeout(
        self,
        *,
        order_id: object,
        message: str | None = None,
    ) -> BrokerOrderResult:
        aggregator = self.registry.pop_order(order_id)
        if aggregator is None:
            raise KeyError(f"No pending IBKR order: {order_id}")
        event = {
            "event_type": "timeout",
            "operation": "submit_market_order",
            "message": message or "submit_market_order_timeout",
        }
        aggregator.on_event(event)
        return aggregator.result()
