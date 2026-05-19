from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from alpaca_broker_adapter import AlpacaBrokerAdapter
from ibkr_broker_adapter import IBKRBrokerAdapter
from broker_factory import SUPPORTED_BROKERS, create_broker_adapter
from ibkr_native_imports import IBKRNativeAPI


class FakeEClient:
    side_effect_calls: list[str] = []

    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper
        self.connect_calls = []
        self.run_calls = 0
        self.disconnect_calls = 0

    def connect(self, *args, **kwargs) -> None:
        self.connect_calls.append((args, kwargs))

    def run(self) -> None:
        self.run_calls += 1

    def disconnect(self) -> None:
        self.disconnect_calls += 1

    def isConnected(self) -> bool:
        return False

    def reqAccountSummary(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqAccountSummary")

    def reqPositionsMulti(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqPositionsMulti")

    def reqAllOpenOrders(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqAllOpenOrders")

    def reqExecutions(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("reqExecutions")

    def placeOrder(self, *args, **kwargs) -> None:
        self.side_effect_calls.append("placeOrder")


class FakeEWrapper:
    pass


class FakeContract:
    pass


class FakeOrder:
    pass


class FakeExecutionFilter:
    pass


def fake_native_api() -> IBKRNativeAPI:
    return IBKRNativeAPI(
        e_client=FakeEClient,
        e_wrapper=FakeEWrapper,
        contract=FakeContract,
        order=FakeOrder,
        execution_filter=FakeExecutionFilter,
    )


def ibkr_config(**overrides):
    values = {
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
    values.update(overrides)
    return SimpleNamespace(**values)


class BrokerFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeEClient.side_effect_calls = []

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
        with patch.dict(os.environ, {"OPENCLAW_BROKER": "ibkr"}, clear=True):
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

        self.assertNotIn("import main", source)
        self.assertNotIn("from main", source)

    def test_ibkr_rejection_does_not_require_tws_or_broker_calls(self) -> None:
        with (
            patch(
                "broker_factory.assemble_ibkr_runtime",
                side_effect=AssertionError("disabled IBKR must not assemble runtime"),
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

    def test_invalid_ibkr_config_rejects_before_adapter_construction(self) -> None:
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

        for overrides, message in cases:
            with self.subTest(overrides=overrides):
                invalid_config = ibkr_config(
                    OPENCLAW_IBKR_RUNTIME_ENABLED=True,
                    **overrides,
                )

                with patch(
                    "broker_factory.assemble_ibkr_runtime",
                    side_effect=AssertionError("invalid config must not assemble"),
                ):
                    with self.assertRaisesRegex(ValueError, message):
                        create_broker_adapter(
                            "ibkr",
                            alpaca_api_key="key",
                            alpaca_secret_key="secret",
                            ibkr_config_module=invalid_config,
                        )

    def test_enabled_fake_native_ibkr_factory_construction_has_no_side_effects(
        self,
    ) -> None:
        adapter = create_broker_adapter(
            "ibkr",
            alpaca_api_key="key",
            alpaca_secret_key="secret",
            ibkr_config_module=ibkr_config(OPENCLAW_IBKR_RUNTIME_ENABLED=True),
            ibkr_native_api=fake_native_api(),
        )

        self.assertIsInstance(adapter, IBKRBrokerAdapter)
        self.assertTrue(adapter.enabled)
        self.assertEqual(adapter.host, "127.0.0.1")
        self.assertEqual(adapter.port, 7497)
        self.assertEqual(adapter.client_id, 9107)
        self.assertIsNotNone(adapter.client)
        self.assertEqual(adapter.client.connect_calls, [])
        self.assertEqual(adapter.client.run_calls, 0)
        self.assertEqual(adapter.client.disconnect_calls, 0)
        self.assertEqual(FakeEClient.side_effect_calls, [])


if __name__ == "__main__":
    unittest.main()
