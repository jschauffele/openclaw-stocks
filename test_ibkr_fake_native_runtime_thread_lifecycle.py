from __future__ import annotations

import threading
import unittest

from broker_interface import BrokerLifecycleResult
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_lifecycle import IBKRWrapperBridge


class FakeRuntimeThreadOwner:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.bridge = IBKRCallbackBridge()
        self.wrapper = IBKRWrapperBridge(self.bridge)
        self.thread_state = "not_started"
        self.shutdown_state = "active"
        self.connect_state = "connected"
        self.notification_count = 0
        self.join_attempts = 0
        self.join_completed = False
        self.shutdown_result: BrokerLifecycleResult | None = None
        self.shutdown_completed_by: str | None = None

    def thread_run_started(self) -> None:
        with self.lock:
            if self.thread_state != "not_started":
                raise RuntimeError(f"IBKR thread already {self.thread_state}")
            self.thread_state = "running"

    def thread_run_exited(self) -> None:
        with self.lock:
            if self.thread_state != "running":
                raise RuntimeError("IBKR thread exit requires running state")
            self.thread_state = "stopped"
            self._notify_waiters()

    def request_shutdown(self) -> None:
        with self.lock:
            if self.shutdown_state != "active":
                raise RuntimeError(f"IBKR shutdown already {self.shutdown_state}")
            self.shutdown_state = "stopping"

    def disconnect(self) -> None:
        with self.lock:
            if self.thread_state != "stopped":
                raise RuntimeError("IBKR disconnect requires stopped thread")
            self.connect_state = "disconnected"

    def join_after_run_exit(self) -> None:
        with self.lock:
            self.join_attempts += 1
            if self.thread_state != "stopped":
                raise RuntimeError("IBKR join requires stopped thread")
            self.join_completed = True

    def callback_during_shutdown(self, *, order_id: int = 101) -> bool:
        with self.lock:
            if self.shutdown_state == "complete":
                return False
            if self.shutdown_result is not None:
                return False
            self.bridge.begin_lifecycle(operation="disconnect")
            routed = self.bridge.connect_ready(
                operation="disconnect",
                message=f"late callback order_id={order_id}",
            )
            if not routed:
                return False
            self.shutdown_result = self.bridge.complete_lifecycle(
                operation="disconnect"
            )
            self.shutdown_completed_by = "callback"
            self._notify_waiters()
            return True

    def shutdown_terminal(self, *, reason: str) -> bool:
        with self.lock:
            if self.shutdown_result is not None:
                return False
            self.shutdown_result = BrokerLifecycleResult(
                broker_name="ibkr",
                operation="disconnect",
                passed=True,
                reason=reason,
                message=reason,
                connected=False,
                retryable=False,
                elapsed_ms=0,
                raw_error=None,
            )
            self.shutdown_completed_by = "shutdown"
            self.shutdown_state = "complete"
            self._notify_waiters()
            return True

    def complete_shutdown(self) -> None:
        with self.lock:
            self.shutdown_state = "complete"
            self._notify_waiters()

    def fake_waiter_generation(self) -> int:
        with self.lock:
            return self.notification_count

    def fake_waiter_was_woken(self, *, previous_generation: int) -> bool:
        with self.lock:
            return self.notification_count > previous_generation

    def _notify_waiters(self) -> None:
        self.notification_count += 1
        self.condition.notify_all()


class IBKRFakeNativeRuntimeThreadLifecycleTests(unittest.TestCase):
    def test_thread_run_started(self) -> None:
        owner = FakeRuntimeThreadOwner()

        owner.thread_run_started()

        self.assertEqual(owner.thread_state, "running")
        self.assertEqual(owner.notification_count, 0)

    def test_thread_run_exited(self) -> None:
        owner = FakeRuntimeThreadOwner()
        owner.thread_run_started()

        owner.thread_run_exited()

        self.assertEqual(owner.thread_state, "stopped")
        self.assertEqual(owner.notification_count, 1)

    def test_thread_exit_notifies_waiters(self) -> None:
        owner = FakeRuntimeThreadOwner()
        owner.thread_run_started()
        waiter_generation = owner.fake_waiter_generation()

        owner.thread_run_exited()

        self.assertTrue(
            owner.fake_waiter_was_woken(previous_generation=waiter_generation)
        )

    def test_disconnect_waits_for_thread_stop(self) -> None:
        owner = FakeRuntimeThreadOwner()
        owner.thread_run_started()
        owner.request_shutdown()

        with self.assertRaisesRegex(RuntimeError, "requires stopped thread"):
            owner.disconnect()

        owner.thread_run_exited()
        owner.disconnect()

        self.assertEqual(owner.connect_state, "disconnected")

    def test_join_ordering_after_run_exit(self) -> None:
        owner = FakeRuntimeThreadOwner()
        owner.thread_run_started()

        with self.assertRaisesRegex(RuntimeError, "join requires stopped thread"):
            owner.join_after_run_exit()

        owner.thread_run_exited()
        owner.join_after_run_exit()

        self.assertEqual(owner.join_attempts, 2)
        self.assertEqual(owner.join_completed, True)

    def test_late_callback_during_shutdown(self) -> None:
        owner = FakeRuntimeThreadOwner()
        owner.thread_run_started()
        owner.request_shutdown()

        self.assertTrue(owner.callback_during_shutdown(order_id=101))

        self.assertEqual(owner.shutdown_completed_by, "callback")
        self.assertEqual(owner.shutdown_result.passed, True)
        self.assertEqual(owner.shutdown_result.message, "late callback order_id=101")

    def test_callback_ignored_after_shutdown_complete(self) -> None:
        owner = FakeRuntimeThreadOwner()
        owner.thread_run_started()
        owner.request_shutdown()
        owner.shutdown_terminal(reason="disconnect_complete")
        owner.complete_shutdown()
        completed_result = owner.shutdown_result

        self.assertFalse(owner.callback_during_shutdown(order_id=101))

        self.assertIs(owner.shutdown_result, completed_result)
        self.assertEqual(owner.shutdown_completed_by, "shutdown")

    def test_shutdown_first_terminal_event_wins(self) -> None:
        owner = FakeRuntimeThreadOwner()
        owner.thread_run_started()
        owner.request_shutdown()

        self.assertTrue(owner.shutdown_terminal(reason="disconnect_complete"))
        self.assertFalse(owner.callback_during_shutdown(order_id=101))
        self.assertFalse(owner.shutdown_terminal(reason="second_terminal"))

        self.assertEqual(owner.shutdown_completed_by, "shutdown")
        self.assertEqual(owner.shutdown_result.reason, "disconnect_complete")
        self.assertEqual(owner.notification_count, 1)


if __name__ == "__main__":
    unittest.main()
