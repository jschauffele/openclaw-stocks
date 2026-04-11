from __future__ import annotations

import sys
import types
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch


if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

import bot_service
from data_models import Candle, HistoricalBarsResult


def make_settings(**overrides):
    base = {
        "base_dir": "/tmp/openclaw-stocks",
        "log_file": "/tmp/openclaw-stocks/openclaw.log",
        "state_file": "/tmp/openclaw-stocks/order_state.json",
        "run_report_file": "/tmp/openclaw-stocks/last_run_report.json",
        "legacy_last_order_file": "/tmp/openclaw-stocks/last_order.txt",
        "openclaw_enabled": True,
        "dry_run": True,
        "symbol": "AAPL",
        "qty": 1,
        "max_position_size": 5,
        "duplicate_cooldown_seconds": 900,
        "alpaca_api_key": "key",
        "alpaca_secret_key": "secret",
        "alpaca_base_url": "https://paper-api.alpaca.markets",
        "allowed_symbols": ("AAPL", "MSFT", "GOOG"),
        "trigger_source": "test",
        "signal_timeframe": "1Day",
        "signal_limit": 5,
        "mode": "dry_run",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_bars_result(*closes: float) -> HistoricalBarsResult:
    candles = tuple(
        Candle(
            symbol="AAPL",
            timestamp=datetime(2026, 4, 10, 13, 30 + index, tzinfo=timezone.utc),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1000.0,
        )
        for index, close in enumerate(closes)
    )
    return HistoricalBarsResult(
        symbol="AAPL",
        timeframe="1Day",
        source="alpaca",
        adjustment_type="raw",
        is_adjusted=False,
        candles=candles,
        warnings=(),
    )


class BotServiceTests(unittest.TestCase):
    def make_bot(self, settings=None, client=None):
        settings = settings or make_settings()
        client = client or SimpleNamespace(get_account=Mock(return_value=SimpleNamespace(buying_power=10000.0)))
        return bot_service.OpenClawBot(
            settings=settings,
            trading_client_factory=lambda: client,
            market_data_provider_factory=lambda: object(),
        ), client

    def test_disabled_killswitch_blocks_before_runtime_work(self):
        bot, _client = self.make_bot(settings=make_settings(openclaw_enabled=False))

        with patch.object(bot_service, "persist_report_for_settings") as persist_report, patch.object(
            bot_service, "get_market_session_status"
        ) as market_status:
            bot.run()

        market_status.assert_not_called()
        persist_report.assert_called_once()
        self.assertEqual(persist_report.call_args.kwargs["result"], "blocked")
        self.assertEqual(persist_report.call_args.kwargs["reason"], "killswitch_disabled")

    def test_pre_open_market_block_persists_expected_reason(self):
        bot, _client = self.make_bot()

        with patch.object(bot_service, "persist_report_for_settings") as persist_report, patch.object(
            bot_service, "get_market_session_status", return_value={"is_open": False, "reason": "before_regular_session_open"}
        ), patch.object(bot_service, "validate_config", return_value=True):
            bot.run()

        persist_report.assert_called_once()
        self.assertEqual(persist_report.call_args.kwargs["reason"], "before_regular_session_open")

    def test_insufficient_market_data_blocks_run(self):
        bot, _client = self.make_bot()

        with patch.object(bot_service, "persist_report_for_settings") as persist_report, patch.object(
            bot_service, "get_market_session_status", return_value={"is_open": True, "reason": "regular_session_open"}
        ), patch.object(bot_service, "validate_config", return_value=True), patch.object(
            bot_service,
            "get_historical_bars",
            return_value=make_bars_result(253.59),
        ):
            bot.run()

        persist_report.assert_called_once()
        self.assertEqual(persist_report.call_args.kwargs["reason"], "insufficient_market_data")

    def test_strategy_hold_path_persists_hold_report(self):
        bot, client = self.make_bot()

        with patch.object(bot_service, "persist_report_for_settings") as persist_report, patch.object(
            bot_service, "get_market_session_status", return_value={"is_open": True, "reason": "regular_session_open"}
        ), patch.object(bot_service, "validate_config", return_value=True), patch.object(
            bot_service,
            "get_historical_bars",
            return_value=make_bars_result(258.87, 253.59),
        ):
            bot.run()

        client.get_account.assert_not_called()
        persist_report.assert_called_once()
        self.assertEqual(persist_report.call_args.kwargs["reason"], "strategy_hold")

    def test_dry_run_buy_path_writes_state_and_success_report(self):
        bot, client = self.make_bot(settings=make_settings(dry_run=True, mode="dry_run"))

        with patch.object(bot_service, "persist_report_for_settings") as persist_report, patch.object(
            bot_service, "write_order_state_for_settings"
        ) as write_state, patch.object(
            bot_service, "submit_market_order"
        ) as submit_order, patch.object(
            bot_service, "get_market_session_status", return_value={"is_open": True, "reason": "regular_session_open"}
        ), patch.object(bot_service, "validate_config", return_value=True), patch.object(
            bot_service,
            "get_historical_bars",
            return_value=make_bars_result(253.59, 258.87),
        ), patch.object(
            bot_service,
            "duplicate_check_for_settings",
            return_value={"is_duplicate": False, "reason": "no_matching_state", "age_seconds": None},
        ), patch.object(
            bot_service,
            "risk_check",
            return_value={"passed": True, "reason": "passed", "message": "risk_check_passed", "estimated_cost": 100},
        ), patch.object(
            bot_service,
            "reconcile_position",
            return_value={
                "passed": True,
                "reason": "broker_reconciliation_passed",
                "message": "broker_reconciliation_passed",
                "existing_qty": 3,
                "open_buy_order_qty": 0,
                "projected_qty": 4,
            },
        ):
            bot.run()

        client.get_account.assert_called_once()
        write_state.assert_called_once()
        submit_order.assert_not_called()
        self.assertEqual(persist_report.call_args.kwargs["reason"], "dry_run_completed")

    def test_duplicate_cooldown_blocks_before_risk_and_reconciliation(self):
        bot, _client = self.make_bot()

        with patch.object(bot_service, "persist_report_for_settings") as persist_report, patch.object(
            bot_service, "risk_check"
        ) as risk_check, patch.object(
            bot_service, "reconcile_position"
        ) as reconcile_position, patch.object(
            bot_service, "get_market_session_status", return_value={"is_open": True, "reason": "regular_session_open"}
        ), patch.object(bot_service, "validate_config", return_value=True), patch.object(
            bot_service,
            "get_historical_bars",
            return_value=make_bars_result(253.59, 258.87),
        ), patch.object(
            bot_service,
            "duplicate_check_for_settings",
            return_value={"is_duplicate": True, "reason": "cooldown_active", "age_seconds": 45},
        ):
            bot.run()

        risk_check.assert_not_called()
        reconcile_position.assert_not_called()
        self.assertEqual(persist_report.call_args.kwargs["reason"], "cooldown_active")

    def test_reconciliation_block_persists_guard_reason(self):
        bot, _client = self.make_bot()

        with patch.object(bot_service, "persist_report_for_settings") as persist_report, patch.object(
            bot_service, "get_market_session_status", return_value={"is_open": True, "reason": "regular_session_open"}
        ), patch.object(bot_service, "validate_config", return_value=True), patch.object(
            bot_service,
            "get_historical_bars",
            return_value=make_bars_result(253.59, 258.87),
        ), patch.object(
            bot_service,
            "duplicate_check_for_settings",
            return_value={"is_duplicate": False, "reason": "no_matching_state", "age_seconds": None},
        ), patch.object(
            bot_service,
            "risk_check",
            return_value={"passed": True, "reason": "passed", "message": "risk_check_passed", "estimated_cost": 100},
        ), patch.object(
            bot_service,
            "reconcile_position",
            return_value={
                "passed": False,
                "reason": "projected_exposure_exceeds_max_position_size",
                "message": "projected exposure 6 exceeds max_position_size 5",
                "existing_qty": 3,
                "open_buy_order_qty": 2,
                "projected_qty": 6,
            },
        ):
            bot.run()

        self.assertEqual(
            persist_report.call_args.kwargs["reason"],
            "projected_exposure_exceeds_max_position_size",
        )


if __name__ == "__main__":
    unittest.main()
