from __future__ import annotations

import unittest

from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_lifecycle import IBKRClientLifecycleController, IBKRWrapperBridge
from ibkr_timeout_injector import IBKRTimeoutInjector


class ThreadLifecycleFakeClient:
    def __init__(self) -> None:
        self.connect_calls: list[tuple[str, int, int]] = []
        self.disconnect_calls = 0
        self.run_calls = 0
        self.connected = False

    def connect(self, host: str, port: int, client_id: int) -> None:
        self.connect_calls.append((host, port, client_id))

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        self.connected = False

    def run(self) -> None:
        self.run_calls += 1

    def isConnected(self) -> bool:
        return self.connected


class FakeNativeThreadLifecycleOwner:
    def __init__(self) -> None:
        self.bridge = IBKRCallbackBridge()
        self.wrapper = IBKRWrapperBridge(self.bridge)
        self.client = ThreadLifecycleFakeClient()
        self.controller = IBKRClientLifecycleController(
            client=self.client,
            bridge=self.bridge,
            timeout_injector=IBKRTimeoutInjector(self.bridge.registry),
        )
        self.connect_state = "disconnected"
        self.thread_state = "not_requested"
        self.thread_requests = 0

    def request_connect(self) -> None:
        if self.connect_state != "disconnected":
            raise RuntimeError(f"IBKR connect already {self.connect_state}")
        self.controller.connect(host="127.0.0.1", port=7497, client_id=7)
        self.connect_state = "connecting"

    def request_thread(self) -> None:
        if self.thread_state in {"requested", "running"}:
            raise RuntimeError(f"IBKR thread already {self.thread_state}")
        self.thread_requests += 1
        self.thread_state = "requested"

    def mark_thread_running(self) -> None:
        if self.thread_state != "requested":
            raise RuntimeError("IBKR thread running requires requested state")
        self.thread_state = "running"

    def mark_thread_stopped(self) -> None:
        if self.thread_state not in {"requested", "running"}:
            raise RuntimeError("IBKR thread stop requires active thread state")
        self.thread_state = "stopped"

    def complete_connect(self) -> None:
        if self.connect_state != "connecting":
            raise RuntimeError("IBKR connect completion requires connecting state")
        self.wrapper.nextValidId(101)
        result = self.controller.complete_connect()
        if result.passed:
            self.client.connected = True
            self.connect_state = "connected"

    def timeout_connect(self) -> None:
        if self.connect_state != "connecting":
            raise RuntimeError("IBKR connect timeout requires connecting state")
        self.controller.connect_timeout(
            message="no nextValidId callback",
            elapsed_ms=5000,
        )
        self.connect_state = "disconnected"

    def disconnect(self) -> None:
        if self.thread_state != "stopped":
            raise RuntimeError("IBKR disconnect requires stopped thread")
        self.controller.disconnect()
        self.connect_state = "disconnected"


class IBKRFakeNativeThreadLifecycleTests(unittest.TestCase):
    def test_thread_requested_records_ownership_without_starting_thread(self) -> None:
        owner = FakeNativeThreadLifecycleOwner()

        owner.request_thread()

        self.assertEqual(owner.thread_state, "requested")
        self.assertEqual(owner.thread_requests, 1)
        self.assertEqual(owner.client.run_calls, 0)

    def test_duplicate_thread_prevention(self) -> None:
        owner = FakeNativeThreadLifecycleOwner()
        owner.request_thread()

        with self.assertRaisesRegex(RuntimeError, "IBKR thread already requested"):
            owner.request_thread()

        owner.mark_thread_running()
        with self.assertRaisesRegex(RuntimeError, "IBKR thread already running"):
            owner.request_thread()

        self.assertEqual(owner.thread_requests, 1)
        self.assertEqual(owner.client.run_calls, 0)

    def test_thread_marked_running(self) -> None:
        owner = FakeNativeThreadLifecycleOwner()
        owner.request_thread()

        owner.mark_thread_running()

        self.assertEqual(owner.thread_state, "running")
        self.assertEqual(owner.client.run_calls, 0)

    def test_thread_marked_stopped(self) -> None:
        owner = FakeNativeThreadLifecycleOwner()
        owner.request_thread()
        owner.mark_thread_running()

        owner.mark_thread_stopped()

        self.assertEqual(owner.thread_state, "stopped")
        self.assertEqual(owner.client.run_calls, 0)

    def test_disconnect_requires_thread_stop(self) -> None:
        owner = FakeNativeThreadLifecycleOwner()
        owner.request_connect()
        owner.request_thread()
        owner.mark_thread_running()
        owner.complete_connect()

        with self.assertRaisesRegex(RuntimeError, "requires stopped thread"):
            owner.disconnect()

        owner.mark_thread_stopped()
        owner.disconnect()

        self.assertEqual(owner.connect_state, "disconnected")
        self.assertEqual(owner.thread_state, "stopped")
        self.assertEqual(owner.client.disconnect_calls, 1)
        self.assertEqual(owner.client.run_calls, 0)

    def test_timeout_during_connect_before_thread_start(self) -> None:
        owner = FakeNativeThreadLifecycleOwner()
        owner.request_connect()

        owner.timeout_connect()

        self.assertEqual(owner.connect_state, "disconnected")
        self.assertEqual(owner.thread_state, "not_requested")
        self.assertEqual(owner.thread_requests, 0)
        self.assertEqual(owner.client.run_calls, 0)
        self.assertEqual(owner.client.disconnect_calls, 0)


if __name__ == "__main__":
    unittest.main()
