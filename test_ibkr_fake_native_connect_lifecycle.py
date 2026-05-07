from __future__ import annotations

import unittest

from broker_interface import BrokerLifecycleResult
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_lifecycle import IBKRClientLifecycleController, IBKRWrapperBridge
from ibkr_timeout_injector import IBKRTimeoutInjector


class ConnectLifecycleFakeClient:
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


class FakeNativeConnectLifecycleOwner:
    def __init__(self) -> None:
        self.bridge = IBKRCallbackBridge()
        self.wrapper = IBKRWrapperBridge(self.bridge)
        self.client = ConnectLifecycleFakeClient()
        self.controller = IBKRClientLifecycleController(
            client=self.client,
            bridge=self.bridge,
            timeout_injector=IBKRTimeoutInjector(self.bridge.registry),
        )
        self.state = "disconnected"

    def request_connect(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 7,
    ) -> None:
        if self.state in {"connecting", "connected"}:
            raise RuntimeError(f"IBKR connect already {self.state}")
        self.controller.connect(host=host, port=port, client_id=client_id)
        self.state = "connecting"

    def complete_connect(self, *, order_id: int = 101) -> BrokerLifecycleResult:
        if self.state != "connecting":
            raise RuntimeError("IBKR connect completion requires connecting state")
        self.wrapper.nextValidId(order_id)
        result = self.controller.complete_connect()
        if result.passed:
            self.client.connected = True
            self.state = "connected"
        return result

    def timeout_connect(self) -> BrokerLifecycleResult:
        if self.state != "connecting":
            raise RuntimeError("IBKR connect timeout requires connecting state")
        result = self.controller.connect_timeout(
            message="no nextValidId callback",
            elapsed_ms=5000,
        )
        self.state = "disconnected"
        return result

    def disconnect(self) -> BrokerLifecycleResult:
        result = self.controller.disconnect()
        self.state = "disconnected"
        return result


class IBKRFakeNativeConnectLifecycleTests(unittest.TestCase):
    def test_connect_requested_records_fake_client_connect_only(self) -> None:
        owner = FakeNativeConnectLifecycleOwner()

        owner.request_connect()

        self.assertEqual(owner.state, "connecting")
        self.assertEqual(owner.client.connect_calls, [("127.0.0.1", 7497, 7)])
        self.assertEqual(owner.client.run_calls, 0)
        self.assertEqual(owner.client.disconnect_calls, 0)
        self.assertEqual(owner.client.isConnected(), False)

    def test_connect_success_transitions_to_connected(self) -> None:
        owner = FakeNativeConnectLifecycleOwner()
        owner.request_connect()

        result = owner.complete_connect(order_id=101)

        self.assertEqual(owner.state, "connected")
        self.assertEqual(result.passed, True)
        self.assertEqual(result.reason, "connect_ready")
        self.assertEqual(result.message, "next_valid_id")
        self.assertEqual(result.connected, True)
        self.assertEqual(owner.client.isConnected(), True)
        self.assertEqual(owner.client.run_calls, 0)

    def test_connect_timeout_transitions_to_disconnected(self) -> None:
        owner = FakeNativeConnectLifecycleOwner()
        owner.request_connect()

        result = owner.timeout_connect()

        self.assertEqual(owner.state, "disconnected")
        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_timeout")
        self.assertEqual(result.message, "no nextValidId callback")
        self.assertEqual(result.connected, False)
        self.assertEqual(owner.client.isConnected(), False)
        self.assertEqual(owner.client.run_calls, 0)

    def test_duplicate_connect_is_prevented_while_connecting(self) -> None:
        owner = FakeNativeConnectLifecycleOwner()
        owner.request_connect()

        with self.assertRaisesRegex(RuntimeError, "IBKR connect already connecting"):
            owner.request_connect()

        self.assertEqual(owner.client.connect_calls, [("127.0.0.1", 7497, 7)])
        self.assertEqual(owner.client.run_calls, 0)

    def test_duplicate_connect_is_prevented_after_connect_success(self) -> None:
        owner = FakeNativeConnectLifecycleOwner()
        owner.request_connect()
        owner.complete_connect(order_id=101)

        with self.assertRaisesRegex(RuntimeError, "IBKR connect already connected"):
            owner.request_connect()

        self.assertEqual(owner.client.connect_calls, [("127.0.0.1", 7497, 7)])
        self.assertEqual(owner.client.run_calls, 0)

    def test_disconnect_after_connect_transitions_to_disconnected(self) -> None:
        owner = FakeNativeConnectLifecycleOwner()
        owner.request_connect()
        owner.complete_connect(order_id=101)

        result = owner.disconnect()

        self.assertEqual(owner.state, "disconnected")
        self.assertEqual(owner.client.disconnect_calls, 1)
        self.assertEqual(owner.client.isConnected(), False)
        self.assertEqual(result.passed, True)
        self.assertEqual(result.operation, "disconnect")
        self.assertEqual(result.connected, False)
        self.assertEqual(owner.client.run_calls, 0)


if __name__ == "__main__":
    unittest.main()
