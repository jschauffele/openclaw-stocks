from __future__ import annotations

import unittest
from unittest.mock import patch

from broker_interface import (
    BrokerAccountState,
    BrokerCapabilities,
    BrokerLifecycleResult,
    BrokerPositionState,
)
from ibkr_broker_adapter import IBKRBrokerAdapter
from ibkr_callback_bridge import IBKRCallbackBridge
from ibkr_pending_request_registry import IBKRPendingRequestRegistry
from ibkr_request_coordinator import IBKRRequestCoordinator
from ibkr_timeout_injector import IBKRTimeoutInjector


def lifecycle_result(
    *,
    operation: str,
    passed: bool,
    reason: str,
    message: str,
    connected: bool,
    retryable: bool,
    raw_error=None,
) -> BrokerLifecycleResult:
    return BrokerLifecycleResult(
        broker_name="ibkr",
        operation=operation,
        passed=passed,
        reason=reason,
        message=message,
        connected=connected,
        retryable=retryable,
        elapsed_ms=0,
        raw_error=raw_error,
    )


class FakeClient:
    def __init__(self, *, connected: bool = False) -> None:
        self.connected = connected

    def isConnected(self) -> bool:
        return self.connected


class FakeAccountSummaryClient:
    def __init__(self) -> None:
        self.req_account_summary_calls = []
        self.cancel_account_summary_calls = []
        self.on_request = None

    def reqAccountSummary(self, request_id, group, tags) -> None:
        self.req_account_summary_calls.append(
            {"request_id": request_id, "group": group, "tags": tags}
        )
        if self.on_request is not None:
            self.on_request(request_id)

    def cancelAccountSummary(self, request_id) -> None:
        self.cancel_account_summary_calls.append(request_id)

    def isConnected(self) -> bool:
        return True


class FakePositionClient:
    def __init__(self) -> None:
        self.req_positions_multi_calls = []
        self.cancel_positions_multi_calls = []
        self.on_request = None

    def reqPositionsMulti(self, request_id, account, model_code) -> None:
        self.req_positions_multi_calls.append(
            {"request_id": request_id, "account": account, "model_code": model_code}
        )
        if self.on_request is not None:
            self.on_request(request_id)

    def cancelPositionsMulti(self, request_id) -> None:
        self.cancel_positions_multi_calls.append(request_id)

    def isConnected(self) -> bool:
        return True


class FakeCoordinator:
    def __init__(
        self,
        *,
        connect_result=None,
        disconnect_result=None,
        wait_result: bool = True,
        client=None,
    ) -> None:
        self.client = client
        self.connect_calls = []
        self.wait_calls = []
        self.timeout_calls = []
        self.disconnect_calls = []
        self._connect_result = connect_result
        self._disconnect_result = disconnect_result
        self.wait_result = wait_result

    def connect(self, **kwargs) -> None:
        self.connect_calls.append(kwargs)

    def wait_for_completion(self, *, timeout) -> bool:
        self.wait_calls.append({"timeout": timeout})
        return self.wait_result

    def timeout_connect(self, **kwargs) -> bool:
        self.timeout_calls.append(kwargs)
        self._connect_result = lifecycle_result(
            operation="connect",
            passed=False,
            reason="connect_timeout",
            message=kwargs["message"],
            connected=False,
            retryable=True,
        )
        return True

    def connect_result(self):
        return self._connect_result

    def disconnect(self, *, timeout) -> bool:
        self.disconnect_calls.append({"timeout": timeout})
        return self._disconnect_result is None or self._disconnect_result.passed

    def disconnect_result(self):
        return self._disconnect_result


