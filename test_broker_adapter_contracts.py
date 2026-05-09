from __future__ import annotations

import unittest
from types import SimpleNamespace

from alpaca_broker_adapter import AlpacaBrokerAdapter
from broker_interface import (
    BrokerAccountState,
    BrokerCapabilities,
    BrokerLifecycleResult,
    BrokerOpenOrderState,
    BrokerOrderResult,
    BrokerPositionState,
)
from ibkr_broker_adapter import IBKRBrokerAdapter


class ContractFakeClient:
    def get_account(self):
        return SimpleNamespace(buying_power="100.00")

    def get_open_position(self, symbol: str):
        return SimpleNamespace(qty="3")

    def get_orders(self, filter):
        return [SimpleNamespace(id="1", qty="2")]

    def submit_order(self, order):
        return SimpleNamespace(id="order-1", status="accepted")


class BrokerAdapterContractTests(unittest.TestCase):
    def assert_common_surface(self, adapter) -> None:
        for method_name in [
            "get_capabilities",
            "connect",
            "health_check",
            "disconnect",
            "get_account_buying_power",
            "get_existing_position",
            "get_open_buy_order_qty",
            "build_market_order",
            "submit_market_order",
            "normalize_order_response",
        ]:
            self.assertTrue(hasattr(adapter, method_name), method_name)

    def test_alpaca_adapter_exposes_expected_broker_neutral_surface(self) -> None:
        adapter = AlpacaBrokerAdapter(ContractFakeClient())
        self.assert_common_surface(adapter)

        self.assertEqual(
            adapter.connect(timeout_seconds=0.5),
            BrokerLifecycleResult(
                broker_name="alpaca",
                operation="connect",
                passed=True,
                reason="alpaca_lifecycle_noop",
                message="Alpaca lifecycle is a no-op in the adapter boundary",
                connected=True,
                retryable=False,
                elapsed_ms=0,
                raw_error=None,
            ),
        )
        self.assertEqual(
            adapter.health_check(timeout_seconds=0.5),
            BrokerLifecycleResult(
                broker_name="alpaca",
                operation="health_check",
                passed=True,
                reason="alpaca_lifecycle_noop",
                message="Alpaca lifecycle is a no-op in the adapter boundary",
                connected=True,
                retryable=False,
                elapsed_ms=0,
                raw_error=None,
            ),
        )
        self.assertEqual(
            adapter.disconnect(timeout_seconds=0.5),
            BrokerLifecycleResult(
                broker_name="alpaca",
                operation="disconnect",
                passed=True,
                reason="alpaca_lifecycle_noop",
                message="Alpaca lifecycle is a no-op in the adapter boundary",
                connected=False,
                retryable=False,
                elapsed_ms=0,
                raw_error=None,
            ),
        )

        self.assertEqual(
            adapter.get_capabilities(),
            BrokerCapabilities(
                broker_name="alpaca",
                supports_market_orders=True,
                supports_account_read=True,
                supports_positions_read=True,
                supports_open_orders_read=True,
                supports_paper_trading=True,
                lifecycle_async=False,
            ),
        )
        account_state = adapter.get_account_buying_power()
        self.assertEqual(
            account_state,
            BrokerAccountState(
                broker_name="alpaca",
                buying_power=100.0,
                raw_account=account_state.raw_account,
            ),
        )
        self.assertEqual(
            adapter.get_existing_position("AAPL"),
            BrokerPositionState(
                broker_name="alpaca",
                found=True,
                qty=3,
                raw_qty="3",
                side="long",
                reason="position_found",
            ),
        )
        self.assertEqual(
            adapter.get_open_buy_order_qty("AAPL"),
            BrokerOpenOrderState(
                broker_name="alpaca",
                passed=True,
                open_buy_order_qty=2,
                open_buy_order_count=1,
                reason="open_buy_orders_loaded",
            ),
        )

        response = SimpleNamespace(id=123, status="accepted")
        normalized = adapter.normalize_order_response(response)

        self.assertEqual(
            normalized,
            BrokerOrderResult(
                broker_name="alpaca",
                order_id="123",
                order_status="accepted",
                broker_status="accepted",
                is_terminal=False,
                raw_response=response,
            ),
        )
        self.assertIs(normalized.raw_response, response)

        submitted = adapter.submit_market_order(object())
        self.assertEqual(
            submitted,
            BrokerOrderResult(
                broker_name="alpaca",
                order_id="order-1",
                order_status="accepted",
                broker_status="accepted",
                is_terminal=False,
                raw_response=submitted.raw_response,
            ),
        )

    def test_ibkr_lifecycle_only_adapter_exposes_expected_broker_neutral_surface(
        self,
    ) -> None:
        adapter = IBKRBrokerAdapter()
        self.assert_common_surface(adapter)

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
        self.assertEqual(
            adapter.health_check(timeout_seconds=0.5),
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

        for method_name in ["connect", "disconnect"]:
            with self.subTest(lifecycle_method=method_name):
                with self.assertRaisesRegex(
                    NotImplementedError,
                    "IBKR adapter skeleton only; not runtime-enabled",
                ):
                    getattr(adapter, method_name)(timeout_seconds=0.5)

        for method_name, args in [
            ("get_account_buying_power", ()),
            ("get_existing_position", ("AAPL",)),
            ("get_open_buy_order_qty", ("AAPL",)),
            ("build_market_order", ("AAPL", 1)),
            ("submit_market_order", (object(),)),
            ("normalize_order_response", (object(),)),
        ]:
            with self.subTest(method=method_name):
                with self.assertRaisesRegex(
                    NotImplementedError,
                    "IBKR adapter skeleton only; not runtime-enabled",
                ):
                    getattr(adapter, method_name)(*args)


if __name__ == "__main__":
    unittest.main()
