from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

import manual_ibkr_read_only_runtime_visibility_smoke as smoke


class ManualIBKRReadOnlyRuntimeVisibilitySmokeTests(unittest.TestCase):
    def test_builds_explicit_guarded_config(self) -> None:
        config = smoke.build_manual_ibkr_read_only_runtime_visibility_config(
            host="localhost",
            port=4002,
            timeout=1.25,
            disconnect_timeout=0.75,
            client_id=9234,
            symbol="MSFT",
            include_executions=True,
            execution_since="20260512 09:30:00",
        )

        self.assertEqual(config.OPENCLAW_RUNTIME_VISIBILITY_ENABLED, True)
        self.assertEqual(
            config.OPENCLAW_RUNTIME_VISIBILITY_PROVIDERS,
            "ibkr_read_only",
        )
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_ENABLED, True)
        self.assertEqual(
            config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_MODE,
            "paper_localhost",
        )
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_HOST, "localhost")
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_PORT, 4002)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_CLIENT_ID, 9234)
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_TIMEOUT, 1.25)
        self.assertEqual(
            config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_DISCONNECT_TIMEOUT,
            0.75,
        )
        self.assertEqual(config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_SYMBOL, "MSFT")
        self.assertEqual(
            config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_INCLUDE_EXECUTIONS,
            True,
        )
        self.assertEqual(
            config.OPENCLAW_IBKR_RUNTIME_VISIBILITY_EXECUTION_SINCE,
            "20260512 09:30:00",
        )

    def test_rejects_non_localhost_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "localhost"):
            smoke.build_manual_ibkr_read_only_runtime_visibility_config(
                host="192.168.1.10",
                port=7497,
                timeout=1.0,
                disconnect_timeout=1.0,
            )

    def test_rejects_non_paper_port(self) -> None:
        with self.assertRaisesRegex(ValueError, "paper port"):
            smoke.build_manual_ibkr_read_only_runtime_visibility_config(
                host="127.0.0.1",
                port=7496,
                timeout=1.0,
                disconnect_timeout=1.0,
            )

    def test_rejects_non_positive_timeouts(self) -> None:
        cases = [
            {"timeout": 0.0, "disconnect_timeout": 1.0, "message": "timeout > 0"},
            {
                "timeout": 1.0,
                "disconnect_timeout": 0.0,
                "message": "disconnect_timeout > 0",
            },
        ]

        for case in cases:
            with self.subTest(case=case):
                with self.assertRaisesRegex(ValueError, case["message"]):
                    smoke.build_manual_ibkr_read_only_runtime_visibility_config(
                        host="127.0.0.1",
                        port=7497,
                        timeout=case["timeout"],
                        disconnect_timeout=case["disconnect_timeout"],
                    )

    def test_run_uses_injected_builders_and_prints_structured_summary_only(
        self,
    ) -> None:
        config = smoke.build_manual_ibkr_read_only_runtime_visibility_config(
            host="127.0.0.1",
            port=7497,
            timeout=1.0,
            disconnect_timeout=1.0,
        )
        provider = object()
        calls = []
        expected_summary = {
            "runtime_visibility_reports": [],
            "runtime_visibility_blocking": False,
            "runtime_visibility_reason": "runtime_visibility_clear",
        }

        def provider_builder(received_config):
            calls.append(("provider_builder", received_config))
            return [provider]

        def summary_builder(providers):
            calls.append(("summary_builder", list(providers)))
            return expected_summary

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = smoke.run_manual_ibkr_read_only_runtime_visibility_smoke(
                config,
                provider_builder=provider_builder,
                summary_builder=summary_builder,
            )

        self.assertEqual(result, expected_summary)
        self.assertEqual(
            calls,
            [
                ("provider_builder", config),
                ("summary_builder", [provider]),
            ],
        )
        self.assertEqual(json.loads(stdout.getvalue()), expected_summary)


if __name__ == "__main__":
    unittest.main()
