from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace

import runtime_visibility_provider_composer
from runtime_visibility_provider_composer import build_runtime_visibility_providers


class RuntimeVisibilityProviderComposerTests(unittest.TestCase):
    def test_composer_returns_empty_provider_list_by_default(self) -> None:
        self.assertEqual(build_runtime_visibility_providers(), [])

    def test_composer_returns_empty_provider_list_with_config_module(self) -> None:
        config_module = SimpleNamespace(
            OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED=True,
        )

        self.assertEqual(build_runtime_visibility_providers(config_module), [])

    def test_composer_does_not_import_ibkr_provider_or_diagnostics_modules(self) -> None:
        source = inspect.getsource(runtime_visibility_provider_composer)

        self.assertNotIn("ibkr_read_only_runtime_provider", source)
        self.assertNotIn("ibkr_runtime_diagnostics", source)
        self.assertNotIn("IBKRReadOnlyRuntimeProvider", source)
        self.assertNotIn("run_ibkr_runtime_diagnostics", source)


if __name__ == "__main__":
    unittest.main()
