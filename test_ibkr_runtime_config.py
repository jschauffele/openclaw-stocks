from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import config
from broker_factory import SUPPORTED_BROKERS, create_broker_adapter
from ibkr_runtime_assembly import IBKRRuntimeAssemblyConfig, assemble_ibkr_runtime
from ibkr_runtime_config import build_ibkr_runtime_assembly_config


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

    def test_default_config_maps_to_disabled_assembly_config(self) -> None:
        self.refresh_with({})

        assembly_config = build_ibkr_runtime_assembly_config(config)

        self.assertIsInstance(assembly_config, IBKRRuntimeAssemblyConfig)
        self.assertFalse(assembly_config.enabled)
        self.assertEqual(assembly_config.host, "127.0.0.1")
        self.assertEqual(assembly_config.port, 7497)
        self.assertEqual(assembly_config.client_id, 9107)
        self.assertEqual(assembly_config.position_account, "")
        self.assertEqual(assembly_config.position_model_code, "")
        self.assertIsNone(assembly_config.order_id_start)
        self.assertEqual(assembly_config.connect_timeout_seconds, 5.0)

    def test_enabled_runtime_values_map_to_assembly_config_without_routing(self) -> None:
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
            }
        )

        assembly_config = build_ibkr_runtime_assembly_config(config)

        self.assertTrue(assembly_config.enabled)
        self.assertEqual(assembly_config.host, "localhost")
        self.assertEqual(assembly_config.port, 4002)
        self.assertEqual(assembly_config.client_id, 9123)
        self.assertEqual(assembly_config.position_account, "DU1234567")
        self.assertEqual(assembly_config.position_model_code, "MODEL")
        self.assertEqual(assembly_config.order_id_start, 1000)
        self.assertEqual(assembly_config.connect_timeout_seconds, 6.5)
        self.assertEqual(config.OPENCLAW_BROKER, "alpaca")

    def test_mapping_ignores_read_only_visibility_config(self) -> None:
        self.refresh_with(
            {
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED": "true",
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST": "example.com",
                "OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT": "7496",
            }
        )

        assembly_config = build_ibkr_runtime_assembly_config(config)

        self.assertFalse(assembly_config.enabled)
        self.assertEqual(assembly_config.host, "127.0.0.1")
        self.assertEqual(assembly_config.port, 7497)

    def test_mapping_fails_closed_for_invalid_config_module_values(self) -> None:
        valid = {
            "OPENCLAW_IBKR_RUNTIME_ENABLED": False,
            "OPENCLAW_IBKR_RUNTIME_MODE": "paper_localhost",
            "OPENCLAW_IBKR_RUNTIME_HOST": "127.0.0.1",
            "OPENCLAW_IBKR_RUNTIME_PORT": 7497,
            "OPENCLAW_IBKR_RUNTIME_CLIENT_ID": 9107,
            "OPENCLAW_IBKR_RUNTIME_CONNECT_TIMEOUT_SECONDS": 5.0,
            "OPENCLAW_IBKR_RUNTIME_ACCOUNT": "",
            "OPENCLAW_IBKR_RUNTIME_MODEL_CODE": "",
            "OPENCLAW_IBKR_RUNTIME_ORDER_ID_START": None,
        }
        cases = (
            (
                {"OPENCLAW_IBKR_RUNTIME_MODE": "live"},
                "OPENCLAW_IBKR_RUNTIME_MODE must be paper_localhost",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_HOST": "example.com"},
                "OPENCLAW_IBKR_RUNTIME_HOST must be localhost",
            ),
            (
                {"OPENCLAW_IBKR_RUNTIME_PORT": 7496},
                "OPENCLAW_IBKR_RUNTIME_PORT must be a paper port",
            ),
        )

        for override, message in cases:
            with self.subTest(override=override):
                config_module = SimpleNamespace(**(valid | override))

                with self.assertRaisesRegex(ValueError, message):
                    build_ibkr_runtime_assembly_config(config_module)

    def test_mapping_helper_has_no_runtime_or_routing_authority(self) -> None:
        self.refresh_with({"OPENCLAW_IBKR_RUNTIME_ENABLED": "true"})

        with patch(
            "ibkr_native_imports.load_ibkr_native_api",
            side_effect=AssertionError("mapping must not load ibapi"),
        ):
            assembly_config = build_ibkr_runtime_assembly_config(config)

        self.assertTrue(assembly_config.enabled)
        self.assertEqual(SUPPORTED_BROKERS, {"alpaca"})

    def test_default_mapping_feeds_disabled_assembly_without_authority(self) -> None:
        self.refresh_with({})

        def fail_loader():
            raise AssertionError("disabled assembly must not load native IBKR API")

        assembly_config = build_ibkr_runtime_assembly_config(config)
        assembly = assemble_ibkr_runtime(
            assembly_config,
            native_api_loader=fail_loader,
        )

        self.assertIsInstance(assembly_config, IBKRRuntimeAssemblyConfig)
        self.assertFalse(assembly_config.enabled)
        self.assertFalse(assembly.enabled)
        self.assertIsNone(assembly.native_api)
        self.assertIsNone(assembly.native_bundle)
        self.assertIsNone(assembly.runtime_coordinator)
        self.assertIsNone(assembly.adapter.client)
        self.assertIsNone(assembly.adapter.native_api)
        self.assertIsNone(assembly.adapter.coordinator)

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported OPENCLAW_BROKER='ibkr'; supported brokers: alpaca",
        ):
            create_broker_adapter(
                "ibkr",
                alpaca_api_key="key",
                alpaca_secret_key="secret",
            )

        main_source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
        self.assertNotIn("ibkr_runtime_config", main_source)
        self.assertNotIn("ibkr_runtime_assembly", main_source)
        self.assertNotIn("build_ibkr_runtime_assembly_config", main_source)
        self.assertNotIn("assemble_ibkr_runtime", main_source)

    def test_mapping_module_stays_detached_from_runtime_authority(self) -> None:
        source = Path(__file__).with_name("ibkr_runtime_config.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("assemble_ibkr_runtime", source)
        self.assertNotIn("load_ibkr_native_api", source)
        self.assertNotIn("create_broker_adapter", source)
        self.assertNotIn("SUPPORTED_BROKERS", source)
        self.assertNotIn("import main", source)


if __name__ == "__main__":
    unittest.main()
