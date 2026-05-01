from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from decision_engine import build_action_proposal
from event_logger import initialize_event_logger, log_event
from main import (
    build_strategy_hold_report_notes,
    build_strategy_signal_event_payload,
    validate_data_config,
)
from reporting import build_run_report
from signal_validator import validate_signal_result
from strategy_engine import generate_signal_from_closes


class ObservabilityPayloadsTest(unittest.TestCase):
    def _action_proposal(self) -> dict:
        signal_result = validate_signal_result(
            generate_signal_from_closes([100.0, 100.25, 100.60])
        )
        return build_action_proposal(
            symbol="aapl",
            qty=1,
            signal_result=signal_result,
        )

    def test_signal_metrics_survive_validation_and_action_proposal(self) -> None:
        action_proposal = self._action_proposal()

        self.assertAlmostEqual(
            action_proposal["percent_change"],
            (100.60 - 100.25) / 100.25 * 100,
        )
        self.assertAlmostEqual(
            action_proposal["three_close_percent_change"],
            (100.60 - 100.0) / 100.0 * 100,
        )

    def test_strategy_signal_event_payload_contains_three_close_metric(self) -> None:
        action_proposal = self._action_proposal()
        payload = build_strategy_signal_event_payload(action_proposal)

        self.assertIn("percent_change", payload)
        self.assertIn("three_close_percent_change", payload)
        self.assertAlmostEqual(
            payload["percent_change"],
            (100.60 - 100.25) / 100.25 * 100,
        )
        self.assertAlmostEqual(payload["three_close_percent_change"], 0.6)

        with tempfile.TemporaryDirectory() as temp_dir:
            run_id = "run_test_observability"
            initialize_event_logger(run_id, base_dir=temp_dir)
            log_event("strategy", "strategy_evaluated", "ok", payload)

            event_path = Path(temp_dir) / f"{run_id}.jsonl"
            event = json.loads(event_path.read_text(encoding="utf-8").strip())

        self.assertEqual(event["event_type"], "strategy")
        self.assertEqual(event["stage"], "strategy_evaluated")
        self.assertIn("percent_change", event["payload"])
        self.assertIn("three_close_percent_change", event["payload"])

    def test_sell_signal_survives_report_and_strategy_event_payload(self) -> None:
        signal_result = validate_signal_result(
            generate_signal_from_closes([100.0, 100.0, 99.4])
        )
        action_proposal = build_action_proposal(
            symbol="aapl",
            qty=1,
            signal_result=signal_result,
        )
        payload = build_strategy_signal_event_payload(action_proposal)
        report = build_run_report(
            run_id="run_test",
            mode="dry_run",
            result="blocked",
            reason=action_proposal["reason"],
            trigger_source="test",
            side=action_proposal["action"],
            symbol="AAPL",
            qty=1,
            openclaw_enabled=True,
            duplicate_cooldown_seconds=600,
            max_position_size=5,
            allowed_symbols=["AAPL"],
            alpaca_base_url="https://paper-api.alpaca.markets",
        )

        self.assertEqual(action_proposal["action"], "sell")
        self.assertFalse(action_proposal["should_submit"])
        self.assertEqual(report["side"], "sell")
        self.assertEqual(report["reason"], "percent_change_meets_sell_threshold")
        self.assertEqual(payload["signal"], "sell")
        self.assertEqual(payload["decision"], "sell")
        self.assertEqual(payload["action"], "sell")
        self.assertEqual(payload["reason"], "percent_change_meets_sell_threshold")

        with tempfile.TemporaryDirectory() as temp_dir:
            run_id = "run_test_sell_observability"
            initialize_event_logger(run_id, base_dir=temp_dir)
            log_event("strategy", "strategy_evaluated", "blocked", payload)

            event_path = Path(temp_dir) / f"{run_id}.jsonl"
            event = json.loads(event_path.read_text(encoding="utf-8").strip())

        self.assertEqual(event["stage"], "strategy_evaluated")
        self.assertEqual(event["payload"]["action"], "sell")
        self.assertEqual(
            event["payload"]["reason"],
            "percent_change_meets_sell_threshold",
        )

    def test_strategy_hold_report_notes_include_three_close_metric_next_to_percent_change(
        self,
    ) -> None:
        action_proposal = self._action_proposal()
        report = build_run_report(
            run_id="run_test",
            mode="dry_run",
            result="blocked",
            reason="strategy_hold",
            trigger_source="test",
            side="buy",
            symbol="AAPL",
            qty=1,
            openclaw_enabled=True,
            duplicate_cooldown_seconds=600,
            max_position_size=5,
            allowed_symbols=["AAPL"],
            alpaca_base_url="https://paper-api.alpaca.markets",
            signal_timeframe="5Min",
            signal_limit=5,
            notes=build_strategy_hold_report_notes(action_proposal),
        )

        self.assertEqual(report["signal_timeframe"], "5Min")
        self.assertEqual(report["signal_limit"], 5)
        self.assertTrue(
            any(note.startswith("percent_change=") for note in report["notes"])
        )
        self.assertTrue(
            any(
                note.startswith("three_close_percent_change=")
                for note in report["notes"]
            )
        )

    def test_systemd_timer_rejects_daily_signal_timeframe(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "OPENCLAW_SIGNAL_TIMEFRAME must not be 1Day",
        ):
            validate_data_config(
                trigger_source="systemd_timer",
                signal_timeframe="1Day",
                signal_limit=5,
            )

    def test_systemd_timer_rejects_signal_limit_below_three(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "OPENCLAW_SIGNAL_LIMIT must be >= 3",
        ):
            validate_data_config(
                trigger_source="systemd_timer",
                signal_timeframe="5Min",
                signal_limit=2,
            )

    def test_non_timer_trigger_allows_existing_defaults(self) -> None:
        validate_data_config(
            trigger_source="manual_or_systemd",
            signal_timeframe="1Day",
            signal_limit=1,
        )


if __name__ == "__main__":
    unittest.main()
