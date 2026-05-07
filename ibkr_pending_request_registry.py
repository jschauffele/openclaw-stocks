from __future__ import annotations

from typing import Any


class IBKRPendingRequestRegistry:
    def __init__(self) -> None:
        self._lifecycle_aggregators: dict[str, Any] = {}
        self._request_aggregators: dict[str, Any] = {}
        self._order_aggregators: dict[str, Any] = {}

    def register_lifecycle(self, operation: str, aggregator: Any) -> None:
        self._lifecycle_aggregators[operation] = aggregator

    def get_lifecycle(self, operation: str) -> Any | None:
        return self._lifecycle_aggregators.get(operation)

    def pop_lifecycle(self, operation: str) -> Any | None:
        return self._lifecycle_aggregators.pop(operation, None)

    def register_request(self, request_id: object, aggregator: Any) -> None:
        self._request_aggregators[str(request_id)] = aggregator

    def get_request(self, request_id: object) -> Any | None:
        return self._request_aggregators.get(str(request_id))

    def pop_request(self, request_id: object) -> Any | None:
        return self._request_aggregators.pop(str(request_id), None)

    def register_order(self, order_id: object, aggregator: Any) -> None:
        self._order_aggregators[str(order_id)] = aggregator

    def get_order(self, order_id: object) -> Any | None:
        return self._order_aggregators.get(str(order_id))

    def pop_order(self, order_id: object) -> Any | None:
        return self._order_aggregators.pop(str(order_id), None)

    def route_lifecycle_event(self, operation: str, event: dict[str, object]) -> bool:
        aggregator = self.get_lifecycle(operation)
        if aggregator is None:
            return False
        aggregator.on_event(event)
        return True

    def route_request_event(self, request_id: object, event: dict[str, object]) -> bool:
        aggregator = self.get_request(request_id)
        if aggregator is None:
            return False
        aggregator.on_event(event)
        return True

    def route_order_event(self, order_id: object, event: dict[str, object]) -> bool:
        aggregator = self.get_order(order_id)
        if aggregator is None:
            return False
        aggregator.on_event(event)
        return True

    def has_lifecycle(self, operation: str) -> bool:
        return operation in self._lifecycle_aggregators

    def has_request(self, request_id: object) -> bool:
        return str(request_id) in self._request_aggregators

    def has_order(self, order_id: object) -> bool:
        return str(order_id) in self._order_aggregators
