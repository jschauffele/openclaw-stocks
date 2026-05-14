from __future__ import annotations

import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ibkr_runtime_diagnostics import (
    DEFAULT_CLIENT_ID,
    classify_broker_state,
    run_ibkr_runtime_diagnostics,
)


class FakeNativeWrapper:
    pass


class FakeExecutionFilter:
    pass


class FakeNativeApi:
    e_wrapper = FakeNativeWrapper
    execution_filter = FakeExecutionFilter

    def __init__(self, client_factory) -> None:
        self.client_factory = client_factory

    def e_client(self, wrapper):
        return self.client_factory(wrapper)


class DiagnosticsFakeClient:
    def __init__(
        self,
        wrapper,
        *,
        open_order_qty: str = "0",
        open_order_status: str = "Submitted",
        position_qty: str = "0",
        disconnect_event: threading.Event | None = None,
        release_on_disconnect: bool = True,
    ) -> None:
        self.wrapper = wrapper
        self.connected = False
        self.disconnect_event = disconnect_event or threading.Event()
        self.open_order_qty = open_order_qty
        self.open_order_status = open_order_status
        self.position_qty = position_qty
        self.release_on_disconnect = release_on_disconnect
        self.connect_calls = []
        self.req_all_open_orders_calls = 0
        self.req_positions_multi_calls = []
        self.req_executions_calls = []
        self.cancel_order_calls = []
        self.req_global_cancel_calls = 0
        self.disconnect_calls = 0
        self.cancel_positions_multi_calls = []

    def connect(self, host, port, client_id) -> None:
        self.connect_calls.append(
            {"host": host, "port": port, "client_id": client_id}
        )
        self.connected = True
        self.wrapper.nextValidId(7001)

    def isConnected(self) -> bool:
        return self.connected

    def run(self) -> None:
        self.disconnect_event.wait(timeout=5.0)

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        self.connected = False
        if self.release_on_disconnect:
            self.disconnect_event.set()

    def reqAllOpenOrders(self) -> None:
        self.req_all_open_orders_calls += 1
        if self.open_order_qty != "0":
            self.wrapper.openOrder(
                11,
                SimpleNamespace(symbol="AAPL"),
                SimpleNamespace(action="BUY", totalQuantity=self.open_order_qty, permId=91),
                SimpleNamespace(status=self.open_order_status),
            )
        self.wrapper.openOrderEnd()

    def reqPositionsMulti(self, request_id, account, model_code) -> None:
        self.req_positions_multi_calls.append(
            {"request_id": request_id, "account": account, "model_code": model_code}
        )
        if self.position_qty != "0":
            self.wrapper.positionMulti(
                request_id,
                "DU123",
                "",
                SimpleNamespace(symbol="AAPL"),
                self.position_qty,
                "0",
            )
        self.wrapper.positionMultiEnd(request_id)

    def cancelPositionsMulti(self, request_id) -> None:
        self.cancel_positions_multi_calls.append(request_id)

    def reqExecutions(self, request_id, execution_filter) -> None:
        self.req_executions_calls.append(
            {"request_id": request_id, "execution_filter": execution_filter}
        )
        self.wrapper.execDetailsEnd(request_id)

    def cancelOrder(self, order_id) -> None:
        self.cancel_order_calls.append(order_id)

    def reqGlobalCancel(self) -> None:
        self.req_global_cancel_calls += 1


def fake_loader_for(client_holder: list[DiagnosticsFakeClient], **client_kwargs):
    def load_native_api():
        def build_client(wrapper):
            client = DiagnosticsFakeClient(wrapper, **client_kwargs)
            client_holder.append(client)
            return client

        return FakeNativeApi(build_client)

    return load_native_api


