from __future__ import annotations

import sys
import unittest

from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_lifecycle import IBKRClientLifecycleController, IBKRWrapperBridge
from ibkr_timeout_injector import IBKRTimeoutInjector


class FakeNativeClient:
    def __init__(self) -> None:
        self.connect_calls: list[tuple[str, int, int]] = []
        self.disconnect_calls = 0
        self.connected = False

    def connect(self, host: str, port: int, client_id: int) -> None:
        self.connect_calls.append((host, port, client_id))
        self.connected = True

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        self.connected = False

    def isConnected(self) -> bool:
        return self.connected


class IBKRNativeLifecycleTests(unittest.TestCase):
    def test_next_valid_id_routes_to_lifecycle_readiness(self) -> None:
        bridge = IBKRCallbackBridge()
        wrapper = IBKRWrapperBridge(bridge)
        bridge.begin_lifecycle(operation="connect")

        self.assertTrue(wrapper.nextValidId(101))
        result = bridge.complete_lifecycle(operation="connect")

        self.assertEqual(result.passed, True)
        self.assertEqual(result.reason, "connect_ready")
        self.assertEqual(result.message, "next_valid_id")
        self.assertEqual(result.connected, True)

    def test_connect_error_routes_to_lifecycle_failure(self) -> None:
        bridge = IBKRCallbackBridge()
        wrapper = IBKRWrapperBridge(bridge)
        bridge.begin_lifecycle(operation="connect")

        self.assertTrue(wrapper.error(-1, 502, "cannot connect"))
        result = bridge.complete_lifecycle(operation="connect")

        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_error")
        self.assertEqual(result.message, "cannot connect")
        self.assertEqual(result.connected, False)

    def test_fake_client_connect_and_disconnect_calls_are_recorded(self) -> None:
        bridge = IBKRCallbackBridge()
        client = FakeNativeClient()
        controller = IBKRClientLifecycleController(
            client=client,
            bridge=bridge,
            timeout_injector=IBKRTimeoutInjector(bridge.registry),
        )

        controller.connect(host="127.0.0.1", port=7497, client_id=7)
        self.assertEqual(client.connect_calls, [("127.0.0.1", 7497, 7)])
        self.assertEqual(client.isConnected(), True)

        result = controller.disconnect()

        self.assertEqual(client.disconnect_calls, 1)
        self.assertEqual(client.isConnected(), False)
        self.assertEqual(result.passed, True)
        self.assertEqual(result.operation, "disconnect")
        self.assertEqual(result.connected, False)

    def test_health_check_reflects_fake_connected_state(self) -> None:
        bridge = IBKRCallbackBridge()
        client = FakeNativeClient()
        controller = IBKRClientLifecycleController(
            client=client,
            bridge=bridge,
            timeout_injector=IBKRTimeoutInjector(bridge.registry),
        )

        disconnected = controller.health_check()
        client.connected = True
        connected = controller.health_check()

        self.assertEqual(disconnected.passed, False)
        self.assertEqual(disconnected.connected, False)
        self.assertEqual(disconnected.reason, "ibkr_client_disconnected")
        self.assertEqual(connected.passed, True)
        self.assertEqual(connected.connected, True)
        self.assertEqual(connected.reason, "ibkr_client_connected")

    def test_timeout_injection_can_produce_connect_timeout(self) -> None:
        bridge = IBKRCallbackBridge()
        client = FakeNativeClient()
        controller = IBKRClientLifecycleController(
            client=client,
            bridge=bridge,
            timeout_injector=IBKRTimeoutInjector(bridge.registry),
        )
        controller.connect(host="127.0.0.1", port=7497, client_id=7)

        result = controller.connect_timeout(
            message="no nextValidId callback",
            elapsed_ms=5000,
        )

        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_timeout")
        self.assertEqual(result.message, "no nextValidId callback")
        self.assertEqual(result.elapsed_ms, 5000)

    def test_lifecycle_module_does_not_import_ibapi(self) -> None:
        imported_ibapi_modules = [
            name for name in sys.modules if name == "ibapi" or name.startswith("ibapi.")
        ]

        self.assertEqual(imported_ibapi_modules, [])


if __name__ == "__main__":
    unittest.main()
