from __future__ import annotations

import threading
import unittest

from ibkr_native_lifecycle import IBKRRuntimeThreadOwner


class IBKRRuntimeThreadOwnerTests(unittest.TestCase):
    def test_fake_target_runs_once(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        calls = []

        owner.start_thread(lambda: calls.append("ran"))
        self.assertTrue(owner.join_thread(timeout=1.0))

        self.assertEqual(calls, ["ran"])
        self.assertEqual(owner.target_run_count, 1)

    def test_thread_state_not_started_to_running_to_stopped(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        release_target = threading.Event()
        running_seen = []

        def target() -> None:
            with owner.lock:
                running_seen.append(owner.thread_state)
            release_target.wait(timeout=1.0)

        owner.start_thread(target)
        with owner.condition:
            self.assertTrue(
                owner.condition.wait_for(
                    lambda: owner.thread_state == "running",
                    timeout=1.0,
                )
            )

        self.assertEqual(running_seen, ["running"])
        self.assertEqual(owner.thread_state, "running")

        release_target.set()
        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertEqual(owner.thread_state, "stopped")

    def test_duplicate_start_rejected(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        release_target = threading.Event()

        owner.start_thread(lambda: release_target.wait(timeout=1.0))
        with owner.condition:
            self.assertTrue(
                owner.condition.wait_for(
                    lambda: owner.thread_state == "running",
                    timeout=1.0,
                )
            )

        with self.assertRaisesRegex(RuntimeError, "already running"):
            owner.start_thread(lambda: None)

        release_target.set()
        self.assertTrue(owner.join_thread(timeout=1.0))

    def test_join_after_exit_succeeds(self) -> None:
        owner = IBKRRuntimeThreadOwner()

        owner.start_thread(lambda: None)
        self.assertTrue(owner.join_thread(timeout=1.0))

        self.assertEqual(owner.thread_state, "stopped")

    def test_join_before_stopped_does_not_deadlock(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        release_target = threading.Event()

        owner.start_thread(lambda: release_target.wait(timeout=1.0))
        with owner.condition:
            self.assertTrue(
                owner.condition.wait_for(
                    lambda: owner.thread_state == "running",
                    timeout=1.0,
                )
            )

        self.assertFalse(owner.join_thread(timeout=0.01))
        self.assertEqual(owner.thread_state, "running")

        release_target.set()
        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertEqual(owner.thread_state, "stopped")

    def test_shutdown_marks_stopping_before_join(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        release_target = threading.Event()

        owner.start_thread(lambda: release_target.wait(timeout=1.0))
        with owner.condition:
            self.assertTrue(
                owner.condition.wait_for(
                    lambda: owner.thread_state == "running",
                    timeout=1.0,
                )
            )
        owner.request_shutdown()

        self.assertEqual(owner.shutdown_state, "stopping")
        self.assertFalse(owner.join_thread(timeout=0.01))

        release_target.set()
        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertEqual(owner.shutdown_state, "complete")

    def test_no_real_ibkr_client_run_or_connect_used(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = GuardedFakeClient()
        fake_calls = []

        def fake_target() -> None:
            fake_calls.append("fake target only")

        owner.start_thread(fake_target)
        self.assertTrue(owner.join_thread(timeout=1.0))

        self.assertEqual(fake_calls, ["fake target only"])
        self.assertEqual(client.connect_calls, 0)
        self.assertEqual(client.run_calls, 0)
        self.assertEqual(owner.target_exception, None)

    def test_runtime_thread_starts_fake_client_run(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = ControlledFakeRuntimeClient(owner=owner)

        owner.start_thread(client.run)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        owner.request_shutdown(stop_signal=client.stop)

        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertEqual(client.run_calls, 1)
        self.assertTrue(client.run_exited.is_set())

    def test_run_loop_stays_active_until_stop_signal(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = ControlledFakeRuntimeClient(owner=owner)

        owner.start_thread(client.run)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        self.assertTrue(client.wait_for_loop_iterations(2, timeout=1.0))
        self.assertEqual(owner.thread_state, "running")
        self.assertFalse(client.run_exited.is_set())

        owner.request_shutdown(stop_signal=client.stop)
        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertTrue(client.run_exited.is_set())

    def test_shutdown_requests_stop_signal_and_run_exits(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = ControlledFakeRuntimeClient(owner=owner)

        owner.start_thread(client.run)
        self.assertTrue(client.run_entered.wait(timeout=1.0))

        owner.request_shutdown(stop_signal=client.stop)

        self.assertEqual(owner.shutdown_state, "stopping")
        self.assertTrue(client.stop_event.is_set())
        self.assertTrue(client.run_exited.wait(timeout=1.0))
        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertEqual(owner.shutdown_state, "complete")

    def test_waiters_notified_on_run_exit(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = ControlledFakeRuntimeClient(owner=owner)

        owner.start_thread(client.run)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        owner.request_shutdown(stop_signal=client.stop)

        with owner.condition:
            self.assertTrue(
                owner.condition.wait_for(
                    lambda: owner.thread_state == "stopped",
                    timeout=1.0,
                )
            )
        self.assertTrue(owner.join_thread(timeout=1.0))

    def test_join_succeeds_after_fake_run_stop(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = ControlledFakeRuntimeClient(owner=owner)

        owner.start_thread(client.run)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        owner.request_shutdown(stop_signal=client.stop)

        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertEqual(owner.thread_state, "stopped")

    def test_duplicate_shutdown_requests_are_deterministic(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = ControlledFakeRuntimeClient(owner=owner)

        owner.start_thread(client.run)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        owner.request_shutdown(stop_signal=client.stop)

        with self.assertRaisesRegex(RuntimeError, "shutdown already stopping"):
            owner.request_shutdown(stop_signal=client.stop)

        self.assertTrue(owner.join_thread(timeout=1.0))
        with self.assertRaisesRegex(RuntimeError, "shutdown already complete"):
            owner.request_shutdown(stop_signal=client.stop)

    def test_fake_run_loop_does_not_execute_under_owner_lock(self) -> None:
        owner = IBKRRuntimeThreadOwner()
        client = ControlledFakeRuntimeClient(owner=owner)

        owner.start_thread(client.run)
        self.assertTrue(client.run_entered.wait(timeout=1.0))
        owner.request_shutdown(stop_signal=client.stop)
        self.assertTrue(owner.join_thread(timeout=1.0))

        self.assertEqual(client.owner_lock_owned_during_run, [False])


class GuardedFakeClient:
    def __init__(self) -> None:
        self.connect_calls = 0
        self.run_calls = 0

    def connect(self) -> None:
        self.connect_calls += 1
        raise AssertionError("fake runtime thread owner must not call connect")

    def run(self) -> None:
        self.run_calls += 1
        raise AssertionError("fake runtime thread owner must not call run")


class ControlledFakeRuntimeClient:
    def __init__(self, *, owner: IBKRRuntimeThreadOwner) -> None:
        self.owner = owner
        self.stop_event = threading.Event()
        self.run_entered = threading.Event()
        self.run_exited = threading.Event()
        self.loop_condition = threading.Condition()
        self.loop_iterations = 0
        self.run_calls = 0
        self.owner_lock_owned_during_run: list[bool] = []

    def run(self) -> None:
        self.run_calls += 1
        self.owner_lock_owned_during_run.append(self._owner_lock_is_owned())
        self.run_entered.set()
        try:
            while not self.stop_event.is_set():
                with self.loop_condition:
                    self.loop_iterations += 1
                    self.loop_condition.notify_all()
                self.stop_event.wait(timeout=0.001)
        finally:
            self.run_exited.set()

    def stop(self) -> None:
        self.stop_event.set()

    def wait_for_loop_iterations(self, count: int, *, timeout: float) -> bool:
        with self.loop_condition:
            return self.loop_condition.wait_for(
                lambda: self.loop_iterations >= count,
                timeout=timeout,
            )

    def _owner_lock_is_owned(self) -> bool:
        is_owned = getattr(self.owner.lock, "_is_owned", None)
        if is_owned is None:
            return False
        return bool(is_owned())


if __name__ == "__main__":
    unittest.main()
