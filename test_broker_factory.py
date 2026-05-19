from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from alpaca_broker_adapter import AlpacaBrokerAdapter
from broker_factory import SUPPORTED_BROKERS, create_broker_adapter


class BrokerFactoryTests(unittest.TestCase):
    def test_supported_brokers_remains_alpaca_only(self) -> None:
        self.assertEqual(SUPPORTED_BROKERS, {"alpaca"})

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

    def test_ibkr_runtime_config_presence_does_not_enable_factory_support(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENCLAW_BROKER": "ibkr",
                "OPENCLAW_IBKR_RUNTIME_ENABLED": "true",
                "OPENCLAW_IBKR_RUNTIME_MODE": "paper_localhost",
                "OPENCLAW_IBKR_RUNTIME_HOST": "127.0.0.1",
                "OPENCLAW_IBKR_RUNTIME_PORT": "7497",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Unsupported OPENCLAW_BROKER='ibkr'; supported brokers: alpaca",
            ):
                create_broker_adapter(
                    os.environ["OPENCLAW_BROKER"],
                    alpaca_api_key="key",
                    alpaca_secret_key="secret",
                )

    def test_broker_factory_does_not_import_ibkr_runtime_authority(self) -> None:
        source = Path(__file__).with_name("broker_factory.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("ibkr_runtime_config", source)
        self.assertNotIn("ibkr_runtime_assembly", source)
        self.assertNotIn("assemble_ibkr_runtime", source)
        self.assertNotIn("build_ibkr_runtime_assembly_config", source)
        self.assertNotIn("load_ibkr_native_api", source)

    def test_ibkr_rejection_does_not_require_tws_or_broker_calls(self) -> None:
        with (
            patch(
                "ibkr_native_imports.load_ibkr_native_api",
                side_effect=AssertionError("factory rejection must not load ibapi"),
            ),
            patch(
                "broker_factory.create_trading_client",
                side_effect=AssertionError("IBKR rejection must not call Alpaca"),
            ),
        ):
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
