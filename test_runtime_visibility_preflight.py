from __future__ import annotations

import unittest

from runtime_visibility_preflight import (
    build_runtime_visibility_report,
    run_runtime_visibility_preflight,
)


class FakeReadOnlyProvider:
    def __init__(
        self,
        *,
        provider_name: str = "fake",
        diagnostics: dict[str, object] | None = None,
        raises: Exception | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.diagnostics = diagnostics or {}
        self.raises = raises
        self.read_calls = 0
        self.runtime_diagnostics_calls = 0
        self.execution_like_calls = 0

    def read_broker_state(self):
        self.read_calls += 1
        if self.raises is not None:
            raise self.raises
        return self.diagnostics

    def get_runtime_diagnostics(self):
        self.runtime_diagnostics_calls += 1
        raise AssertionError("read_broker_state should be preferred")

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


class RuntimeDiagnosticsOnlyProvider:
    provider_name = "runtime-only"

    def __init__(self, diagnostics: dict[str, object]) -> None:
        self.diagnostics = diagnostics
        self.runtime_diagnostics_calls = 0

    def get_runtime_diagnostics(self):
        self.runtime_diagnostics_calls += 1
        return self.diagnostics


def diagnostics(
    *,
    provider_status: str = "enabled",
    enabled: bool = True,
    broker_state: str = "clean",
) -> dict[str, object]:
    return {
        "provider_status": provider_status,
        "enabled": enabled,
        "broker_state": broker_state,
        "connection_result": None,
    }


class RuntimeVisibilityPreflightTests(unittest.TestCase):
    def test_disabled_provider_produces_non_blocking_report(self) -> None:
        provider = FakeReadOnlyProvider(
            diagnostics=diagnostics(
                provider_status="disabled",
                enabled=False,
                broker_state="unknown",
            )
        )

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(report["provider_name"], "fake")
        self.assertEqual(report["provider_status"], "disabled")
        self.assertEqual(report["enabled"], False)
        self.assertEqual(report["broker_state"], "unknown")
        self.assertEqual(report["blocking"], False)
        self.assertEqual(report["reason"], "provider_disabled")

    def test_clean_enabled_provider_produces_non_blocking_report(self) -> None:
        provider = FakeReadOnlyProvider(diagnostics=diagnostics(broker_state="clean"))

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(report["provider_status"], "enabled")
        self.assertEqual(report["enabled"], True)
        self.assertEqual(report["broker_state"], "clean")
        self.assertEqual(report["blocking"], False)
        self.assertEqual(report["reason"], "broker_state_clean")

    def test_open_orders_produces_blocking_report(self) -> None:
        provider = FakeReadOnlyProvider(
            diagnostics=diagnostics(broker_state="open_orders")
        )

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(report["broker_state"], "open_orders")
        self.assertEqual(report["blocking"], True)
        self.assertEqual(report["reason"], "broker_state_open_orders")

    def test_non_flat_position_produces_blocking_report(self) -> None:
        provider = FakeReadOnlyProvider(
            diagnostics=diagnostics(broker_state="non_flat_position")
        )

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(report["broker_state"], "non_flat_position")
        self.assertEqual(report["blocking"], True)
        self.assertEqual(report["reason"], "broker_state_non_flat_position")

    def test_unknown_produces_blocking_report(self) -> None:
        provider = FakeReadOnlyProvider(
            diagnostics=diagnostics(broker_state="unknown")
        )

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(report["broker_state"], "unknown")
        self.assertEqual(report["blocking"], True)
        self.assertEqual(report["reason"], "broker_state_unknown")

    def test_provider_exception_produces_blocking_error_report(self) -> None:
        provider = FakeReadOnlyProvider(raises=TimeoutError("provider timed out"))

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(report["provider_status"], "error")
        self.assertEqual(report["broker_state"], "unknown")
        self.assertEqual(report["blocking"], True)
        self.assertEqual(report["reason"], "provider_exception")
        self.assertEqual(
            report["raw_diagnostics"]["error"],
            {"type": "TimeoutError", "message": "provider timed out"},
        )

    def test_supports_multiple_providers(self) -> None:
        providers = [
            FakeReadOnlyProvider(
                provider_name="disabled",
                diagnostics=diagnostics(
                    provider_status="disabled",
                    enabled=False,
                    broker_state="unknown",
                ),
            ),
            FakeReadOnlyProvider(
                provider_name="ibkr",
                diagnostics=diagnostics(broker_state="open_orders"),
            ),
        ]

        reports = run_runtime_visibility_preflight(providers)

        self.assertEqual([report["provider_name"] for report in reports], ["disabled", "ibkr"])
        self.assertEqual([report["blocking"] for report in reports], [False, True])

    def test_never_calls_execution_like_methods(self) -> None:
        provider = FakeReadOnlyProvider(diagnostics=diagnostics(broker_state="clean"))

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(report["blocking"], False)
        self.assertEqual(provider.read_calls, 1)
        self.assertEqual(provider.runtime_diagnostics_calls, 0)
        self.assertEqual(provider.execution_like_calls, 0)

    def test_uses_read_broker_state_if_available(self) -> None:
        provider = FakeReadOnlyProvider(diagnostics=diagnostics(broker_state="clean"))

        build_runtime_visibility_report(provider)

        self.assertEqual(provider.read_calls, 1)
        self.assertEqual(provider.runtime_diagnostics_calls, 0)

    def test_falls_back_to_get_runtime_diagnostics_when_read_broker_state_absent(
        self,
    ) -> None:
        provider = RuntimeDiagnosticsOnlyProvider(
            diagnostics=diagnostics(broker_state="clean")
        )

        report = build_runtime_visibility_report(provider).to_dict()

        self.assertEqual(provider.runtime_diagnostics_calls, 1)
        self.assertEqual(report["provider_name"], "runtime-only")
        self.assertEqual(report["blocking"], False)


if __name__ == "__main__":
    unittest.main()
