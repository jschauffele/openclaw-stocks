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


def build_connect_coordinator():
    lock = threading.RLock()
    registry = LockAssertingRegistry(lock)
    client = ControlledFakeRuntimeClient(lock=lock)
    coordinator = IBKRRuntimeArbitrationCoordinator(
        client=client,
        enabled=True,
        lock=lock,
        registry=registry,
    )
    return coordinator, client


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

    def test_connect_error_wins_before_callback(self) -> None:
        coordinator = build_locked_coordinator()
        coordinator.begin_connect()

        self.assertTrue(coordinator.callback_connect_error(message="connect failed"))
        self.assertFalse(coordinator.callback_connect_ready())

        result = coordinator.connect_result()
        self.assertEqual(coordinator.completed_by, "callback_error")
        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_error")
        self.assertEqual(result.message, "connect failed")
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

    def test_successful_fake_connect_lifecycle(self) -> None:
        coordinator, client = build_connect_coordinator()

        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))

        self.assertEqual(client.connect_calls, [("127.0.0.1", 7497, 7)])
        self.assertLess(
            client.events.index("connect"),
            client.events.index("run_entered"),
        )
        self.assertEqual(coordinator.connect_state, "connecting")
        self.assertTrue(coordinator.callback_connect_ready())

        result = coordinator.connect_result()
        self.assertEqual(result.passed, True)
        self.assertEqual(coordinator.completed_by, "callback")
        self.assertEqual(coordinator.connect_state, "connected")
        self.assertFalse(coordinator.has_pending_connect())

        self.assertTrue(coordinator.disconnect(timeout=1.0))

    def test_timeout_cleanup_lifecycle_disconnects_then_joins(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))

        self.assertTrue(coordinator.timeout_connect())

        result = coordinator.connect_result()
        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_timeout")
        self.assertEqual(coordinator.completed_by, "timeout")
        self.assertEqual(coordinator.connect_state, "disconnected")
        self.assertEqual(coordinator.shutdown_state, "complete")
        self.assertEqual(client.disconnect_calls, 1)
        self.assertTrue(client.run_exited.is_set())
        self.assertEqual(coordinator.thread_owner.thread_state, "stopped")

    def test_disconnect_after_callback_success(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        self.assertTrue(coordinator.callback_connect_ready())

        self.assertTrue(coordinator.disconnect(timeout=1.0))

        self.assertEqual(client.disconnect_calls, 1)
        self.assertEqual(coordinator.connect_state, "disconnected")
        self.assertEqual(coordinator.shutdown_state, "complete")
        self.assertEqual(coordinator.thread_owner.thread_state, "stopped")

    def test_duplicate_connect_prevention(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))

        with self.assertRaisesRegex(RuntimeError, "connect already connecting"):
            coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)

        self.assertTrue(coordinator.disconnect(timeout=1.0))

    def test_duplicate_disconnect_safety(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        self.assertTrue(coordinator.callback_connect_ready())

        self.assertTrue(coordinator.disconnect(timeout=1.0))
        self.assertTrue(coordinator.disconnect(timeout=1.0))

        self.assertEqual(client.disconnect_calls, 1)
        self.assertEqual(coordinator.shutdown_state, "complete")

    def test_late_callback_during_disconnect_ignored(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        self.assertTrue(coordinator.callback_connect_ready())

        self.assertTrue(coordinator.disconnect(timeout=1.0))
        completed_result = coordinator.connect_result()

        self.assertFalse(coordinator.callback_connect_ready())
        self.assertIs(coordinator.connect_result(), completed_result)
        self.assertEqual(coordinator.completed_by, "callback")

    def test_join_ordering_after_disconnect(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        self.assertTrue(coordinator.callback_connect_ready())

        self.assertTrue(coordinator.disconnect(timeout=1.0))

        self.assertLess(
            client.events.index("disconnect"),
            client.events.index("run_exited"),
        )
        self.assertEqual(coordinator.thread_owner.thread_state, "stopped")

    def test_no_connect_disconnect_or_run_under_coordinator_lock(self) -> None:
        coordinator, client = build_connect_coordinator()

        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        self.assertTrue(coordinator.callback_connect_ready())
        self.assertTrue(coordinator.disconnect(timeout=1.0))

        self.assertEqual(client.run_lock_owned, [False])
        self.assertEqual(client.connect_lock_owned, [False])
        self.assertEqual(client.disconnect_lock_owned, [False])

    def test_run_thread_starts_only_after_successful_connect_call(self) -> None:
        coordinator, client = build_connect_coordinator()

        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))

        self.assertEqual(client.events[:2], ["connect", "run_entered"])
        self.assertEqual(client.run_calls, 1)
        self.assertTrue(coordinator.disconnect(timeout=1.0))

    def test_localhost_host_accepted(self) -> None:
        coordinator, client = build_connect_coordinator()

        coordinator.connect(host="localhost", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))

        self.assertEqual(client.connect_calls, [("localhost", 7497, 7)])
        self.assertTrue(coordinator.disconnect(timeout=1.0))

    def test_non_localhost_host_rejected(self) -> None:
        coordinator, client = build_connect_coordinator()

        with self.assertRaisesRegex(ValueError, "restricted to localhost"):
            coordinator.connect(
                host="192.168.1.10",
                port=7497,
                client_id=7,
                timeout=1.0,
            )

        self.assertEqual(client.connect_calls, [])
        self.assertEqual(client.run_calls, 0)

    def test_unsupported_port_rejected(self) -> None:
        coordinator, client = build_connect_coordinator()

        with self.assertRaisesRegex(ValueError, "restricted to paper ports"):
            coordinator.connect(host="127.0.0.1", port=7496, client_id=7, timeout=1.0)

        self.assertEqual(client.connect_calls, [])
        self.assertEqual(client.run_calls, 0)

    def test_none_timeout_rejected(self) -> None:
        coordinator, client = build_connect_coordinator()

        with self.assertRaisesRegex(ValueError, "finite timeout"):
            coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=None)

        self.assertEqual(client.connect_calls, [])
        self.assertEqual(client.run_calls, 0)

    def test_disabled_connect_rejected(self) -> None:
        lock = threading.RLock()
        registry = LockAssertingRegistry(lock)
        client = ControlledFakeRuntimeClient(lock=lock)
        coordinator = IBKRRuntimeArbitrationCoordinator(
            client=client,
            lock=lock,
            registry=registry,
        )

        with self.assertRaisesRegex(RuntimeError, "enabled=True"):
            coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)

        self.assertEqual(client.connect_calls, [])
        self.assertEqual(client.run_calls, 0)

    def test_connect_exception_cleanup_completes(self) -> None:
        coordinator, client = build_connect_coordinator()
        client.connect_exception = RuntimeError("connect failed")

        with self.assertRaisesRegex(RuntimeError, "connect failed"):
            coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)

        result = coordinator.connect_result()
        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_exception")
        self.assertEqual(coordinator.completed_by, "connect_exception")
        self.assertEqual(coordinator.connect_state, "disconnected")
        self.assertEqual(coordinator.shutdown_state, "complete")
        self.assertFalse(coordinator.has_pending_connect())
        self.assertEqual(client.disconnect_calls, 1)
        self.assertEqual(client.run_calls, 0)
        self.assertFalse(client.run_entered.is_set())
        self.assertFalse(client.run_exited.is_set())
        self.assertNotIn("run_entered", client.events)

    def test_runtime_thread_startup_failure_cleanup_completes(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.thread_owner = FailingRuntimeThreadOwner()

        with self.assertRaisesRegex(RuntimeError, "thread start failed"):
            coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)

        result = coordinator.connect_result()
        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "runtime_thread_start_failed")
        self.assertEqual(coordinator.completed_by, "runtime_thread_start_failed")
        self.assertEqual(coordinator.connect_state, "disconnected")
        self.assertEqual(coordinator.shutdown_state, "complete")
        self.assertFalse(coordinator.has_pending_connect())
        self.assertEqual(client.connect_calls, [("127.0.0.1", 7497, 7)])
        self.assertEqual(client.disconnect_calls, 1)
        self.assertEqual(client.run_calls, 0)
        self.assertEqual(client.events, ["connect", "disconnect"])

    def test_disconnect_exception_cleanup_still_finalizes_shutdown(self) -> None:
        coordinator, client = build_connect_coordinator()
        client.disconnect_exception = RuntimeError("disconnect failed")
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        self.assertTrue(coordinator.callback_connect_ready())

        self.assertTrue(coordinator.disconnect(timeout=1.0))

        self.assertEqual(coordinator.connect_state, "disconnected")
        self.assertEqual(coordinator.shutdown_state, "complete")
        self.assertEqual(client.disconnect_calls, 1)
        self.assertTrue(client.run_exited.is_set())

    def test_timeout_cleanup_remains_idempotent(self) -> None:
        coordinator, client = build_connect_coordinator()
        coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        self.assertTrue(client.run_entered.wait(timeout=1.0))

        self.assertTrue(coordinator.timeout_connect())
        self.assertFalse(coordinator.timeout_connect())
        self.assertTrue(coordinator.disconnect(timeout=1.0))

        self.assertEqual(client.disconnect_calls, 1)
        self.assertEqual(coordinator.shutdown_state, "complete")

    def test_late_callback_after_failed_cleanup_ignored(self) -> None:
        coordinator, client = build_connect_coordinator()
        client.connect_exception = RuntimeError("connect failed")
        with self.assertRaisesRegex(RuntimeError, "connect failed"):
            coordinator.connect(host="127.0.0.1", port=7497, client_id=7, timeout=1.0)
        completed_result = coordinator.connect_result()

        self.assertFalse(coordinator.callback_connect_ready())

        self.assertIs(coordinator.connect_result(), completed_result)
        self.assertEqual(coordinator.completed_by, "connect_exception")


