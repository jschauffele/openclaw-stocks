from __future__ import annotations

import unittest
from unittest.mock import patch

from alpaca_broker_adapter import AlpacaBrokerAdapter
from broker_factory import create_broker_adapter


class BrokerFactoryTests(unittest.TestCase):
    def test_alpaca_broker_selection_returns_alpaca_adapter(self) -> None:
        fake_client = object()

        with patch("broker_factory.create_trading_client", return_value=fake_client):
            adapter = create_broker_adapter(
                "alpaca",
                alpaca_api_key="key",
                alpaca_secret_key="secret",
            )

        self.assertIsInstance(adapter, AlpacaBrokerAdapter)
        self.assertIs(adapter.client, fake_client)

    def test_alpaca_broker_selection_is_case_and_whitespace_insensitive(self) -> None:
        fake_client = object()

        with patch("broker_factory.create_trading_client", return_value=fake_client):
            adapter = create_broker_adapter(
                " Alpaca ",
                alpaca_api_key="key",
                alpaca_secret_key="secret",
            )

        self.assertIsInstance(adapter, AlpacaBrokerAdapter)
        self.assertIs(adapter.client, fake_client)

    def test_unsupported_broker_fails_explicitly(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported OPENCLAW_BROKER='ibkr'; supported brokers: alpaca",
        ):
            create_broker_adapter(
                "ibkr",
                alpaca_api_key="key",
                alpaca_secret_key="secret",
            )

    def test_openclaw_broker_ibkr_is_not_runtime_enabled_yet(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported OPENCLAW_BROKER='ibkr'; supported brokers: alpaca",
        ):
            create_broker_adapter(
                "ibkr",
                alpaca_api_key="key",
                alpaca_secret_key="secret",
            )


if __name__ == "__main__":
    unittest.main()
