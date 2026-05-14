from __future__ import annotations

import unittest

from runtime_visibility_orchestrator import build_runtime_visibility_summary


class FakeReadOnlyProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        provider_status: str = "enabled",
        enabled: bool = True,
        broker_state: str = "clean",
    ) -> None:
        self.provider_name = provider_name
        self.provider_status = provider_status
        self.enabled = enabled
        self.broker_state = broker_state
        self.read_calls = 0
        self.execution_like_calls = 0

    def read_broker_state(self):
        self.read_calls += 1
        return {
            "provider_status": self.provider_status,
            "enabled": self.enabled,
            "broker_state": self.broker_state,
        }

    def build_market_order(self):
        self.execution_like_calls += 1
        raise AssertionError("execution-like method must not be called")

    def submit_market_order(self):
        self.execution_like_calls += 1
        raise AssertionError("execution-like method must not be called")

    def cancel_order(self):
        self.execution_like_calls += 1
        raise AssertionError("execution-like method must not be called")

    def flatten(self):
        self.execution_like_calls += 1
        raise AssertionError("execution-like method must not be called")


class RaisingProvider:
    provider_name = "raising-provider"

    def read_broker_state(self):
        raise RuntimeError("provider failed")


class RuntimeVisibilityOrchestratorTests(unittest.TestCase):
    def test_no_providers_returns_clear_non_blocking_summary(self) -> None:
        result = build_runtime_visibility_summary([])

        self.assertEqual(
            result,
            {
                "runtime_visibility_reports": [],
                "runtime_visibility_blocking": False,
                "runtime_visibility_reason": "runtime_visibility_clear",
            },
        )

    def test_all_disabled_providers_returns_clear_non_blocking_summary(self) -> None:
        providers = [
            FakeReadOnlyProvider(
                provider_name="ibkr",
                provider_status="disabled",
                enabled=False,
                broker_state="unknown",
            )
        ]

        result = build_runtime_visibility_summary(providers)

        self.assertEqual(result["runtime_visibility_blocking"], False)
        self.assertEqual(result["runtime_visibility_reason"], "runtime_visibility_clear")
        self.assertEqual(result["runtime_visibility_reports"][0]["provider_status"], "disabled")

    def test_clean_provider_returns_clear_non_blocking_summary(self) -> None:
        providers = [FakeReadOnlyProvider(provider_name="ibkr", broker_state="clean")]

        result = build_runtime_visibility_summary(providers)

        self.assertEqual(result["runtime_visibility_blocking"], False)
        self.assertEqual(result["runtime_visibility_reason"], "runtime_visibility_clear")
        self.assertEqual(result["runtime_visibility_reports"][0]["broker_state"], "clean")

    def test_open_orders_provider_returns_blocking_summary(self) -> None:
        providers = [
            FakeReadOnlyProvider(provider_name="ibkr", broker_state="open_orders")
        ]

        result = build_runtime_visibility_summary(providers)

        self.assertEqual(result["runtime_visibility_blocking"], True)
        self.assertEqual(
            result["runtime_visibility_reason"],
            "ibkr:broker_state_open_orders",
        )

    def test_non_flat_position_provider_returns_blocking_summary(self) -> None:
        providers = [
            FakeReadOnlyProvider(
                provider_name="ibkr",
                broker_state="non_flat_position",
            )
        ]

        result = build_runtime_visibility_summary(providers)

        self.assertEqual(result["runtime_visibility_blocking"], True)
        self.assertEqual(
            result["runtime_visibility_reason"],
            "ibkr:broker_state_non_flat_position",
        )

    def test_provider_error_returns_blocking_summary(self) -> None:
        result = build_runtime_visibility_summary([RaisingProvider()])

        self.assertEqual(result["runtime_visibility_blocking"], True)
        self.assertEqual(
            result["runtime_visibility_reason"],
            "raising-provider:provider_exception",
        )
        self.assertEqual(result["runtime_visibility_reports"][0]["provider_status"], "error")

    def test_multiple_providers_report_all_results_and_first_blocking_reason(self) -> None:
        providers = [
            FakeReadOnlyProvider(
                provider_name="disabled",
                provider_status="disabled",
                enabled=False,
                broker_state="unknown",
            ),
            FakeReadOnlyProvider(provider_name="ibkr", broker_state="open_orders"),
            FakeReadOnlyProvider(
                provider_name="second",
                broker_state="non_flat_position",
            ),
        ]

        result = build_runtime_visibility_summary(providers)

        self.assertEqual(
            [
                report["provider_name"]
                for report in result["runtime_visibility_reports"]
            ],
            ["disabled", "ibkr", "second"],
        )
        self.assertEqual(result["runtime_visibility_blocking"], True)
        self.assertEqual(
            result["runtime_visibility_reason"],
            "ibkr:broker_state_open_orders",
        )

    def test_does_not_call_execution_like_methods(self) -> None:
        provider = FakeReadOnlyProvider(provider_name="ibkr", broker_state="clean")

        result = build_runtime_visibility_summary([provider])

        self.assertEqual(result["runtime_visibility_blocking"], False)
        self.assertEqual(provider.read_calls, 1)
        self.assertEqual(provider.execution_like_calls, 0)

    def test_output_shape_is_stable(self) -> None:
        provider = FakeReadOnlyProvider(provider_name="ibkr", broker_state="clean")

        result = build_runtime_visibility_summary([provider])

        self.assertEqual(
            list(result.keys()),
            [
                "runtime_visibility_reports",
                "runtime_visibility_blocking",
                "runtime_visibility_reason",
            ],
        )
        self.assertEqual(
            set(result["runtime_visibility_reports"][0].keys()),
            {
                "provider_name",
                "provider_status",
                "enabled",
                "broker_state",
                "blocking",
                "reason",
                "raw_diagnostics",
            },
        )


if __name__ == "__main__":
    unittest.main()
