from __future__ import annotations

import unittest

from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_native_imports import IBKRDependencyUnavailable, load_ibkr_native_api
from ibkr_native_lifecycle import (
    IBKRRuntimeThreadOwner,
    build_ibkr_native_client_bundle,
)


class IBKRRealRunNoConnectSmokeTests(unittest.TestCase):
    def test_real_eclient_run_exits_cleanly_without_connectivity(self) -> None:
        try:
            native_api = load_ibkr_native_api()
        except IBKRDependencyUnavailable as exc:
            self.skipTest(str(exc))

        bridge = IBKRCallbackBridge()
        bundle = build_ibkr_native_client_bundle(
            native_api=native_api,
            bridge=bridge,
        )
        owner = IBKRRuntimeThreadOwner()
        connect_calls = []

        def forbidden_connect(*args, **kwargs) -> None:
            connect_calls.append((args, kwargs))
            raise AssertionError("no-connect smoke must not call client.connect")

        bundle.client.connect = forbidden_connect

        owner.start_thread(bundle.client.run)

        self.assertTrue(owner.join_thread(timeout=1.0))
        self.assertEqual(owner.thread_state, "stopped")
        self.assertEqual(owner.target_run_count, 1)
        self.assertEqual(owner.target_exception, None)
        self.assertEqual(connect_calls, [])
        self.assertEqual(bundle.client.isConnected(), False)
        self.assertEqual(bridge.registry.has_lifecycle("connect"), False)


if __name__ == "__main__":
    unittest.main()
