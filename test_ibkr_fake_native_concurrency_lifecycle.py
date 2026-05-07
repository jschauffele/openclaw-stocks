from __future__ import annotations

import threading
import unittest

from broker_interface import BrokerLifecycleResult
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_lifecycle import IBKRWrapperBridge
from ibkr_timeout_injector import IBKRTimeoutInjector


class FakeNativeConcurrencyOwner:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.bridge = IBKRCallbackBridge()
        self.wrapper = IBKRWrapperBridge(self.bridge)
        self.timeout_injector = IBKRTimeoutInjector(self.bridge.registry)
        self.connect_state = "disconnected"
        self.thread_state = "not_requested"
        self.completed_result: BrokerLifecycleResult | None = None
        self.completed_by: str | None = None
        self.notification_count = 0

    def request_connect(self) -> None:
        with self.lock:
            if self.connect_state != "disconnected":
                raise RuntimeError(f"IBKR connect already {self.connect_state}")
            self.bridge.begin_lifecycle(operation="connect")
            self.connect_state = "connecting"

    def callback_success(self, *, order_id: int = 101) -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            routed = self.wrapper.nextValidId(order_id)
            if not routed:
                return False
            self.completed_result = self.bridge.complete_lifecycle(operation="connect")
            self.completed_by = "callback"
            self.connect_state = "connected"
            self._notify_waiters()
            return True

    def callback_error(self, *, message: str = "cannot connect") -> bool:
        with self.lock:
            if self.completed_result is not None:
                return False
            routed = self.wrapper.error(-1, 502, message)
            if not routed:
                return False
            self.completed_result = self.bridge.complete_lifecycle(operation="connect")
            self.completed_by = "callback"
            self.connect_state = "disconnected"
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
            self.connect_state = "disconnected"
            self._notify_waiters()
            return True

    def fake_waiter_generation(self) -> int:
        with self.lock:
            return self.notification_count

    def fake_waiter_was_woken(self, *, previous_generation: int) -> bool:
        with self.lock:
            return self.notification_count > previous_generation

    def mark_thread_running(self) -> None:
        with self.lock:
            self.thread_state = "running"

    def mark_thread_stopped(self) -> None:
        with self.lock:
            self.thread_state = "stopped"
            self._notify_waiters()

    def disconnect(self) -> None:
        with self.lock:
            if self.thread_state != "stopped":
                raise RuntimeError("IBKR disconnect requires stopped thread")
            self.connect_state = "disconnected"

    def _notify_waiters(self) -> None:
        self.notification_count += 1
        self.condition.notify_all()


class IBKRFakeNativeConcurrencyLifecycleTests(unittest.TestCase):
    def test_callback_arrives_before_timeout(self) -> None:
        owner = FakeNativeConcurrencyOwner()
        owner.request_connect()

        self.assertTrue(owner.callback_success(order_id=101))
        self.assertFalse(owner.timeout())

        self.assertEqual(owner.completed_by, "callback")
        self.assertEqual(owner.completed_result.passed, True)
        self.assertEqual(owner.completed_result.message, "next_valid_id")
        self.assertEqual(owner.connect_state, "connected")

    def test_timeout_arrives_before_callback(self) -> None:
        owner = FakeNativeConcurrencyOwner()
        owner.request_connect()

        self.assertTrue(owner.timeout())
        self.assertFalse(owner.callback_success(order_id=101))

        self.assertEqual(owner.completed_by, "timeout")
        self.assertEqual(owner.completed_result.passed, False)
        self.assertEqual(owner.completed_result.reason, "connect_timeout")
        self.assertEqual(owner.connect_state, "disconnected")

    def test_late_callback_ignored_after_timeout(self) -> None:
        owner = FakeNativeConcurrencyOwner()
        owner.request_connect()
        owner.timeout()
        completed_result = owner.completed_result

        self.assertFalse(owner.callback_error(message="late error"))

        self.assertIs(owner.completed_result, completed_result)
        self.assertEqual(owner.completed_by, "timeout")
        self.assertEqual(owner.completed_result.message, "no nextValidId callback")

    def test_duplicate_callback_serialization(self) -> None:
        owner = FakeNativeConcurrencyOwner()
        owner.request_connect()

        self.assertTrue(owner.callback_success(order_id=101))
        self.assertFalse(owner.callback_success(order_id=101))
        self.assertFalse(owner.callback_error(message="duplicate error"))

        self.assertEqual(owner.completed_by, "callback")
        self.assertEqual(owner.completed_result.passed, True)
        self.assertEqual(owner.notification_count, 1)

    def test_callback_completion_wakes_waiter(self) -> None:
        owner = FakeNativeConcurrencyOwner()
        owner.request_connect()
        waiter_generation = owner.fake_waiter_generation()

        owner.callback_success(order_id=101)

        self.assertTrue(
            owner.fake_waiter_was_woken(previous_generation=waiter_generation)
        )
        self.assertEqual(owner.notification_count, 1)

    def test_disconnect_blocked_until_thread_stopped_state(self) -> None:
        owner = FakeNativeConcurrencyOwner()
        owner.request_connect()
        owner.mark_thread_running()
        owner.callback_success(order_id=101)

        with self.assertRaisesRegex(RuntimeError, "requires stopped thread"):
            owner.disconnect()

        owner.mark_thread_stopped()
        owner.disconnect()

        self.assertEqual(owner.thread_state, "stopped")
        self.assertEqual(owner.connect_state, "disconnected")

    def test_first_terminal_event_wins(self) -> None:
        owner = FakeNativeConcurrencyOwner()
        owner.request_connect()

        self.assertTrue(owner.callback_error(message="first terminal error"))
        self.assertFalse(owner.timeout())
        self.assertFalse(owner.callback_success(order_id=101))

        self.assertEqual(owner.completed_by, "callback")
        self.assertEqual(owner.completed_result.passed, False)
        self.assertEqual(owner.completed_result.reason, "connect_error")
        self.assertEqual(owner.completed_result.message, "first terminal error")
        self.assertEqual(owner.notification_count, 1)


if __name__ == "__main__":
    unittest.main()