class IBKRBrokerAdapterTests(unittest.TestCase):
    def test_capabilities_return_expected_ibkr_metadata(self) -> None:
        adapter = IBKRBrokerAdapter()

        self.assertEqual(
            adapter.get_capabilities(),
            BrokerCapabilities(
                broker_name="ibkr",
                supports_market_orders=False,
                supports_account_read=True,
                supports_positions_read=True,
                supports_open_orders_read=False,
                supports_paper_trading=True,
                lifecycle_async=True,
            ),
        )

    def test_state_and_order_methods_fail_explicitly(self) -> None:
        adapter = IBKRBrokerAdapter()

        expected_message = "IBKR adapter skeleton only; not runtime-enabled"

        for method_name, args in [
            ("get_account_buying_power", ()),
            ("get_existing_position", ("AAPL",)),
            ("get_open_buy_order_qty", ("AAPL",)),
            ("build_market_order", ("AAPL", 1)),
            ("submit_market_order", (object(),)),
            ("normalize_order_response", (object(),)),
        ]:
            with self.subTest(method=method_name):
                with self.assertRaisesRegex(NotImplementedError, expected_message):
                    getattr(adapter, method_name)(*args)

    def test_lifecycle_methods_require_injected_coordinator_except_health_check(
        self,
    ) -> None:
        adapter = IBKRBrokerAdapter()

        for method_name in ["connect", "disconnect"]:
            with self.subTest(method=method_name):
                with self.assertRaisesRegex(
                    NotImplementedError,
                    "IBKR adapter skeleton only; not runtime-enabled",
                ):
                    getattr(adapter, method_name)(timeout_seconds=1.5)

        self.assertEqual(
            adapter.health_check(timeout_seconds=1.5),
            BrokerLifecycleResult(
                broker_name="ibkr",
                operation="health_check",
                passed=False,
                reason="ibkr_client_disconnected",
                message="IBKR client reports disconnected",
                connected=False,
                retryable=True,
                elapsed_ms=0,
                raw_error=None,
            ),
        )

    def test_constructor_stores_injected_dependencies_without_enabling_runtime(
        self,
    ) -> None:
        client = object()
        native_api = object()
        bridge = object()
        registry = object()
        timeout_injector = object()

        adapter = IBKRBrokerAdapter(
            client,
            native_api=native_api,
            bridge=bridge,
            registry=registry,
            timeout_injector=timeout_injector,
        )

        self.assertIs(adapter.client, client)
        self.assertIs(adapter.native_api, native_api)
        self.assertIs(adapter.bridge, bridge)
        self.assertIs(adapter.registry, registry)
        self.assertIs(adapter.timeout_injector, timeout_injector)
        self.assertEqual(adapter.enabled, False)

        with self.assertRaisesRegex(
            NotImplementedError,
                "IBKR adapter skeleton only; not runtime-enabled",
        ):
            adapter.connect()

    def test_constructor_stores_injected_lifecycle_dependencies(self) -> None:
        client = FakeClient()
        coordinator = FakeCoordinator(client=client)

        adapter = IBKRBrokerAdapter(
            client,
            coordinator=coordinator,
            host="localhost",
            port=4002,
            client_id=17,
        )

        self.assertIs(adapter.client, client)
        self.assertIs(adapter.coordinator, coordinator)
        self.assertEqual(adapter.host, "localhost")
        self.assertEqual(adapter.port, 4002)
        self.assertEqual(adapter.client_id, 17)

    def test_constructor_builds_default_callback_scaffolding(self) -> None:
        adapter = IBKRBrokerAdapter()

        self.assertIsInstance(adapter.registry, IBKRPendingRequestRegistry)
        self.assertIsInstance(adapter.bridge, IBKRCallbackBridge)
        self.assertIsInstance(adapter.timeout_injector, IBKRTimeoutInjector)
        self.assertIs(adapter.bridge.registry, adapter.registry)
        self.assertIs(adapter.timeout_injector.registry, adapter.registry)

    def test_constructor_preserves_injected_registry_with_default_bridge_and_timeout(
        self,
    ) -> None:
        registry = IBKRPendingRequestRegistry()

        adapter = IBKRBrokerAdapter(registry=registry)

        self.assertIs(adapter.registry, registry)
        self.assertIs(adapter.bridge.registry, registry)
        self.assertIs(adapter.request_coordinator.registry, registry)
        self.assertIs(adapter.timeout_injector.registry, registry)

    def test_enabled_true_alone_does_not_implement_runtime_behavior(self) -> None:
        adapter = IBKRBrokerAdapter(enabled=True)

        self.assertEqual(adapter.enabled, True)
        with self.assertRaisesRegex(
            NotImplementedError,
            "IBKR adapter skeleton only; not runtime-enabled",
        ):
            adapter.connect()

    def test_connect_success_delegates_to_coordinator(self) -> None:
        result = lifecycle_result(
            operation="connect",
            passed=True,
            reason="connect_ready",
            message="next_valid_id",
            connected=True,
            retryable=False,
        )
        coordinator = FakeCoordinator(connect_result=result)
        adapter = IBKRBrokerAdapter(
            coordinator=coordinator,
            host="localhost",
            port=4002,
            client_id=17,
        )

        self.assertIs(adapter.connect(timeout_seconds=1.25), result)

        self.assertEqual(
            coordinator.connect_calls,
            [
                {
                    "host": "localhost",
                    "port": 4002,
                    "client_id": 17,
                    "timeout": 1.25,
                }
            ],
        )
        self.assertEqual(coordinator.wait_calls, [{"timeout": 1.25}])
        self.assertEqual(coordinator.timeout_calls, [])

    def test_connect_timeout_returns_coordinator_timeout_result(self) -> None:
        coordinator = FakeCoordinator(wait_result=False)
        adapter = IBKRBrokerAdapter(coordinator=coordinator)

        result = adapter.connect(timeout_seconds=1.5)

        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_timeout")
        self.assertEqual(
            result.message,
            "IBKR adapter timed out waiting for nextValidId",
        )
        self.assertEqual(
            coordinator.timeout_calls,
            [
                {
                    "message": "IBKR adapter timed out waiting for nextValidId",
                    "elapsed_ms": 1500,
                }
            ],
        )

    def test_connect_error_returns_coordinator_error_result(self) -> None:
        result = lifecycle_result(
            operation="connect",
            passed=False,
            reason="connect_error",
            message="connect failed",
            connected=False,
            retryable=True,
        )
        coordinator = FakeCoordinator(connect_result=result)
        adapter = IBKRBrokerAdapter(coordinator=coordinator)

        self.assertIs(adapter.connect(timeout_seconds=1.0), result)

    def test_connect_missing_result_is_deterministic_failure(self) -> None:
        coordinator = FakeCoordinator(connect_result=None)
        adapter = IBKRBrokerAdapter(coordinator=coordinator)

        result = adapter.connect(timeout_seconds=1.0)

        self.assertEqual(result.passed, False)
        self.assertEqual(result.reason, "connect_result_missing")
        self.assertEqual(result.connected, False)
        self.assertTrue(result.retryable)

    def test_account_summary_snapshot_success_issues_native_request(self) -> None:
        client = FakeAccountSummaryClient()
        adapter = IBKRBrokerAdapter(client=client, account_summary_request_id_start=7001)

        def complete(request_id) -> None:
            adapter.bridge.account_summary(
                request_id=request_id,
                account="DU123",
                tag="BuyingPower",
                value="12345.67",
                currency="USD",
            )
            adapter.bridge.account_summary_end(request_id=request_id)

        client.on_request = complete

        result = adapter.get_account_buying_power(timeout_seconds=0.25)

        self.assertEqual(
            result,
            BrokerAccountState(
                broker_name="ibkr",
                buying_power=12345.67,
                raw_account=result.raw_account,
            ),
        )
        self.assertEqual(
            client.req_account_summary_calls,
            [{"request_id": 7001, "group": "All", "tags": "BuyingPower"}],
        )
        self.assertEqual(client.cancel_account_summary_calls, [7001])
        self.assertEqual(adapter.request_coordinator.completed_by(7001), "callback")
        self.assertFalse(adapter.request_coordinator.has_pending_request(7001))

    def test_account_summary_timeout_removes_pending_request_and_cancels(self) -> None:
        client = FakeAccountSummaryClient()
        adapter = IBKRBrokerAdapter(client=client, account_summary_request_id_start=7101)

        with self.assertRaisesRegex(TimeoutError, "reqId=7101"):
            adapter.get_account_buying_power(timeout_seconds=0.001)

        self.assertEqual(
            client.req_account_summary_calls,
            [{"request_id": 7101, "group": "All", "tags": "BuyingPower"}],
        )
        self.assertEqual(client.cancel_account_summary_calls, [7101])
        self.assertEqual(adapter.request_coordinator.completed_by(7101), "timeout")
        self.assertIsInstance(adapter.request_coordinator.result(7101), ValueError)
        self.assertFalse(adapter.request_coordinator.has_pending_request(7101))
        self.assertFalse(
            adapter.bridge.account_summary(
                request_id=7101,
                tag="BuyingPower",
                value="999.99",
            )
        )
        self.assertFalse(adapter.bridge.account_summary_end(request_id=7101))

    def test_account_summary_wrong_and_missing_req_id_callbacks_are_ignored(self) -> None:
        client = FakeAccountSummaryClient()
        adapter = IBKRBrokerAdapter(client=client, account_summary_request_id_start=7201)

        def complete(request_id) -> None:
            self.assertFalse(
                adapter.bridge.account_summary(
                    request_id=request_id + 1,
                    tag="BuyingPower",
                    value="999.99",
                )
            )
            self.assertFalse(
                adapter.bridge.account_summary(
                    request_id=None,
                    tag="BuyingPower",
                    value="888.88",
                )
            )
            adapter.bridge.account_summary(
                request_id=request_id,
                tag="BuyingPower",
                value="111.11",
            )
            adapter.bridge.account_summary_end(request_id=request_id)

        client.on_request = complete

        result = adapter.get_account_buying_power(timeout_seconds=0.25)

        self.assertEqual(result.buying_power, 111.11)

    def test_account_summary_duplicate_end_marker_ignored_after_completion(self) -> None:
        client = FakeAccountSummaryClient()
        adapter = IBKRBrokerAdapter(client=client, account_summary_request_id_start=7301)

        def complete(request_id) -> None:
            adapter.bridge.account_summary(
                request_id=request_id,
                tag="BuyingPower",
                value="222.22",
            )
            self.assertTrue(adapter.bridge.account_summary_end(request_id=request_id))
            self.assertFalse(adapter.bridge.account_summary_end(request_id=request_id))

        client.on_request = complete

        result = adapter.get_account_buying_power(timeout_seconds=0.25)

        self.assertEqual(result.buying_power, 222.22)
        self.assertEqual(adapter.request_coordinator.notification_count, 1)

    def test_account_summary_request_ids_are_deterministic_and_isolated(self) -> None:
        client = FakeAccountSummaryClient()
        adapter = IBKRBrokerAdapter(client=client, account_summary_request_id_start=7401)

        def complete(request_id) -> None:
            adapter.bridge.account_summary(
                request_id=request_id,
                tag="BuyingPower",
                value=str(request_id),
            )
            adapter.bridge.account_summary_end(request_id=request_id)

        client.on_request = complete

        first = adapter.get_account_buying_power(timeout_seconds=0.25)
        second = adapter.get_account_buying_power(timeout_seconds=0.25)

        self.assertEqual(first.buying_power, 7401.0)
        self.assertEqual(second.buying_power, 7402.0)
        self.assertEqual(
            client.req_account_summary_calls,
            [
                {"request_id": 7401, "group": "All", "tags": "BuyingPower"},
                {"request_id": 7402, "group": "All", "tags": "BuyingPower"},
            ],
        )
        self.assertFalse(adapter.request_coordinator.has_pending_request(7401))
        self.assertFalse(adapter.request_coordinator.has_pending_request(7402))

    def test_account_summary_with_injected_request_coordinator_retains_result(self) -> None:
        registry = IBKRPendingRequestRegistry()
        request_coordinator = IBKRRequestCoordinator(registry=registry)
        client = FakeAccountSummaryClient()
        adapter = IBKRBrokerAdapter(
            client=client,
            registry=registry,
            request_coordinator=request_coordinator,
            account_summary_request_id_start=7501,
        )

        def complete(request_id) -> None:
            adapter.bridge.account_summary(
                request_id=request_id,
                tag="BuyingPower",
                value="333.33",
            )
            adapter.bridge.account_summary_end(request_id=request_id)

        client.on_request = complete

        result = adapter.get_account_buying_power(timeout_seconds=0.25)

        self.assertIs(request_coordinator.result(7501), result)
        self.assertEqual(result.buying_power, 333.33)

    def test_position_snapshot_success_issues_native_request(self) -> None:
        client = FakePositionClient()
        adapter = IBKRBrokerAdapter(
            client=client,
            position_account="DU123",
            position_model_code="",
            position_request_id_start=8001,
        )

        def complete(request_id) -> None:
            adapter.bridge.position_multi(
                request_id=request_id,
                account="DU123",
                model_code="",
                symbol="MSFT",
                qty="2",
            )
            adapter.bridge.position_multi(
                request_id=request_id,
                account="DU123",
                model_code="",
                symbol="AAPL",
                qty="-3",
                side="short",
            )
            adapter.bridge.position_multi_end(request_id=request_id)

        client.on_request = complete

        result = adapter.get_existing_position("AAPL", timeout_seconds=0.25)

        self.assertEqual(
            result,
            BrokerPositionState(
                broker_name="ibkr",
                found=True,
                qty=3,
                raw_qty="-3",
                side="short",
                reason="position_found",
            ),
        )
        self.assertEqual(
            client.req_positions_multi_calls,
            [{"request_id": 8001, "account": "DU123", "model_code": ""}],
        )
        self.assertEqual(client.cancel_positions_multi_calls, [8001])
        self.assertEqual(adapter.request_coordinator.completed_by(8001), "callback")
        self.assertFalse(adapter.request_coordinator.has_pending_request(8001))

    def test_position_snapshot_no_position_result_after_end_marker(self) -> None:
        client = FakePositionClient()
        adapter = IBKRBrokerAdapter(client=client, position_request_id_start=8101)

        def complete(request_id) -> None:
            adapter.bridge.position_multi(
                request_id=request_id,
                symbol="MSFT",
                qty="2",
            )
            adapter.bridge.position_multi_end(request_id=request_id)

        client.on_request = complete

        result = adapter.get_existing_position("AAPL", timeout_seconds=0.25)

        self.assertEqual(
            result,
            BrokerPositionState(
                broker_name="ibkr",
                found=False,
                qty=0,
                raw_qty="0",
                side=None,
                reason="no_position",
            ),
        )
        self.assertEqual(client.cancel_positions_multi_calls, [8101])
        self.assertFalse(adapter.request_coordinator.has_pending_request(8101))

    def test_position_timeout_removes_pending_request_and_cancels(self) -> None:
        client = FakePositionClient()
        adapter = IBKRBrokerAdapter(client=client, position_request_id_start=8201)

        with self.assertRaisesRegex(TimeoutError, "reqId=8201"):
            adapter.get_existing_position("AAPL", timeout_seconds=0.001)

        self.assertEqual(
            client.req_positions_multi_calls,
            [{"request_id": 8201, "account": "", "model_code": ""}],
        )
        self.assertEqual(client.cancel_positions_multi_calls, [8201])
        self.assertEqual(adapter.request_coordinator.completed_by(8201), "timeout")
        result = adapter.request_coordinator.result(8201)
        self.assertEqual(result.error, "position_snapshot_incomplete")
        self.assertFalse(adapter.request_coordinator.has_pending_request(8201))
        self.assertFalse(
            adapter.bridge.position_multi(request_id=8201, symbol="AAPL", qty="9")
        )
        self.assertFalse(adapter.bridge.position_multi_end(request_id=8201))

    def test_position_wrong_and_missing_req_id_callbacks_are_ignored(self) -> None:
        client = FakePositionClient()
        adapter = IBKRBrokerAdapter(client=client, position_request_id_start=8301)

        def complete(request_id) -> None:
            self.assertFalse(
                adapter.bridge.position_multi(
                    request_id=request_id + 1,
                    symbol="AAPL",
                    qty="999",
                )
            )
            self.assertFalse(
                adapter.bridge.position_multi(
                    request_id=None,
                    symbol="AAPL",
                    qty="888",
                )
            )
            adapter.bridge.position_multi(
                request_id=request_id,
                symbol="AAPL",
                qty="4",
            )
            adapter.bridge.position_multi_end(request_id=request_id)

        client.on_request = complete

        result = adapter.get_existing_position("AAPL", timeout_seconds=0.25)

        self.assertEqual(result.found, True)
        self.assertEqual(result.qty, 4)

    def test_position_duplicate_end_marker_ignored_after_completion(self) -> None:
        client = FakePositionClient()
        adapter = IBKRBrokerAdapter(client=client, position_request_id_start=8401)

        def complete(request_id) -> None:
            adapter.bridge.position_multi(
                request_id=request_id,
                symbol="AAPL",
                qty="5",
            )
            self.assertTrue(adapter.bridge.position_multi_end(request_id=request_id))
            self.assertFalse(adapter.bridge.position_multi_end(request_id=request_id))

        client.on_request = complete

        result = adapter.get_existing_position("AAPL", timeout_seconds=0.25)

        self.assertEqual(result.qty, 5)
        self.assertEqual(adapter.request_coordinator.notification_count, 1)

    def test_position_request_ids_are_deterministic_and_isolated(self) -> None:
        client = FakePositionClient()
        adapter = IBKRBrokerAdapter(client=client, position_request_id_start=8501)

        def complete(request_id) -> None:
            adapter.bridge.position_multi(
                request_id=request_id,
                symbol="AAPL",
                qty=str(request_id - 8500),
            )
            adapter.bridge.position_multi_end(request_id=request_id)

        client.on_request = complete

        first = adapter.get_existing_position("AAPL", timeout_seconds=0.25)
        second = adapter.get_existing_position("AAPL", timeout_seconds=0.25)

        self.assertEqual(first.qty, 1)
        self.assertEqual(second.qty, 2)
        self.assertEqual(
            client.req_positions_multi_calls,
            [
                {"request_id": 8501, "account": "", "model_code": ""},
                {"request_id": 8502, "account": "", "model_code": ""},
            ],
        )
        self.assertFalse(adapter.request_coordinator.has_pending_request(8501))
        self.assertFalse(adapter.request_coordinator.has_pending_request(8502))

    def test_position_with_injected_request_coordinator_retains_result(self) -> None:
        registry = IBKRPendingRequestRegistry()
        request_coordinator = IBKRRequestCoordinator(registry=registry)
        client = FakePositionClient()
        adapter = IBKRBrokerAdapter(
            client=client,
            registry=registry,
            request_coordinator=request_coordinator,
            position_request_id_start=8601,
        )

        def complete(request_id) -> None:
            adapter.bridge.position_multi(
                request_id=request_id,
                symbol="AAPL",
                qty="7",
            )
            adapter.bridge.position_multi_end(request_id=request_id)

        client.on_request = complete

        result = adapter.get_existing_position("AAPL", timeout_seconds=0.25)

        self.assertIs(request_coordinator.result(8601), result)
        self.assertEqual(result.qty, 7)

    def test_health_check_connected(self) -> None:
        adapter = IBKRBrokerAdapter(client=FakeClient(connected=True))

        self.assertEqual(
            adapter.health_check(),
            BrokerLifecycleResult(
                broker_name="ibkr",
                operation="health_check",
                passed=True,
                reason="ibkr_client_connected",
                message="IBKR client reports connected",
                connected=True,
                retryable=False,
                elapsed_ms=0,
                raw_error=None,
            ),
        )

    def test_health_check_disconnected(self) -> None:
        adapter = IBKRBrokerAdapter(client=FakeClient(connected=False))

        self.assertEqual(
            adapter.health_check(),
            BrokerLifecycleResult(
                broker_name="ibkr",
                operation="health_check",
                passed=False,
                reason="ibkr_client_disconnected",
                message="IBKR client reports disconnected",
                connected=False,
                retryable=True,
                elapsed_ms=0,
                raw_error=None,
            ),
        )

    def test_health_check_uses_coordinator_client_when_adapter_client_missing(
        self,
    ) -> None:
        coordinator = FakeCoordinator(client=FakeClient(connected=True))
        adapter = IBKRBrokerAdapter(coordinator=coordinator)

        self.assertEqual(adapter.health_check().reason, "ibkr_client_connected")

    def test_disconnect_success_returns_coordinator_result(self) -> None:
        result = lifecycle_result(
            operation="disconnect",
            passed=True,
            reason="disconnect_complete",
            message="IBKR runtime disconnected",
            connected=False,
            retryable=False,
        )
        coordinator = FakeCoordinator(disconnect_result=result)
        adapter = IBKRBrokerAdapter(coordinator=coordinator)

        self.assertIs(adapter.disconnect(timeout_seconds=2.0), result)
        self.assertEqual(coordinator.disconnect_calls, [{"timeout": 2.0}])

    def test_disconnect_stuck_thread_returns_coordinator_result(self) -> None:
        diagnostic = {"thread_state": "running"}
        result = lifecycle_result(
            operation="disconnect",
            passed=False,
            reason="runtime_thread_join_timeout",
            message="IBKR runtime thread did not stop before join timeout",
            connected=True,
            retryable=True,
            raw_error=diagnostic,
        )
        coordinator = FakeCoordinator(disconnect_result=result)
        adapter = IBKRBrokerAdapter(coordinator=coordinator)

        self.assertIs(adapter.disconnect(timeout_seconds=0.5), result)

    def test_disconnect_without_coordinator_result_returns_fallback_result(self) -> None:
        coordinator = FakeCoordinator(disconnect_result=None)
        adapter = IBKRBrokerAdapter(coordinator=coordinator)

        self.assertEqual(
            adapter.disconnect(timeout_seconds=0.5),
            BrokerLifecycleResult(
                broker_name="ibkr",
                operation="disconnect",
                passed=True,
                reason="disconnect_complete",
                message="IBKR runtime disconnected",
                connected=False,
                retryable=False,
                elapsed_ms=None,
                raw_error=None,
            ),
        )

    def test_constructor_does_not_call_native_import_loader(self) -> None:
        with patch(
            "ibkr_native_imports.load_ibkr_native_api",
            side_effect=AssertionError("native loader should not be called"),
        ):
            adapter = IBKRBrokerAdapter()

        self.assertEqual(adapter.enabled, False)


if __name__ == "__main__":
    unittest.main()
