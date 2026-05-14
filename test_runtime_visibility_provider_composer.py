from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace

import runtime_visibility_provider_composer
from runtime_visibility_provider_composer import build_runtime_visibility_providers


class RuntimeVisibilityProviderComposerTests(unittest.TestCase):
    def test_composer_returns_empty_provider_list_by_default(self) -> None:
        self.assertEqual(build_runtime_visibility_providers(), [])

    def test_composer_returns_empty_provider_list_with_irrelevant_config(self) -> None:
        config_module = SimpleNamespace(
            OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED=True,
        )

        self.assertEqual(build_runtime_visibility_providers(config_module), [])

    def test_composer_returns_empty_provider_list_if_only_global_gate_enabled(
        self,
    ) -> None:
        config_module = SimpleNamespace(
            OPENCLAW_RUNTIME_VISIBILITY_ENABLED=True,
        )

        self.assertEqual(build_runtime_visibility_providers(config_module), [])

    def test_composer_returns_empty_provider_list_if_only_provider_allowlist_set(
        self,
    ) -> None:
        config_module = SimpleNamespace(
            OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS="fake",
        )

        self.assertEqual(build_runtime_visibility_providers(config_module), [])

    def test_composer_returns_fake_provider_only_when_both_fake_gates_are_set(
        self,
    ) -> None:
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

    def test_fake_provider_can_report_blocking_state_for_tests(self) -> None:
        config_module = SimpleNamespace(
            OPENCLAW_RUNTIME_VISIBILITY_ENABLED=True,
            OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS=["fake"],
            OPENCLAW_RUNTIME_VISIBILITY_FAKE_BROKER_STATE="open_orders",
        )

        providers = build_runtime_visibility_providers(config_module)

        self.assertEqual(providers[0].read_broker_state()["broker_state"], "open_orders")

    def test_composer_does_not_import_ibkr_provider_or_diagnostics_modules(self) -> None:
        source = inspect.getsource(runtime_visibility_provider_composer)

        self.assertNotIn("ibkr_read_only_runtime_provider", source)
        self.assertNotIn("ibkr_runtime_diagnostics", source)
        self.assertNotIn("IBKRReadOnlyRuntimeProvider", source)
        self.assertNotIn("run_ibkr_runtime_diagnostics", source)


if __name__ == "__main__":
    unittest.main()
