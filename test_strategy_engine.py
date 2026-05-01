from __future__ import annotations

import unittest

from strategy_engine import generate_signal_from_closes


class GenerateSignalFromClosesTest(unittest.TestCase):
    def test_buy_when_percent_change_meets_default_threshold_with_three_close_uptrend(
        self,
    ) -> None:
        result = generate_signal_from_closes([100.0, 100.50, 101.00])

        self.assertEqual(result["signal"], "buy")
        self.assertEqual(result["decision"], "buy")
        self.assertEqual(result["reason"], "percent_change_meets_buy_threshold")
        self.assertGreaterEqual(result["percent_change"], 0.25)
        self.assertAlmostEqual(result["percent_change"], (0.50 / 100.50) * 100)
        self.assertAlmostEqual(result["three_close_percent_change"], 1.0)

    def test_hold_when_three_close_confirmation_fails_on_one_bar_rebound(self) -> None:
        result = generate_signal_from_closes([100.0, 99.0, 99.50])

        self.assertEqual(result["signal"], "hold")
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "three_close_confirmation_failed")

    def test_hold_when_percent_change_is_up_but_below_threshold(self) -> None:
        result = generate_signal_from_closes([100.0, 100.10, 100.20])

        self.assertEqual(result["signal"], "hold")
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "percent_change_below_buy_threshold")

    def test_hold_when_latest_close_is_not_above_previous_close(self) -> None:
        result = generate_signal_from_closes([100.0, 100.30, 100.20])

        self.assertEqual(result["signal"], "hold")
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "three_close_confirmation_failed")

    def test_sell_when_percent_change_is_below_sell_threshold(self) -> None:
        result = generate_signal_from_closes([100.0, 100.0, 99.4])

        self.assertEqual(result["signal"], "sell")
        self.assertEqual(result["decision"], "sell")
        self.assertEqual(result["action"], "SELL")
        self.assertEqual(result["reason"], "percent_change_meets_sell_threshold")
        self.assertLessEqual(result["percent_change"], -0.5)

    def test_sell_when_percent_change_is_at_sell_threshold_boundary(self) -> None:
        result = generate_signal_from_closes([100.0, 100.0, 99.5])

        self.assertEqual(result["signal"], "sell")
        self.assertEqual(result["decision"], "sell")
        self.assertEqual(result["action"], "SELL")
        self.assertEqual(result["reason"], "percent_change_meets_sell_threshold")
        self.assertAlmostEqual(result["percent_change"], -0.5)

    def test_no_sell_when_percent_change_is_above_sell_threshold(self) -> None:
        result = generate_signal_from_closes([100.0, 100.0, 99.51])

        self.assertNotEqual(result["signal"], "sell")
        self.assertNotEqual(result["decision"], "sell")
        self.assertNotIn("action", result)
        self.assertAlmostEqual(result["percent_change"], -0.49)

    def test_sell_takes_precedence_over_positive_multi_close_momentum(self) -> None:
        result = generate_signal_from_closes([99.0, 101.2, 100.6])

        self.assertEqual(result["signal"], "sell")
        self.assertEqual(result["decision"], "sell")
        self.assertEqual(result["action"], "SELL")
        self.assertEqual(result["reason"], "percent_change_meets_sell_threshold")
        self.assertLessEqual(result["percent_change"], -0.5)
        self.assertGreaterEqual(result["three_close_percent_change"], 1.0)

    def test_hold_when_insufficient_closes_are_available(self) -> None:
        result = generate_signal_from_closes([100.0, 100.25])

        self.assertEqual(result["signal"], "hold")
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "insufficient_data_for_confirmation")
        self.assertEqual(result["three_close_percent_change"], 0.0)

    def test_custom_threshold_can_be_used_for_deterministic_tests(self) -> None:
        result = generate_signal_from_closes(
            [100.0, 100.50, 101.00],
            min_buy_percent_change_pct=0.05,
        )

        self.assertEqual(result["signal"], "buy")
        self.assertEqual(result["min_buy_percent_change_pct"], 0.05)

    def test_negative_threshold_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "min_buy_percent_change_pct must be >= 0",
        ):
            generate_signal_from_closes(
                [100.0, 100.25, 100.60],
                min_buy_percent_change_pct=-0.1,
            )


if __name__ == "__main__":
    unittest.main()
