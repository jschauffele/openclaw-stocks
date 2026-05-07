from __future__ import annotations

import threading
import unittest
from typing import Any

from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_runtime_coordinator import IBKRRuntimeArbitrationCoordinator


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
            raise AssertionError(f"{operation} requires coordinator lock")
        self.protected_operations.append(operation)


class GuardedFakeClient:
    def __init__(self) -> None:
        self.connect_calls = 0
        self.run_calls = 0

    def connect(self, *args, **kwargs) -> None:
        self.connect_calls += 1
        raise AssertionError("runtime coordinator fake connect must not call connect")

    def run(self) -> None:
        self.run_calls += 1
        raise AssertionError("runtime coordinator fake connect must not call run")


def build_locked_coordinator() -> IBKRRuntimeArbitrationCoordinator:
    lock = threading.RLock()
    registry = LockAssertingRegistry(lock)
    return IBKRRuntimeArbitrationCoordinator(
        client=GuardedFakeClient(),
        lock=lock,
        registry=registry,
    )


class IBKRRuntimeCoordinatorTests(unittest.TestCase):
    def test_callback_wins_before_timeout(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.callback_connect_ready())
        self.assertFalse(coordinator.timeout_connect())

        result = coordinator.connect_result()
        self.assertEqual(coordinator.completed_by, "callback")
        self.assertEqual(result.passed, True)
        self.assertEqual(result.reason, "connect_ready")
        self.assertEqual(result.message, "next_valid_id")
        self.assertFalse(coordinator.has_pending_connect())

    def test_timeout_wins_before_callback(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.timeout_connect())
        self.assertFalse(coordinator.callback_connect_ready())

        result = coordinator.connect_result()
        self.assertEqual(coordinator.completed_by, "timeout")
        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_timeout")
        self.assertEqual(result.message, "no nextValidId callback")
        self.assertFalse(coordinator.has_pending_connect())

    def test_late_callback_ignored_after_timeout(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()
        coordinator.timeout_connect()
        completed_result = coordinator.connect_result()

        self.assertFalse(coordinator.callback_connect_ready())

        self.assertIs(coordinator.connect_result(), completed_result)
        self.assertEqual(coordinator.completed_by, "timeout")
        self.assertEqual(coordinator.notification_count, 1)

    def test_duplicate_callback_ignored_after_completion(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.callback_connect_ready())
        completed_result = coordinator.connect_result()
        self.assertFalse(coordinator.callback_connect_ready())

        self.assertIs(coordinator.connect_result(), completed_result)
        self.assertEqual(coordinator.completed_by, "callback")
        self.assertEqual(coordinator.notification_count, 1)

    def test_timeout_ignored_after_callback_completion(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.callback_connect_ready())
        completed_result = coordinator.connect_result()
        self.assertFalse(coordinator.timeout_connect())

        self.assertIs(coordinator.connect_result(), completed_result)
        self.assertEqual(coordinator.completed_by, "callback")
        self.assertEqual(coordinator.notification_count, 1)

    def test_waiter_notified_on_terminal_completion(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()
        previous_generation = coordinator.notification_count

        self.assertTrue(coordinator.callback_connect_ready())

        self.assertGreater(coordinator.notification_count, previous_generation)
        self.assertTrue(coordinator.wait_for_completion(timeout=0.01))

    def test_registry_is_empty_after_completion(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.callback_connect_ready())

        self.assertFalse(coordinator.has_pending_connect())

    def test_registry_bridge_timeout_and_completion_are_under_same_lock(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.callback_connect_ready())
        self.assertFalse(coordinator.has_pending_connect())

        self.assertIn("register_lifecycle", coordinator.registry.protected_operations)
        self.assertIn(
            "route_lifecycle_event",
            coordinator.registry.protected_operations,
        )
        self.assertIn("get_lifecycle", coordinator.registry.protected_operations)
        self.assertIn("pop_lifecycle", coordinator.registry.protected_operations)
        self.assertIn("has_lifecycle", coordinator.registry.protected_operations)

    def test_timeout_injection_and_completion_are_under_same_lock(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.timeout_connect())
        self.assertFalse(coordinator.has_pending_connect())

        self.assertIn("register_lifecycle", coordinator.registry.protected_operations)
        self.assertIn("pop_lifecycle", coordinator.registry.protected_operations)
        self.assertIn("has_lifecycle", coordinator.registry.protected_operations)

    def test_runtime_thread_owner_uses_coordinator_lock_boundary(self) -> None:
        coordinator = build_locked_coordinator()

        self.assertIs(coordinator.thread_owner.lock, coordinator.lock)
        self.assertIs(coordinator.thread_owner.condition, coordinator.condition)

    def test_no_real_connect_or_run_occurs(self) -> None:
        coordinator = build_locked_coordinator()

        coordinator.begin_connect()
        self.assertTrue(coordinator.callback_connect_ready())

        self.assertEqual(coordinator.client.connect_calls, 0)
        self.assertEqual(coordinator.client.run_calls, 0)


if __name__ == "__main__":
    unittest.main()
