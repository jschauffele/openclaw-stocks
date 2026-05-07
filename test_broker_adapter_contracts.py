from __future__ import annotations

import unittest
from types import SimpleNamespace

from alpaca_broker_adapter import AlpacaBrokerAdapter
from broker_interface import BrokerCapabilities
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

        response = SimpleNamespace(id=123, status="accepted")
        normalized = adapter.normalize_order_response(response)

        self.assertEqual(
            normalized,
            {
                "broker_name": "alpaca",
                "order_id": "123",
                "order_status": "accepted",
                "broker_status": "accepted",
                "is_terminal": False,
                "raw_response": response,
            },
        )
        self.assertIs(normalized["raw_response"], response)

    def test_ibkr_skeleton_exposes_expected_broker_neutral_surface(self) -> None:
        adapter = IBKRBrokerAdapter()
        self.assert_common_surface(adapter)

        self.assertEqual(
            adapter.get_capabilities(),
            BrokerCapabilities(
                broker_name="ibkr",
                supports_market_orders=False,
                supports_account_read=False,
                supports_positions_read=False,
                supports_open_orders_read=False,
                supports_paper_trading=True,
                lifecycle_async=True,
            ),
        )

        for method_name, args in [
            ("connect", ()),
            ("health_check", ()),
            ("disconnect", ()),
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
