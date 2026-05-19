from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import config
from broker_factory import create_broker_adapter


IBKR_RUNTIME_ENV_NAMES = (
    "OPENCLAW_IBKR_RUNTIME_ENABLED",
    "OPENCLAW_IBKR_RUNTIME_MODE",
    "OPENCLAW_IBKR_RUNTIME_HOST",
    "OPENCLAW_IBKR_RUNTIME_PORT",
    "OPENCLAW_IBKR_RUNTIME_CLIENT_ID",
    "OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS",
    "OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS",
    "OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS",
    "OPENCLAW_IBKR_RUNTIME_ACCOUNT",
    "OPENCLAW_IBKR_RUNTIME_MODEL_CODE",
    "OPENCLAW_IBKR_RUNTIME_ORDER_ID_START",
)


class IBKRRuntimeConfigTests(unittest.TestCase):
    def tearDown(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config.refresh_config_from_env()

    def refresh_with(self, env: dict[str, str]) -> None:
        with patch.dict(os.environ, env, clear=True):
            config.refresh_config_from_env()

    def test_defaults_are_disabled_paper_localhost_only(self) -> None:
        self.refresh_with({})

        self.assertFalse(config.OPENCLAW_IBKR_RUNTIME_ENABLED)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_MODE, "paper_localhost")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_HOST, "127.0.0.1")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_PORT, 7497)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_CLIENT_ID, 9107)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS, 5.0)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS, 2.0)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS, 5.0)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_ACCOUNT, "")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_MODEL_CODE, "")
        self.assertIsNone(config.OPENCLAW_IBKR_RUNTIME_ORDER_ID_START)

    def test_valid_runtime_overrides_remain_separate_from_alpaca_config(self) -> None:
        self.refresh_with(
            {
                "OPENCLAW_IBKR_RUNTIME_ENABLED": "true",
                "OPENCLAW_IBKR_RUNTIME_MODE": "paper_localhost",
                "OPENCLAW_IBKR_RUNTIME_HOST": "localhost",
                "OPENCLAW_IBKR_RUNTIME_PORT": "4002",
                "OPENCLAW_IBKR_RUNTIME_CLIENT_ID": "9123",
                "OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS": "6.5",
                "OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS": "3.5",
                "OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS": "7.5",
                "OPENCLAW_IBKR_RUNTIME_ACCOUNT": "DU1234567",
                "OPENCLAW_IBKR_RUNTIME_MODEL_CODE": "MODEL",
                "OPENCLAW_IBKR_RUNTIME_ORDER_ID_START": "1000",
                "ALPACA_API_KEY": "alpaca-key",
                "ALPACA_SECRET_KEY": "alpaca-secret",
                "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
            }
        )

        self.assertTrue(config.OPENCLAW_IBKR_RUNTIME_ENABLED)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_HOST, "localhost")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_PORT, 4002)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_CLIENT_ID, 9123)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS, 6.5)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS, 3.5)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS, 7.5)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_ACCOUNT, "DU1234567")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_MODEL_CODE, "MODEL")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_ORDER_ID_START, 1000)
        self.assertEqual(config.ALPACA_API_KEY, "alpaca-key")
        self.assertEqual(config.ALPACA_SECRET_KEY, "alpaca-secret")
        self.assertEqual(
            config.ALPACA_BASE_URL,
            "https://paper-api.alpaca.markets",
        )

    def test_runtime_config_stays_separate_from_read_only_visibility_config(self) -> None:
        self.refresh_with(
            {
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED": "true",
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST": "example.com",
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT": "7496",
            }
        )

        self.assertFalse(config.OPENCLAW_IBKR_RUNTIME_ENABLED)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_HOST, "127.0.0.1")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_PORT, 7497)

    def test_config_presence_does_not_enable_ibkr_broker_selection(self) -> None:
        self.refresh_with(
            {
                "OPENCLAW_IBKR_RUNTIME_ENABLED": "true",
                "OPENCLAW_IBKR_RUNTIME_MODE": "paper_localhost",
                "OPENCLAW_IBKR_RUNTIME_HOST": "127.0.0.1",
                "OPENCLAW_IBKR_RUNTIME_PORT": "7497",
            }
        )

        self.assertEqual(config.OPENCLAW_BROKER, "alpaca")
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported OPENCLAW_BROKER='ibkr'; supported brokers: alpaca",
        ):
            create_broker_adapter(
                "ibkr",
                alpaca_api_key="key",
                alpaca_secret_key="secret",
            )

    def test_invalid_runtime_values_fail_closed(self) -> None:
        cases = (
            (
                {"OPENCLAW_IBKR_RUNTIME_MODE": "live"},
                "OPENCLAW_IBKR_RUNTIME_MODE must be paper_localhost",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_HOST": "192.168.1.10"},
                "OPENCLAW_IBKR_RUNTIME_HOST must be localhost",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_PORT": "7496"},
                "OPENCLAW_IBKR_RUNTIME_PORT must be a paper port",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_PORT": "not-a-port"},
                "OPENCLAW_IBKR_RUNTIME_PORT must be an integer",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_CLIENT_ID": "0"},
                "OPENCLAW_IBKR_RUNTIME_CLIENT_ID must be positive",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS": "0"},
                "OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS must be positive",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS": "-1"},
                "OPENCLAW_IBKR_RUNTIME_DISCONNECT_TIMEOUT_SECONDS must be positive",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS": "0"},
                "OPENCLAW_IBKR_RUNTIME_SUBMIT_TIMEOUT_SECONDS must be positive",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_ORDER_ID_START": "0"},
                "OPENCLAW_IBKR_RUNTIME_ORDER_ID_START must be positive",
            ),
        )

        for env, message in cases:
            with self.subTest(env=env):
                with patch.dict(os.environ, env, clear=True):
                    with self.assertRaisesRegex(ValueError, message):
                        config.refresh_config_from_env()

    def test_runtime_config_names_are_explicitly_namespaced(self) -> None:
        for name in IBKR_RUNTIME_ENV_NAMES:
            with self.subTest(name=name):
                self.assertTrue(name.startswith("OPENCLAW_IBKR_RUNTIME_"))
                self.assertFalse(name.startswith("OPENCLAW_IBKR_RUNTIME_VISIBILITY_"))


if __name__ == "__main__":
    unittest.main()
