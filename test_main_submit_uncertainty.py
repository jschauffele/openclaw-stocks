from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime, timezone
import sys
import types
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from broker_interface import BrokerAccountState, BrokerOrderResult


def install_alpaca_import_stubs() -> None:
    exceptions = types.ModuleType("alpaca.common.exceptions")
    exceptions.APIError = type("APIError", (Exception,), {})
    stock = types.ModuleType("alpaca.data.historical.stock")
    stock.StockHistoricalDataClient = type("StockHistoricalDataClient", (), {})
    requests = types.ModuleType("alpaca.data.requests")
    requests.StockBarsRequest = type("StockBarsRequest", (), {})
    timeframe = types.ModuleType("alpaca.data.timeframe")
    trading_client = types.ModuleType("alpaca.trading.client")
    trading_client.TradingClient = type("TradingClient", (), {})
    trading_enums = types.ModuleType("alpaca.trading.enums")
    trading_enums.OrderSide = SimpleNamespace(BUY="buy", SELL="sell")
    trading_enums.QueryOrderStatus = SimpleNamespace(OPEN="open")
    trading_enums.TimeInForce = SimpleNamespace(DAY="day")
    trading_requests = types.ModuleType("alpaca.trading.requests")
    trading_requests.GetCalendarRequest = type("GetCalendarRequest", (), {})
    trading_requests.GetOrdersRequest = type("GetOrdersRequest", (), {})
    trading_requests.MarketOrderRequest = type("MarketOrderRequest", (), {})

    class TimeFrame:
        Minute = SimpleNamespace(unit_value="Minute")
        Hour = "Hour"
        Day = "Day"

        def __init__(self, value, unit_value):
            self.value = value
            self.unit_value = unit_value

    timeframe.TimeFrame = TimeFrame
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    for name in [
        "alpaca",
        "alpaca.common",
        "alpaca.data",
        "alpaca.data.historical",
        "alpaca.trading",
    ]:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules.setdefault("alpaca.common.exceptions", exceptions)
    sys.modules.setdefault("alpaca.data.historical.stock", stock)
    sys.modules.setdefault("alpaca.data.requests", requests)
    sys.modules.setdefault("alpaca.data.timeframe", timeframe)
    sys.modules.setdefault("alpaca.trading.client", trading_client)
    sys.modules.setdefault("alpaca.trading.enums", trading_enums)
    sys.modules.setdefault("alpaca.trading.requests", trading_requests)
    sys.modules.setdefault("dotenv", dotenv)


install_alpaca_import_stubs()
import main


class FakeBroker:
    def __init__(self, order_status: str) -> None:
        self.client = object()
        self.order_status = order_status
        self.submit_calls = 0
        self.execution_snapshot_calls = 0

    def get_account_buying_power(self) -> BrokerAccountState:
        return BrokerAccountState(
            broker_name="test",
            buying_power=100000.0,
        )

    def build_market_order(self, symbol: str, qty: int):
        return SimpleNamespace(symbol=symbol, qty=qty)

    def submit_market_order(self, order) -> BrokerOrderResult:
        self.submit_calls += 1
        return BrokerOrderResult(
            broker_name="ibkr",
            order_id="101",
            order_status=self.order_status,
            broker_status=self.order_status,
            is_terminal=False,
        )

    def get_execution_snapshot(self, **_kwargs):
        self.execution_snapshot_calls += 1
        raise AssertionError("runtime guard must not invoke reconciliation workflow")


def bars_result():
    timestamp = datetime(2026, 5, 12, tzinfo=timezone.utc)
    return SimpleNamespace(
        candles=[
            SimpleNamespace(close=100.0, timestamp=timestamp),
            SimpleNamespace(close=100.25, timestamp=timestamp),
            SimpleNamespace(close=100.60, timestamp=timestamp),
        ],
        warnings=[],
    )


def action_proposal():
    return {
        "should_submit": True,
        "action": "buy",
        "signal": "buy",
        "decision": "buy",
        "reason": "test_submit",
        "previous_close": 100.25,
        "latest_close": 100.60,
        "price_delta": 0.35,
        "percent_change": 0.35,
        "three_close_percent_change": 0.60,
    }


