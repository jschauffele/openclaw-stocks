from __future__ import annotations

import unittest

from broker_interface import BrokerCapabilities
from ibkr_broker_adapter import IBKRBrokerAdapter


class IBKRBrokerAdapterTests(unittest.TestCase):
    def test_capabilities_return_expected_ibkr_metadata(self) -> None:
        adapter = IBKRBrokerAdapter()

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

    def test_skeleton_methods_fail_explicitly(self) -> None:
        adapter = IBKRBrokerAdapter()

        expected_message = "IBKR adapter skeleton only; not runtime-enabled"

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
                with self.assertRaisesRegex(NotImplementedError, expected_message):
                    getattr(adapter, method_name)(*args)


if __name__ == "__main__":
    unittest.main()
