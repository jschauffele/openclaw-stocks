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

    def test_percent_change_fields_are_present(self) -> None:
        row = build_observation_row(
            run_id="run_1",
            action_proposal=ACTION_PROPOSAL,
            result="success",
            timestamp_utc="2026-04-27T00:00:00+00:00",
        )

        self.assertIn("percent_change", row)
        self.assertIn("three_close_percent_change", row)
        self.assertEqual(row["percent_change"], 1.0)
        self.assertEqual(row["three_close_percent_change"], 1.5)

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
