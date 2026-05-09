from __future__ import annotations

import threading
from typing import Any

from ibkr_pending_request_registry import IBKRPendingRequestRegistry


class IBKRRequestCoordinator:
    def __init__(
        self,
        *,
        registry: IBKRPendingRequestRegistry | None = None,
        lock: threading.RLock | None = None,
        condition: threading.Condition | None = None,
    ) -> None:
        self.registry = registry or IBKRPendingRequestRegistry()
        self.lock = lock or threading.RLock()
        self.condition = condition or threading.Condition(self.lock)
        self._terminal_results: dict[str, Any] = {}
        self._completed_by: dict[str, str] = {}
        self.notification_count = 0

    def register_request(self, request_id: object, aggregator: Any) -> None:
        request_key = self._request_key(request_id)
        with self.lock:
            if self.registry.has_request(request_id):
                raise RuntimeError(f"IBKR request already pending: {request_key}")
            if request_key in self._terminal_results:
                raise RuntimeError(f"IBKR request already completed: {request_key}")
            self.registry.register_request(request_id, aggregator)

    def route_callback(self, request_id: object, event: dict[str, object]) -> bool:
        with self.lock:
            if self._is_terminal(request_id):
                return False
            aggregator = self.registry.get_request(request_id)
            if aggregator is None:
                return False
            aggregator.on_event(event)
            return True

    def complete_from_callback(self, request_id: object) -> bool:
        with self.lock:
            if self._is_terminal(request_id):
                return False
            aggregator = self.registry.pop_request(request_id)
            if aggregator is None:
                return False
            self._complete_locked(
                request_id,
                result=aggregator.result(),
                completed_by="callback",
            )
            return True

    def timeout_request(self, request_id: object) -> bool:
        with self.lock:
            if self._is_terminal(request_id):
                return False
            aggregator = self.registry.pop_request(request_id)
            if aggregator is None:
                return False
            self._complete_locked(
                request_id,
                result=aggregator.result(),
                completed_by="timeout",
            )
            return True

    def wait_for_completion(
        self,
        request_id: object,
        timeout: float | None = None,
    ) -> bool:
        with self.condition:
            return self.condition.wait_for(
                lambda: self._is_terminal(request_id),
                timeout=timeout,
            )

    def result(self, request_id: object) -> Any | None:
        with self.lock:
            return self._terminal_results.get(self._request_key(request_id))

    def completed_by(self, request_id: object) -> str | None:
        with self.lock:
            return self._completed_by.get(self._request_key(request_id))

    def has_pending_request(self, request_id: object) -> bool:
        with self.lock:
            return self.registry.has_request(request_id)

    def _complete_locked(
        self,
        request_id: object,
        *,
        result: Any,
        completed_by: str,
    ) -> None:
        request_key = self._request_key(request_id)
        self._terminal_results[request_key] = result
        self._completed_by[request_key] = completed_by
        self.notification_count += 1
        self.condition.notify_all()

    def _is_terminal(self, request_id: object) -> bool:
        return self._request_key(request_id) in self._terminal_results

    def _request_key(self, request_id: object) -> str:
        return str(request_id)