class MainSubmitUncertaintyTests(unittest.TestCase):
    def run_main_with_order_status(self, order_status: str):
        broker = FakeBroker(order_status)
        reports = []
        events = []
        observations = []
        write_state_calls = []

        def persist_report(**kwargs):
            reports.append(kwargs)

        def log_event(event_type, stage, status, payload):
            events.append(
                {
                    "event_type": event_type,
                    "stage": stage,
                    "status": status,
                    "payload": payload,
                }
            )

        patchers = [
            patch("config.load_config"),
            patch("config.BASE_DIR", "/tmp/openclaw-test", create=True),
            patch("config.LOG_FILE", "/tmp/openclaw-test.log", create=True),
            patch("config.STATE_FILE", "/tmp/openclaw-state.json", create=True),
            patch("config.RUN_REPORT_FILE", "/tmp/openclaw-report.json", create=True),
            patch("config.LEGACY_LAST_ORDER_FILE", "/tmp/openclaw-last-order.txt", create=True),
            patch("config.OPENCLAW_ENABLED", True, create=True),
            patch("config.OPENCLAW_DRY_RUN", False, create=True),
            patch("config.OPENCLAW_SYMBOL", "AAPL", create=True),
            patch("config.OPENCLAW_QTY", 1, create=True),
            patch("config.OPENCLAW_MAX_POSITION_SIZE", 5, create=True),
            patch("config.OPENCLAW_DUPLICATE_COOLDOWN_SECONDS", 600, create=True),
            patch("config.OPENCLAW_BROKER", "alpaca", create=True),
            patch("config.ALPACA_API_KEY", "key", create=True),
            patch("config.ALPACA_SECRET_KEY", "secret", create=True),
            patch("config.ALPACA_BASE_URL", "https://paper-api.alpaca.markets", create=True),
            patch("config.ALLOWED_SYMBOLS", ["AAPL"], create=True),
            patch("config.env_str", side_effect=lambda _name, default: default),
            patch("config.env_int", side_effect=lambda _name, default: default),
            patch("main.setup_logging"),
            patch("main.create_broker_adapter", return_value=broker),
            patch("main.generate_run_id", return_value="run-test"),
            patch("main.initialize_event_logger"),
            patch("main.log_event", side_effect=log_event),
            patch("main.validate_config", return_value=True),
            patch(
                "main.get_market_session_status",
                return_value={"is_open": True, "reason": "market_open"},
            ),
            patch("main.AlpacaMarketDataProvider", return_value=object()),
            patch("main.get_historical_bars", return_value=bars_result()),
            patch("main.generate_signal_from_closes", return_value=object()),
            patch("main.validate_signal_result", return_value=object()),
            patch("main.build_action_proposal", return_value=action_proposal()),
            patch(
                "main.risk_check",
                return_value={"passed": True, "estimated_cost": 100.0},
            ),
            patch(
                "main.reconcile_position",
                return_value={
                    "passed": True,
                    "reason": "broker_reconciliation_passed",
                    "message": "broker_reconciliation_passed",
                    "existing_qty": 0,
                    "open_buy_order_qty": 0,
                    "projected_qty": 1,
                },
            ),
            patch(
                "state_manager.duplicate_check",
                return_value={
                    "is_duplicate": False,
                    "reason": "no_matching_state",
                    "age_seconds": None,
                },
            ),
            patch(
                "state_manager.write_order_state",
                side_effect=lambda *args: write_state_calls.append(args),
            ),
            patch("reporting.persist_report", side_effect=persist_report),
            patch(
                "main.append_observation",
                side_effect=lambda **kwargs: observations.append(kwargs),
            ),
        ]
        with ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            main.main()

        return {
            "broker": broker,
            "reports": reports,
            "events": events,
            "observations": observations,
            "write_state_calls": write_state_calls,
        }

    def test_reconciliation_required_does_not_produce_success(self) -> None:
        result = self.run_main_with_order_status("reconciliation_required")

        self.assertEqual(result["broker"].submit_calls, 1)
        self.assertEqual(result["broker"].execution_snapshot_calls, 0)
        self.assertEqual(result["write_state_calls"], [])
        self.assertFalse(
            any(event["status"] == "paper_submitted" for event in result["events"])
        )
        self.assertFalse(
            any(report.get("result") == "success" for report in result["reports"])
        )

        report = result["reports"][-1]
        self.assertEqual(report["result"], "manual_review_required")
        self.assertEqual(report["reason"], "broker_reconciliation_required")
        self.assertEqual(
            report["submit_state"],
            "submit_uncertain_reconciliation_required",
        )
        self.assertIsNone(report["reconciliation_status"])
        self.assertTrue(report["manual_review_required"])
        self.assertTrue(report["terminal_for_run"])
        self.assertTrue(report["reconciliation_ambiguous"])
        self.assertIsNone(report["filled_qty"])
        self.assertIsNone(report["working_qty"])
        self.assertEqual(
            result["observations"][-1]["result"],
            "manual_review_required",
        )

    def test_paper_submitted_path_still_works_for_ordinary_submitted_order(self) -> None:
        result = self.run_main_with_order_status("submitted")

        self.assertEqual(result["broker"].submit_calls, 1)
        self.assertEqual(len(result["write_state_calls"]), 1)
        self.assertTrue(
            any(event["status"] == "paper_submitted" for event in result["events"])
        )
        report = result["reports"][-1]

        self.assertEqual(report["result"], "success")
        self.assertEqual(report["reason"], "paper_order_submitted")
        self.assertEqual(report["order_status"], "submitted")
        self.assertEqual(result["observations"][-1]["result"], "success")


if __name__ == "__main__":
    unittest.main()
