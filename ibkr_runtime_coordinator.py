from __future__ import annotations

import threading
from math import isfinite

from broker_interface import BrokerLifecycleResult
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_lifecycle import IBKRRuntimeThreadOwner
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_timeout_injector import IBKRTimeoutInjector


class IBKRRuntimeArbitrationCoordinator:
    LOCALHOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
    PAPER_PORTS = frozenset({7497, 4002})

    def __init__(
        self,
        *,
        client=None,
        enabled: bool = False,
        lock: threading.RLock | None = None,
        condition: threading.Condition | None = None,
        thread_owner: IBKRRuntimeThreadOwner | None = None,
        registry: IBKRPendingRequestRegistry | None = None,
        bridge: IBKRCallbackBridge | None = None,
        timeout_injector: IBKRTimeoutInjector | None = None,
    ) -> None:
        self.client = client
        self.enabled = enabled
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
        self.connect_state = "disconnected"
        self.shutdown_state = "active"
        self._connect_started = False

    def begin_connect(self) -> None:
        with self.lock:
            if self.completed_result is not None:
                raise RuntimeError("IBKR connect lifecycle already completed")
            self.bridge.begin_lifecycle(operation="connect")

    def connect(
        self,
        *,
        host: str,
        port: int,
        client_id: int,
        timeout: float,
    ) -> None:
        self._validate_connect_guardrails(host=host, port=port, timeout=timeout)
        with self.lock:
            if self._connect_started:
                raise RuntimeError(f"IBKR connect already {self.connect_state}")
            if self.client is None:
                raise RuntimeError("IBKR connect requires a client")
            self._connect_started = True
            self.connect_state = "connecting"
            self.shutdown_state = "active"
            self.bridge.begin_lifecycle(operation="connect")
            run_target = self.client.run

        try:
            self.thread_owner.start_thread(run_target)
        except Exception as exc:
            self._fail_connect_lifecycle(
                reason="runtime_thread_start_failed",
                message=str(exc),
                raw_error=exc,
            )
            with self.lock:
                self.connect_state = "disconnected"
                self.shutdown_state = "complete"
                self._notify_waiters()
            raise

        try:
            self.client.connect(host, port, client_id)
        except Exception as exc:
            self._fail_connect_lifecycle(
                reason="connect_exception",
                message=str(exc),
                raw_error=exc,
            )
            self.disconnect(timeout=timeout)
            raise

    def callback_connect_ready(
        self,
        *,
        message: str = "next_valid_id",
        elapsed_ms: int | None = None,
    ) -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            if self.shutdown_state != "active":
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
            self.connect_state = "connected"
            self._notify_waiters()
            return True

    def callback_connect_error(
        self,
        *,
        message: str = "connect_error",
        retryable: bool = True,
        elapsed_ms: int | None = None,
    ) -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            if not self.bridge.connect_error(
                message=message,
                retryable=retryable,
                elapsed_ms=elapsed_ms,
            ):
                return False
            self.completed_result = self.bridge.complete_lifecycle(
                operation="connect"
            )
            self.completed_by = "callback_error"
            self.connect_state = "disconnected"
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
            should_cleanup = self.connect_state == "connecting"
            self.completed_result = self.timeout_injector.inject_lifecycle_timeout(
                operation="connect",
                message=message,
                elapsed_ms=elapsed_ms,
            )
            self.completed_by = "timeout"
            self._notify_waiters()
        if should_cleanup:
            self.disconnect(timeout=1.0)
        return True

    def disconnect(self, *, timeout: float | None = None) -> bool:
        with self.lock:
            if self.shutdown_state == "complete":
                return True
            should_disconnect = self.client is not None and self.connect_state in {
                "connecting",
                "connected",
            }
            should_join = self.thread_owner.thread is not None
            self.shutdown_state = "stopping"

        if should_disconnect:
            try:
                self.client.disconnect()
            except Exception:
                pass

        joined = True
        if should_join:
            joined = self.thread_owner.join_thread(timeout=timeout)

        with self.lock:
            if joined:
                self.connect_state = "disconnected"
                self.shutdown_state = "complete"
                self._notify_waiters()
            return joined

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

    def _validate_connect_guardrails(
        self,
        *,
        host: str,
        port: int,
        timeout: float | None,
    ) -> None:
        if not self.enabled:
            raise RuntimeError("IBKR coordinator connect requires enabled=True")
        if host not in self.LOCALHOSTS:
            raise ValueError("IBKR coordinator connect is restricted to localhost")
        if port not in self.PAPER_PORTS:
            raise ValueError("IBKR coordinator connect is restricted to paper ports")
        if timeout is None or not isfinite(timeout) or timeout <= 0:
            raise ValueError("IBKR coordinator connect requires a finite timeout")

    def _fail_connect_lifecycle(
        self,
        *,
        reason: str,
        message: str,
        raw_error: object,
    ) -> None:
        with self.lock:
            if self.completed_result is not None:
                return
            self.registry.pop_lifecycle("connect")
            self.completed_result = BrokerLifecycleResult(
                broker_name="ibkr",
                operation="connect",
                passed=False,
                reason=reason,
                message=message,
                connected=False,
                retryable=True,
                elapsed_ms=0,
                raw_error=raw_error,
            )
            self.completed_by = reason
            self.shutdown_state = "stopping"
            self._notify_waiters()
