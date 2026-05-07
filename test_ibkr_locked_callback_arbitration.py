from __future__ import annotations

import threading
import unittest
from typing import Any

from broker_interface import BrokerLifecycleResult
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_timeout_injector import IBKRTimeoutInjector


class LockAssertingRegistry(IBKRPendingRequestRegistry):
    def __init__(self, lock: threading.RLock) -> None:
        super().__init__()
        self.lock = lock
        self.protected_operations: list[str] = []

    def register_lifecycle(self, operation: str, aggregator: Any) -> None:
        self._assert_locked("register_lifecycle")
        super().register_lifecycle(operation, aggregator)

    def get_lifecycle(self, operation: str) -> Any | None:
        self._assert_locked("get_lifecycle")
        return super().get_lifecycle(operation)

    def pop_lifecycle(self, operation: str) -> Any | None:
        self._assert_locked("pop_lifecycle")
        return super().pop_lifecycle(operation)

    def route_lifecycle_event(self, operation: str, event: dict[str, object]) -> bool:
        self._assert_locked("route_lifecycle_event")
        return super().route_lifecycle_event(operation, event)

    def has_lifecycle(self, operation: str) -> bool:
        self._assert_locked("has_lifecycle")
        return super().has_lifecycle(operation)

    def _assert_locked(self, operation: str) -> None:
        is_owned = getattr(self.lock, "_is_owned", None)
        if is_owned is None or not is_owned():
            raise AssertionError(f"{operation} requires adapter-owned lock")
        self.protected_operations.append(operation)


class LockedCallbackArbitrationOwner:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.registry = LockAssertingRegistry(self.lock)
        self.bridge = IBKRCallbackBridge(registry=self.registry)
        self.timeout_injector = IBKRTimeoutInjector(self.registry)
        self.completed_result: BrokerLifecycleResult | None = None
        self.completed_by: str | None = None
        self.notification_count = 0

    def begin_connect(self) -> None:
        with self.lock:
            self.bridge.begin_lifecycle(operation="connect")

    def callback_ready(self) -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            if not self.bridge.connect_ready(message="next_valid_id"):
                return False
            self.completed_result = self.bridge.complete_lifecycle(
                operation="connect"
            )
            self.completed_by = "callback"
            self._notify_waiters()
            return True

    def timeout(self) -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            self.completed_result = self.timeout_injector.inject_lifecycle_timeout(
                operation="connect",
                message="no nextValidId callback",
                elapsed_ms=5000,
            )
            self.completed_by = "timeout"
            self._notify_waiters()
            return True

    def has_pending_connect(self) -> bool:
        with self.lock:
            return self.registry.has_lifecycle("connect")

    def fake_waiter_generation(self) -> int:
        with self.lock:
            return self.notification_count

    def fake_waiter_was_woken(self, *, previous_generation: int) -> bool:
        with self.lock:
            return self.notification_count > previous_generation

    def _notify_waiters(self) -> None:
        self.notification_count += 1
        self.condition.notify_all()


class IBKRLockedCallbackArbitrationTests(unittest.TestCase):
    def test_callback_wins_before_timeout(self) -> None:
        owner = LockedCallbackArbitrationOwner()
        owner.begin_connect()

        self.assertTrue(owner.callback_ready())
        self.assertFalse(owner.timeout())

        self.assertEqual(owner.completed_by, "callback")
        self.assertEqual(owner.completed_result.passed, True)
        self.assertEqual(owner.completed_result.reason, "connect_ready")
        self.assertEqual(owner.completed_result.message, "next_valid_id")
        self.assertFalse(owner.has_pending_connect())

    def test_timeout_wins_before_callback(self) -> None:
        owner = LockedCallbackArbitrationOwner()
        owner.begin_connect()

        self.assertTrue(owner.timeout())
        self.assertFalse(owner.callback_ready())

        self.assertEqual(owner.completed_by, "timeout")
        self.assertEqual(owner.completed_result.passed, False)
        self.assertEqual(owner.completed_result.reason, "connect_timeout")
        self.assertEqual(owner.completed_result.message, "no nextValidId callback")
        self.assertFalse(owner.has_pending_connect())

    def test_late_callback_ignored_after_timeout(self) -> None:
        owner = LockedCallbackArbitrationOwner()
        owner.begin_connect()
        owner.timeout()
        completed_result = owner.completed_result

        self.assertFalse(owner.callback_ready())

        self.assertIs(owner.completed_result, completed_result)
        self.assertEqual(owner.completed_by, "timeout")
        self.assertEqual(owner.notification_count, 1)

    def test_duplicate_callback_ignored_after_completion(self) -> None:
        owner = LockedCallbackArbitrationOwner()
        owner.begin_connect()

        self.assertTrue(owner.callback_ready())
        completed_result = owner.completed_result
        self.assertFalse(owner.callback_ready())

        self.assertIs(owner.completed_result, completed_result)
        self.assertEqual(owner.completed_by, "callback")
        self.assertEqual(owner.notification_count, 1)

    def test_timeout_ignored_after_callback_completion(self) -> None:
        owner = LockedCallbackArbitrationOwner()
        owner.begin_connect()

        self.assertTrue(owner.callback_ready())
        completed_result = owner.completed_result
        self.assertFalse(owner.timeout())

        self.assertIs(owner.completed_result, completed_result)
        self.assertEqual(owner.completed_by, "callback")
        self.assertEqual(owner.notification_count, 1)

    def test_waiter_notified_on_terminal_completion(self) -> None:
        owner = LockedCallbackArbitrationOwner()
        owner.begin_connect()
        waiter_generation = owner.fake_waiter_generation()

        self.assertTrue(owner.callback_ready())

        self.assertTrue(
            owner.fake_waiter_was_woken(previous_generation=waiter_generation)
        )
        self.assertEqual(owner.notification_count, 1)

    def test_registry_pop_and_completion_are_protected_by_same_lock(self) -> None:
        owner = LockedCallbackArbitrationOwner()
        owner.begin_connect()

        self.assertTrue(owner.callback_ready())
        self.assertFalse(owner.has_pending_connect())

        self.assertIn("register_lifecycle", owner.registry.protected_operations)
        self.assertIn("route_lifecycle_event", owner.registry.protected_operations)
        self.assertIn("get_lifecycle", owner.registry.protected_operations)
        self.assertIn("pop_lifecycle", owner.registry.protected_operations)
        self.assertIn("has_lifecycle", owner.registry.protected_operations)


if __name__ == "__main__":
    unittest.main()