class ControlledFakeRuntimeClient:
    def __init__(self, *, lock: threading.RLock) -> None:
        self.lock = lock
        self.stop_event = threading.Event()
        self.run_entered = threading.Event()
        self.run_exited = threading.Event()
        self.connect_calls: list[tuple[str, int, int]] = []
        self.disconnect_calls = 0
        self.run_calls = 0
        self.connect_exception: Exception | None = None
        self.disconnect_exception: Exception | None = None
        self.events: list[str] = []
        self.run_lock_owned: list[bool] = []
        self.connect_lock_owned: list[bool] = []
        self.disconnect_lock_owned: list[bool] = []

    def run(self) -> None:
        self.run_calls += 1
        self.run_lock_owned.append(self._lock_is_owned())
        self.events.append("run_entered")
        self.run_entered.set()
        self.stop_event.wait(timeout=2.0)
        self.events.append("run_exited")
        self.run_exited.set()

    def connect(self, host: str, port: int, client_id: int) -> None:
        self.connect_lock_owned.append(self._lock_is_owned())
        self.connect_calls.append((host, port, client_id))
        self.events.append("connect")
        if self.connect_exception is not None:
            raise self.connect_exception

    def disconnect(self) -> None:
        self.disconnect_lock_owned.append(self._lock_is_owned())
        self.disconnect_calls += 1
        self.events.append("disconnect")
        self.stop_event.set()
        if self.disconnect_exception is not None:
            raise self.disconnect_exception

    def _lock_is_owned(self) -> bool:
        is_owned = getattr(self.lock, "_is_owned", None)
        if is_owned is None:
            return False
        return bool(is_owned())


class FailingRuntimeThreadOwner:
    thread = None

    def start_thread(self, target) -> None:
        raise RuntimeError("thread start failed")

    def join_thread(self, timeout=None) -> bool:
        return True


if __name__ == "__main__":
    unittest.main()
