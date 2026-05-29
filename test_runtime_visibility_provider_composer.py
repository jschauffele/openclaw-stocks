from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from runtime_visibility_provider_composer import build_runtime_visibility_providers


IBKR_MODULES = ("ibkr_read_only_runtime_provider", "ibkr_runtime_diagnostics")
FORBIDDEN_AUTHORITY_FIELDS = {
    "submit_approved",
    "submit_attempted",
    "cleanup_approved",
    "flatten",
    "sell",
    "cancel",
    "retry",
    "remediation",
    "safe_to_submit",
}


def drop_ibkr_modules() -> None:
    for module_name in IBKR_MODULES:
        sys.modules.pop(module_name, None)


def assert_ibkr_modules_not_loaded(test_case: unittest.TestCase) -> None:
    for module_name in IBKR_MODULES:
        test_case.assertNotIn(module_name, sys.modules)


def valid_ibkr_config(**overrides):
    fields = {
        "OPENCLAW_RUNTIME_VISIBILITY_ENABLED": True,
        "OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS": "ibkr_read_only",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED": True,
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE": "paper_localhost",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST": "localhost",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT": "4002",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID": "9234",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT": "1.25",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT": "0.75",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL": "MSFT",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS": "true",
        "OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE": "20260512 09:30:00",
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


class RuntimeVisibilityProviderComposerTests(unittest.TestCase):
    def test_composer_returns_empty_provider_list_by_default(self) -> None:
        drop_ibkr_modules()

        self.assertEqual(build_runtime_visibility_providers(), [])
        assert_ibkr_modules_not_loaded(self)

    def test_composer_returns_empty_provider_list_with_irrelevant_config(self) -> None:
        drop_ibkr_modules()
        config_module = SimpleNamespace(
            OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED=True,
        )

        self.assertEqual(build_runtime_visibility_providers(config_module), [])
        assert_ibkr_modules_not_loaded(self)

    def test_composer_returns_empty_provider_list_if_only_global_gate_enabled(
        self,
    ) -> None:
        drop_ibkr_modules()
        config_module = SimpleNamespace(
            OPENCLAW_RUNTIME_VISIBILITY_ENABLED=True,
        )

        self.assertEqual(build_runtime_visibility_providers(config_module), [])
        assert_ibkr_modules_not_loaded(self)

    def test_composer_returns_empty_provider_list_if_only_provider_allowlist_set(
        self,
    ) -> None:
        drop_ibkr_modules()
        config_module = SimpleNamespace(
            OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS="fake",
        )

        self.assertEqual(build_runtime_visibility_providers(config_module), [])
        assert_ibkr_modules_not_loaded(self)

    def test_composer_returns_empty_provider_list_for_each_missing_ibkr_gate(
        self,
    ) -> None:
        cases = [
            valid_ibkr_config(OPENCLAW_RUNTIME_VISIBILITY_ENABLED=False),
            valid_ibkr_config(OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS=""),
            valid_ibkr_config(OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED=False),
            valid_ibkr_config(OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE=""),
        ]

        for config_module in cases:
            with self.subTest(config=config_module):
                drop_ibkr_modules()
                self.assertEqual(build_runtime_visibility_providers(config_module), [])
                assert_ibkr_modules_not_loaded(self)

    def test_composer_returns_fake_provider_only_when_both_fake_gates_are_set(
        self,
    ) -> None:
        drop_ibkr_modules()
        config_module = SimpleNamespace(
            OPENCLAW_RUNTIME_VISIBILITY_ENABLED=True,
            OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS="fake",
        )

        providers = build_runtime_visibility_providers(config_module)

        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0].provider_name, "fake")
        self.assertEqual(
            providers[0].read_broker_state(),
            {
                "provider_status": "enabled",
                "enabled": True,
                "broker_state": "clean",
            },
        )
        assert_ibkr_modules_not_loaded(self)

    def test_fake_provider_can_report_blocking_state_for_tests(self) -> None:
        drop_ibkr_modules()
        config_module = SimpleNamespace(
            OPENCLAW_RUNTIME_VISIBILITY_ENABLED=True,
            OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS=["fake"],
            OPENCLAW_RUNTIME_VISIBILITY_FAKE_BROKER_STATE="open_orders",
        )

        providers = build_runtime_visibility_providers(config_module)

        self.assertEqual(providers[0].read_broker_state()["broker_state"], "open_orders")
        assert_ibkr_modules_not_loaded(self)

    def test_invalid_ibkr_guardrails_return_empty_without_importing_ibkr_modules(
        self,
    ) -> None:
        cases = [
            valid_ibkr_config(OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST="192.168.1.10"),
            valid_ibkr_config(OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT=7496),
            valid_ibkr_config(OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT=0),
            valid_ibkr_config(
                OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT=0
            ),
        ]

        for config_module in cases:
            with self.subTest(config=config_module):
                drop_ibkr_modules()
                factory_calls = []

                def factory(**kwargs):
                    factory_calls.append(kwargs)
                    return object()

                self.assertEqual(
                    build_runtime_visibility_providers(
                        config_module,
                        ibkr_provider_factory=factory,
                    ),
                    [],
                )
                self.assertEqual(factory_calls, [])
                assert_ibkr_modules_not_loaded(self)

    def test_all_ibkr_gates_valid_calls_injected_provider_factory(self) -> None:
        drop_ibkr_modules()
        config_module = valid_ibkr_config()
        factory_calls = []
        provider = object()

        def factory(**kwargs):
            factory_calls.append(kwargs)
            return provider

        result = build_runtime_visibility_providers(
            config_module,
            ibkr_provider_factory=factory,
        )

        self.assertEqual(result, [provider])
        self.assertEqual(len(factory_calls), 1)
        assert_ibkr_modules_not_loaded(self)

    def test_all_ibkr_gates_valid_passes_expected_config_to_injected_factory(
        self,
    ) -> None:
        drop_ibkr_modules()
        config_module = valid_ibkr_config()
        factory_calls = []

        def factory(**kwargs):
            factory_calls.append(kwargs)
            return object()

        build_runtime_visibility_providers(
            config_module,
            ibkr_provider_factory=factory,
        )

        self.assertEqual(
            factory_calls,
            [
                {
                    "enabled": True,
                    "host": "localhost",
                    "port": 4002,
                    "client_id": 9234,
                    "timeout": 1.25,
                    "disconnect_timeout": 0.75,
                    "symbol": "MSFT",
                    "include_executions": True,
                    "execution_since": "20260512 09:30:00",
                }
            ],
        )
        assert_ibkr_modules_not_loaded(self)

    def test_ibkr_read_only_injected_provider_path_is_report_only(self) -> None:
        drop_ibkr_modules()
        config_module = valid_ibkr_config(
            OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL="AAPL",
            OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS=False,
        )

        class InjectedReadOnlyProvider:
            provider_name = "ibkr_read_only"

            def read_broker_state(self):
                return {
                    "provider_status": "enabled",
                    "enabled": True,
                    "broker_state": "non_flat_position",
                    "position_snapshot": {
                        "found": True,
                        "symbol": "AAPL",
                        "qty": 1,
                        "side": "long",
                    },
                }

        factory_calls = []

        def factory(**kwargs):
            factory_calls.append(kwargs)
            return InjectedReadOnlyProvider()

        providers = build_runtime_visibility_providers(
            config_module,
            ibkr_provider_factory=factory,
        )

        self.assertEqual(len(providers), 1)
        provider = providers[0]
        self.assertEqual(provider.provider_name, "ibkr_read_only")
        self.assertEqual(provider.read_broker_state()["broker_state"], "non_flat_position")
        self.assertFalse(FORBIDDEN_AUTHORITY_FIELDS.intersection(factory_calls[0]))
        for field in FORBIDDEN_AUTHORITY_FIELDS:
            with self.subTest(field=field):
                self.assertFalse(hasattr(provider, field))
        for method_name in [
            "submit_market_order",
            "cancel_order",
            "flatten",
            "sell",
            "retry",
            "remediate",
        ]:
            with self.subTest(method=method_name):
                self.assertFalse(hasattr(provider, method_name))
        assert_ibkr_modules_not_loaded(self)


if __name__ == "__main__":
    unittest.main()
