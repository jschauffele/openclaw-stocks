from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analyze_observations import (
    clean_observations,
    format_summary,
    load_observations,
    summarize_observations,
)


class AnalyzeObservationsTests(unittest.TestCase):
    def test_summarizes_counts_and_averages(self) -> None:
        rows = [
            {
                "symbol": "AAPL",
                "signal": "buy",
                "percent_change": 1.0,
                "three_close_percent_change": 1.5,
            },
            {
                "symbol": "MSFT",
                "signal": "hold",
                "percent_change": -0.5,
                "three_close_percent_change": 0.0,
            },
            {
                "symbol": "AAPL",
                "signal": "hold",
                "percent_change": 2.0,
                "three_close_percent_change": 3.0,
            },
        ]

        summary = summarize_observations(rows)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_symbol"]["AAPL"], 2)
        self.assertEqual(summary["by_symbol"]["MSFT"], 1)
        self.assertEqual(summary["signals"]["BUY"], 1)
        self.assertEqual(summary["signals"]["HOLD"], 2)
        self.assertEqual(summary["warnings"], [])
        self.assertAlmostEqual(summary["averages"]["percent_change"], 0.8333, 4)
        self.assertAlmostEqual(
            summary["averages"]["three_close_percent_change"],
            1.5,
        )
        self.assertEqual(summary["distribution"]["percent_change"]["min"], -0.5)
        self.assertEqual(summary["distribution"]["percent_change"]["max"], 2.0)
        self.assertEqual(
            summary["distribution"]["three_close_percent_change"]["min"],
            0.0,
        )
        self.assertEqual(
            summary["distribution"]["three_close_percent_change"]["max"],
            3.0,
        )
        self.assertAlmostEqual(
            summary["averages_by_symbol"]["AAPL"]["percent_change"],
            1.5,
        )
        self.assertAlmostEqual(
            summary["averages_by_symbol"]["AAPL"][
                "three_close_percent_change"
            ],
            2.25,
        )
        self.assertEqual(summary["buy_only"]["count"], 1)
        self.assertAlmostEqual(
            summary["buy_only"]["averages"]["percent_change"],
            1.0,
        )
        self.assertAlmostEqual(
            summary["buy_only"]["averages"]["three_close_percent_change"],
            1.5,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["percent_change"]["min"],
            1.0,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["percent_change"]["max"],
            1.0,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["three_close_percent_change"][
                "min"
            ],
            1.5,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["three_close_percent_change"][
                "max"
            ],
            1.5,
        )

    def test_format_summary_prints_clean_output(self) -> None:
        summary = summarize_observations(
            [
                {
                    "symbol": "AAPL",
                    "signal": "buy",
                    "percent_change": 1.0,
                    "three_close_percent_change": 1.5,
                }
            ]
        )

        output = format_summary(summary)

        self.assertIn("Total Observations: 1", output)
        self.assertIn("AAPL: 1", output)
        self.assertIn("BUY: 1", output)
        self.assertIn("HOLD: 0", output)
        self.assertIn("percent_change: 1.0000", output)
        self.assertIn("three_close_percent_change: 1.5000", output)
        self.assertIn("BUY-Only Metrics:", output)
        self.assertIn("BUY Count: 1", output)
        self.assertIn("Avg BUY percent_change: 1.0000", output)
        self.assertIn("Avg BUY three_close_percent_change: 1.5000", output)
        self.assertIn("Distribution:", output)
        self.assertIn("percent_change: min=1.0000, max=1.0000", output)
        self.assertIn(
            "three_close_percent_change: min=1.5000, max=1.5000",
            output,
        )
        self.assertIn("BUY Distribution:", output)
        self.assertIn(
            "AAPL: count=1, percent_change avg=1.0000 min=1.0000 "
            "max=1.0000, three_close_percent_change avg=1.5000 "
            "min=1.5000 max=1.5000",
            output,
        )

    def test_buy_only_averages_ignore_hold_rows(self) -> None:
        summary = summarize_observations(
            [
                {
                    "symbol": "AAPL",
                    "signal": "buy",
                    "percent_change": 1.0,
                    "three_close_percent_change": 1.5,
                },
                {
                    "symbol": "AAPL",
                    "signal": "hold",
                    "percent_change": 10.0,
                    "three_close_percent_change": 20.0,
                },
                {
                    "symbol": "MSFT",
                    "signal": "buy",
                    "percent_change": 3.0,
                    "three_close_percent_change": 4.5,
                },
            ]
        )

        self.assertEqual(summary["buy_only"]["count"], 2)
        self.assertAlmostEqual(
            summary["buy_only"]["averages"]["percent_change"],
            2.0,
        )
        self.assertAlmostEqual(
            summary["buy_only"]["averages"]["three_close_percent_change"],
            3.0,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["percent_change"]["min"],
            1.0,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["percent_change"]["max"],
            3.0,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["three_close_percent_change"][
                "min"
            ],
            1.5,
        )
        self.assertEqual(
            summary["buy_only"]["distribution"]["three_close_percent_change"][
                "max"
            ],
            4.5,
        )

    def test_buy_only_count_by_symbol(self) -> None:
        summary = summarize_observations(
            [
                {
                    "symbol": "AAPL",
                    "signal": "buy",
                    "percent_change": 1.0,
                    "three_close_percent_change": 1.5,
                },
                {
                    "symbol": "AAPL",
                    "signal": "buy",
                    "percent_change": 2.0,
                    "three_close_percent_change": 2.5,
                },
                {
                    "symbol": "MSFT",
                    "signal": "buy",
                    "percent_change": 3.0,
                    "three_close_percent_change": 3.5,
                },
                {
                    "symbol": "MSFT",
                    "signal": "hold",
                    "percent_change": 99.0,
                    "three_close_percent_change": 99.0,
                },
            ]
        )

        self.assertEqual(summary["buy_only"]["by_symbol"]["AAPL"]["count"], 2)
        self.assertEqual(summary["buy_only"]["by_symbol"]["MSFT"]["count"], 1)
        self.assertAlmostEqual(
            summary["buy_only"]["by_symbol"]["AAPL"]["percent_change"]["avg"],
            1.5,
        )
        self.assertEqual(
            summary["buy_only"]["by_symbol"]["AAPL"]["percent_change"]["min"],
            1.0,
        )
        self.assertEqual(
            summary["buy_only"]["by_symbol"]["AAPL"]["percent_change"]["max"],
            2.0,
        )
        self.assertAlmostEqual(
            summary["buy_only"]["by_symbol"]["AAPL"][
                "three_close_percent_change"
            ]["avg"],
            2.0,
        )
        self.assertEqual(
            summary["buy_only"]["by_symbol"]["AAPL"][
                "three_close_percent_change"
            ]["min"],
            1.5,
        )
        self.assertEqual(
            summary["buy_only"]["by_symbol"]["AAPL"][
                "three_close_percent_change"
            ]["max"],
            2.5,
        )
        self.assertEqual(
            summary["buy_only"]["by_symbol"]["MSFT"]["percent_change"]["min"],
            3.0,
        )
        self.assertEqual(
            summary["buy_only"]["by_symbol"]["MSFT"]["percent_change"]["max"],
            3.0,
        )

    def test_zero_buy_rows_do_not_crash(self) -> None:
        summary = summarize_observations(
            [
                {
                    "symbol": "AAPL",
                    "signal": "hold",
                    "percent_change": 1.0,
                    "three_close_percent_change": 1.5,
                }
            ]
        )

        output = format_summary(summary)

        self.assertEqual(summary["buy_only"]["count"], 0)
        self.assertEqual(
            summary["buy_only"]["averages"]["percent_change"],
            0.0,
        )
        self.assertEqual(
            summary["buy_only"]["averages"]["three_close_percent_change"],
            0.0,
        )
        self.assertEqual(summary["buy_only"]["by_symbol"], {})
        self.assertIn("BUY Count: 0", output)
        self.assertIn("Avg BUY percent_change: 0.0000", output)
        self.assertIn("Avg BUY three_close_percent_change: 0.0000", output)
        self.assertIn("BUY Distribution:", output)
        self.assertIn("percent_change: min=0.0000, max=0.0000", output)

    def test_load_observations_handles_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_file = Path(temp_dir) / "observations" / "missing.jsonl"

            rows = load_observations(missing_file)

        self.assertEqual(rows, [])

    def test_load_observations_handles_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "observations" / "observation_log.jsonl"
            log_file.parent.mkdir(parents=True)
            log_file.write_text("", encoding="utf-8")

            rows = load_observations(log_file)

        self.assertEqual(rows, [])

    def test_load_observations_reads_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "observations" / "observation_log.jsonl"
            log_file.parent.mkdir(parents=True)
            log_file.write_text(
                json.dumps({"symbol": "AAPL", "signal": "buy"}) + "\n",
                encoding="utf-8",
            )

            rows = load_observations(log_file)

        self.assertEqual(rows, [{"symbol": "AAPL", "signal": "buy"}])

    def test_clean_observations_removes_duplicate_snapshots_and_disallowed_symbols(
        self,
    ) -> None:
        rows = [
            {
                "symbol": "AAPL",
                "signal": "buy",
                "latest_candle_timestamp": "2026-04-27T14:35:00+00:00",
                "percent_change": 1.0,
                "three_close_percent_change": 1.5,
            },
            {
                "symbol": "AAPL",
                "signal": "hold",
                "latest_candle_timestamp": "2026-04-27T14:35:00+00:00",
                "percent_change": 99.0,
                "three_close_percent_change": 99.0,
            },
            {
                "symbol": "GOOG",
                "signal": "buy",
                "latest_candle_timestamp": "2026-04-27T14:35:00+00:00",
                "percent_change": 50.0,
                "three_close_percent_change": 50.0,
            },
            {
                "symbol": "MSFT",
                "signal": "hold",
                "latest_candle_timestamp": "2026-04-27T14:40:00+00:00",
                "percent_change": -0.5,
                "three_close_percent_change": 0.0,
            },
        ]

        cleaned = clean_observations(rows, allowed_symbols=["AAPL", "MSFT"])
        summary = summarize_observations(rows)

        self.assertEqual([row["symbol"] for row in cleaned], ["AAPL", "MSFT"])
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["by_symbol"]["AAPL"], 1)
        self.assertEqual(summary["by_symbol"]["MSFT"], 1)
        self.assertEqual(summary["signals"]["BUY"], 1)
        self.assertEqual(summary["signals"]["HOLD"], 1)
        self.assertAlmostEqual(summary["averages"]["percent_change"], 0.25)

    def test_warns_on_repeated_identical_symbol_metrics(self) -> None:
        summary = summarize_observations(
            [
                {
                    "symbol": "AAPL",
                    "signal": "hold",
                    "percent_change": 1.25,
                    "three_close_percent_change": 2.5,
                },
                {
                    "symbol": "AAPL",
                    "signal": "hold",
                    "percent_change": 1.25,
                    "three_close_percent_change": 2.5,
                },
                {
                    "symbol": "AAPL",
                    "signal": "buy",
                    "percent_change": 1.25,
                    "three_close_percent_change": 2.5,
                },
                {
                    "symbol": "MSFT",
                    "signal": "hold",
                    "percent_change": 1.25,
                    "three_close_percent_change": 2.5,
                },
            ]
        )

        self.assertEqual(
            summary["warnings"],
            [
                {
                    "warning": "POSSIBLE_STALE_DATA",
                    "symbol": "AAPL",
                    "count": 3,
                    "percent_change": 1.25,
                    "three_close_percent_change": 2.5,
                }
            ],
        )
        self.assertIn("POSSIBLE_STALE_DATA", format_summary(summary))


if __name__ == "__main__":
    unittest.main()