class IBKRRuntimeDiagnosticsTests(unittest.TestCase):
    def test_refuses_non_localhost_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "localhost"):
            run_ibkr_runtime_diagnostics(
                host="192.168.1.10",
                timeout=1.0,
                native_api_loader=Mock(),
                print_output=False,
            )

    def test_refuses_non_paper_port(self) -> None:
        with self.assertRaisesRegex(ValueError, "paper ports"):
            run_ibkr_runtime_diagnostics(
                port=7496,
                timeout=1.0,
                native_api_loader=Mock(),
                print_output=False,
            )

    def test_refuses_non_positive_timeout(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite positive timeout"):
            run_ibkr_runtime_diagnostics(
                timeout=0,
                native_api_loader=Mock(),
                print_output=False,
            )

    def test_connects_and_queries_read_only_state_with_fakes(self) -> None:
        clients: list[DiagnosticsFakeClient] = []

        result = run_ibkr_runtime_diagnostics(
            timeout=0.5,
            disconnect_timeout=0.05,
            native_api_loader=fake_loader_for(clients),
            print_output=False,
        )

        self.assertEqual(result["connection_result"]["passed"], True)
        self.assertEqual(result["connection_completion_source"], "callback")
        self.assertEqual(result["next_valid_id"], 7001)
        self.assertEqual(result["open_order_snapshot"]["open_buy_order_count"], 0)
        self.assertEqual(result["position_snapshot"]["qty"], 0)
        self.assertEqual(result["broker_state"], "clean")
        self.assertEqual(result["disconnect_result"]["passed"], True)
        self.assertEqual(result["connect_state"], "disconnected")
        self.assertEqual(result["shutdown_state"], "complete")
        self.assertEqual(result["thread_state"]["thread_state"], "stopped")
        self.assertEqual(clients[0].connect_calls[0]["client_id"], DEFAULT_CLIENT_ID)

    def test_does_not_call_build_market_order_or_submit_market_order(self) -> None:
        clients: list[DiagnosticsFakeClient] = []

        with patch(
            "ibkr_runtime_diagnostics.IBKRBrokerAdapter.build_market_order",
            side_effect=AssertionError("build_market_order called"),
        ) as build_market_order:
            with patch(
                "ibkr_runtime_diagnostics.IBKRBrokerAdapter.submit_market_order",
                side_effect=AssertionError("submit_market_order called"),
            ) as submit_market_order:
                run_ibkr_runtime_diagnostics(
                    timeout=0.5,
                    disconnect_timeout=0.05,
                    native_api_loader=fake_loader_for(clients),
                    print_output=False,
                )

        build_market_order.assert_not_called()
        submit_market_order.assert_not_called()

    def test_does_not_call_cancel_or_flatten_behavior(self) -> None:
        clients: list[DiagnosticsFakeClient] = []

        with patch(
            "ibkr_runtime_diagnostics.IBKRBrokerAdapter.submit_market_order",
            side_effect=AssertionError("flatten attempted"),
        ):
            result = run_ibkr_runtime_diagnostics(
                timeout=0.5,
                disconnect_timeout=0.05,
                native_api_loader=fake_loader_for(
                    clients,
                    open_order_qty="3",
                    position_qty="2",
                ),
                print_output=False,
            )

        self.assertEqual(result["broker_state"], "open_orders")
        self.assertEqual(clients[0].cancel_order_calls, [])
        self.assertEqual(clients[0].req_global_cancel_calls, 0)

    def test_disconnects_with_independent_cleanup_timeout(self) -> None:
        clients: list[DiagnosticsFakeClient] = []
        never_released = threading.Event()

        result = run_ibkr_runtime_diagnostics(
            timeout=0.5,
            disconnect_timeout=0.01,
            native_api_loader=fake_loader_for(
                clients,
                disconnect_event=never_released,
                release_on_disconnect=False,
            ),
            print_output=False,
        )

        self.assertEqual(clients[0].disconnect_calls, 1)
        self.assertEqual(
            result["disconnect_result"]["reason"],
            "runtime_thread_join_timeout",
        )
        self.assertEqual(result["disconnect_result"]["raw_error"]["timeout"], 0.01)

    def test_reports_open_orders_without_cleanup(self) -> None:
        clients: list[DiagnosticsFakeClient] = []

        result = run_ibkr_runtime_diagnostics(
            timeout=0.5,
            disconnect_timeout=0.05,
            native_api_loader=fake_loader_for(clients, open_order_qty="4"),
            print_output=False,
        )

        self.assertEqual(result["broker_state"], "open_orders")
        self.assertEqual(result["open_order_snapshot"]["open_buy_order_qty"], 4)
        self.assertEqual(clients[0].cancel_order_calls, [])

    def test_reports_non_flat_position_without_cleanup(self) -> None:
        clients: list[DiagnosticsFakeClient] = []

        result = run_ibkr_runtime_diagnostics(
            timeout=0.5,
            disconnect_timeout=0.05,
            native_api_loader=fake_loader_for(clients, position_qty="-2"),
            print_output=False,
        )

        self.assertEqual(result["broker_state"], "non_flat_position")
        self.assertEqual(result["position_snapshot"]["qty"], 2)
        self.assertEqual(clients[0].cancel_order_calls, [])

    def test_optional_execution_snapshot_uses_since_value_unchanged(self) -> None:
        clients: list[DiagnosticsFakeClient] = []
        since = "20260512 09:30:00"

        result = run_ibkr_runtime_diagnostics(
            timeout=0.5,
            disconnect_timeout=0.05,
            include_execution_snapshot=True,
            execution_since=since,
            native_api_loader=fake_loader_for(clients),
            print_output=False,
        )

        self.assertEqual(result["execution_snapshot"]["passed"], True)
        execution_filter = clients[0].req_executions_calls[0]["execution_filter"]
        self.assertEqual(execution_filter.time, since)

    def test_classifies_unknown_when_snapshot_failed(self) -> None:
        self.assertEqual(
            classify_broker_state(
                open_order_snapshot={"error": "TimeoutError"},
                position_snapshot={"qty": 0},
            ),
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()
