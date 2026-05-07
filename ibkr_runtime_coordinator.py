from __future__ import annotations

import threading

from broker_interface import BrokerLifecycleResult
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_lifecycle import IBKRRuntimeThreadOwner
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_timeout_injector import IBKRTimeoutInjector


class IBKRRuntimeArbitrationCoordinator:
    def __init__(
        self,
        *,
        client=None,
        lock: threading.RLock | None = None,
        condition: threading.Condition | None = None,
        thread_owner: IBKRRuntimeThreadOwner | None = None,
        registry: IBKRPendingRequestRegistry | None = None,
        bridge: IBKRCallbackBridge | None = None,
        timeout_injector: IBKRTimeoutInjector | None = None,
    ) -> None:
        self.client = client
        self.lock = lock or threading.RLock()
        self.condition = condition or threading.Condition(self.lock)
        self.thread_owner = thread_owner or IBKRRuntimeThreadOwner(
            lock=self.lock,
            condition=self.condition,
        )
        self.registry = registry or IBKRPendingRequestRegistry()
        self.bridge = bridge or IBKRCallbackBridge(registry=self.registry)
        self.timeout_injector = timeout_injector or IBKRTimeoutInjector(
            self.registry
        )
        self.completed_result: BrokerLifecycleResult | None = None
        self.completed_by: str | None = None
        self.notification_count = 0

    def begin_connect(self) -> None:
        with self.lock:
            if self.completed_result is not None:
                raise RuntimeError("IBKR connect lifecycle already completed")
            self.bridge.begin_lifecycle(operation="connect")

    def callback_connect_ready(
        self,
        *,
        message: str = "next_valid_id",
        elapsed_ms: int | None = None,
    ) -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            if not self.bridge.connect_ready(
                message=message,
                elapsed_ms=elapsed_ms,
            ):
                return False
            self.completed_result = self.bridge.complete_lifecycle(
                operation="connect"
            )
            self.completed_by = "callback"
            self._notify_waiters()
            return True

    def timeout_connect(
        self,
        *,
        message: str = "no nextValidId callback",
        elapsed_ms: int | None = None,
    ) -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            self.completed_result = self.timeout_injector.inject_lifecycle_timeout(
                operation="connect",
                message=message,
                elapsed_ms=elapsed_ms,
            )
            self.completed_by = "timeout"
            self._notify_waiters()
            return True

    def connect_result(self) -> BrokerLifecycleResult | None:
        with self.lock:
            return self.completed_result

    def has_pending_connect(self) -> bool:
        with self.lock:
            return self.registry.has_lifecycle("connect")

    def wait_for_completion(self, timeout: float | None = None) -> bool:
        with self.condition:
            return self.condition.wait_for(
                lambda: self.completed_result is not None,
                timeout=timeout,
            )

    def _notify_waiters(self) -> None:
        self.notification_count += 1
        self.condition.notify_all()
