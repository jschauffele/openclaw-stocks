from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observation_logger import append_observation, build_observation_row


ACTION_PROPOSAL = {
    "action": "buy",
    "should_submit": True,
    "symbol": "AAPL",
    "qty": 1,
    "signal": "buy",
    "decision": "buy",
    "reason": "percent_change_meets_buy_threshold",
    "previous_close": 100.0,
    "latest_close": 101.0,
    "price_delta": 1.0,
    "percent_change": 1.0,
    "three_close_percent_change": 1.5,
}


class ObservationLoggerTests(unittest.TestCase):
    def test_observation_row_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "observations" / "observation_log.jsonl"

            append_observation(
                run_id="run_1",
                action_proposal=ACTION_PROPOSAL,
                result="success",
                signal_timeframe="5Min",
                signal_limit=5,
                latest_candle_timestamp="2026-04-27T14:35:00+00:00",
                log_file=log_file,
            )

            rows = [
                json.loads(line)
                for line in log_file.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_id"], "run_1")
        self.assertEqual(rows[0]["symbol"], "AAPL")
        self.assertEqual(rows[0]["signal"], "buy")
        self.assertEqual(rows[0]["action"], "buy")
        self.assertEqual(rows[0]["result"], "success")
        self.assertEqual(rows[0]["signal_timeframe"], "5Min")
        self.assertEqual(rows[0]["signal_limit"], 5)
        self.assertEqual(
            rows[0]["latest_candle_timestamp"],
            "2026-04-27T14:35:00+00:00",
        )

    def test_data_safety_fields_are_present(self) -> None:
        row = build_observation_row(
            run_id="run_1",
            action_proposal=ACTION_PROPOSAL,
            result="success",
            signal_timeframe="5Min",
            signal_limit=5,
            latest_candle_timestamp="2026-04-27T14:35:00+00:00",
            timestamp_utc="2026-04-27T00:00:00+00:00",
        )

        self.assertIn("percent_change", row)
        self.assertIn("three_close_percent_change", row)
        self.assertIn("signal_timeframe", row)
        self.assertIn("signal_limit", row)
        self.assertIn("latest_candle_timestamp", row)
        self.assertEqual(row["percent_change"], 1.0)
        self.assertEqual(row["three_close_percent_change"], 1.5)
        self.assertEqual(row["signal_timeframe"], "5Min")
        self.assertEqual(row["signal_limit"], 5)
        self.assertEqual(
            row["latest_candle_timestamp"],
            "2026-04-27T14:35:00+00:00",
        )

    def test_reconciliation_fields_are_included_when_supplied(self) -> None:
        row = build_observation_row(
            run_id="run_1",
            action_proposal=ACTION_PROPOSAL,
            result="reconciled",
            submit_state="submit_uncertain_reconciliation_required",
            reconciliation_status="accepted_unfilled",
            manual_review_required=False,
            terminal_for_run=True,
            filled_qty=0.0,
            working_qty=1.0,
            timestamp_utc="2026-04-27T00:00:00+00:00",
        )

        self.assertEqual(
            row["submit_state"],
            "submit_uncertain_reconciliation_required",
        )
        self.assertEqual(row["reconciliation_status"], "accepted_unfilled")
        self.assertFalse(row["manual_review_required"])
        self.assertTrue(row["terminal_for_run"])
        self.assertEqual(row["filled_qty"], 0.0)
        self.assertEqual(row["working_qty"], 1.0)

    def test_reconciliation_fields_are_omitted_when_not_supplied(self) -> None:
        row = build_observation_row(
            run_id="run_1",
            action_proposal=ACTION_PROPOSAL,
            result="success",
            timestamp_utc="2026-04-27T00:00:00+00:00",
        )

        self.assertNotIn("submit_state", row)
        self.assertNotIn("reconciliation_status", row)
        self.assertNotIn("manual_review_required", row)
        self.assertNotIn("terminal_for_run", row)
        self.assertNotIn("filled_qty", row)
        self.assertNotIn("working_qty", row)

    def test_routing_fields_are_included_when_supplied(self) -> None:
        row = build_observation_row(
            run_id="run_1",
            action_proposal=ACTION_PROPOSAL,
            result="blocked",
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no_eligible_strategy_for_regime",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
            timestamp_utc="2026-04-27T00:00:00+00:00",
        )

        self.assertEqual(row["regime_id"], "sideways")
        self.assertIsNone(row["selected_strategy_id"])
        self.assertEqual(
            row["routing_reason"],
            "no_eligible_strategy_for_regime",
        )
        self.assertEqual(row["eligible_strategy_ids"], ())
        self.assertEqual(row["rejected_strategy_ids"], ("close_momentum_v1",))
        self.assertNotIn("strategy_architecture", row)

    def test_routing_fields_are_omitted_when_not_supplied(self) -> None:
        row = build_observation_row(
            run_id="run_1",
            action_proposal=ACTION_PROPOSAL,
            result="success",
            timestamp_utc="2026-04-27T00:00:00+00:00",
        )

        self.assertNotIn("regime_id", row)
        self.assertNotIn("selected_strategy_id", row)
        self.assertNotIn("routing_reason", row)
        self.assertNotIn("eligible_strategy_ids", row)
        self.assertNotIn("rejected_strategy_ids", row)

    def test_append_behavior_preserves_prior_observations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "observations" / "observation_log.jsonl"
            log_file.parent.mkdir(parents=True)
            log_file.write_text(
                json.dumps({"run_id": "prior_run"}) + "\n",
                encoding="utf-8",
            )

            append_observation(
                run_id="run_2",
                action_proposal=ACTION_PROPOSAL,
                result="blocked",
                log_file=log_file,
            )

            rows = [
                json.loads(line)
                for line in log_file.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["run_id"], "prior_run")
        self.assertEqual(rows[1]["run_id"], "run_2")


if __name__ == "__main__":
    unittest.main()
