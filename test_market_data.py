from __future__ import annotations

import importlib
import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from data_models import HistoricalBarsRequest


def install_fake_alpaca_modules() -> None:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

    alpaca = types.ModuleType("alpaca")
    sys.modules["alpaca"] = alpaca

    common = types.ModuleType("alpaca.common")
    sys.modules["alpaca.common"] = common
    common_exceptions = types.ModuleType("alpaca.common.exceptions")

    class APIError(Exception):
        pass

    common_exceptions.APIError = APIError
    sys.modules["alpaca.common.exceptions"] = common_exceptions

    data = types.ModuleType("alpaca.data")
    sys.modules["alpaca.data"] = data
    historical = types.ModuleType("alpaca.data.historical")
    sys.modules["alpaca.data.historical"] = historical
    stock = types.ModuleType("alpaca.data.historical.stock")

    class StockHistoricalDataClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    stock.StockHistoricalDataClient = StockHistoricalDataClient
    sys.modules["alpaca.data.historical.stock"] = stock

    requests = types.ModuleType("alpaca.data.requests")

    class StockBarsRequest:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    requests.StockBarsRequest = StockBarsRequest
    sys.modules["alpaca.data.requests"] = requests

    timeframe = types.ModuleType("alpaca.data.timeframe")

    class FakeTimeFrame:
        Minute = types.SimpleNamespace(unit_value="minute")
        Hour = "hour"
        Day = "day"

        def __init__(self, amount, unit):
            self.amount = amount
            self.unit = unit

    timeframe.TimeFrame = FakeTimeFrame
    sys.modules["alpaca.data.timeframe"] = timeframe


def import_provider_module():
    install_fake_alpaca_modules()
    sys.modules.pop("alpaca_data_provider", None)
    return importlib.import_module("alpaca_data_provider")


def make_bar(close: float):
    return types.SimpleNamespace(
        timestamp=datetime(2026, 4, 10, 13, 30, tzinfo=timezone.utc),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1000.0,
    )


class MarketDataProviderTests(unittest.TestCase):
    def test_daily_request_retries_when_fewer_than_two_bars_are_returned(self):
        module = import_provider_module()
        provider = module.AlpacaMarketDataProvider(api_key="key", secret_key="secret")

        with patch.object(
            provider,
            "_fetch_bars",
            side_effect=[[make_bar(253.59)], [make_bar(253.59), make_bar(258.87)]],
        ) as fetch_bars:
            result = provider.get_historical_bars(
                HistoricalBarsRequest(symbol="AAPL", timeframe="1Day", limit=5)
            )

        self.assertEqual(fetch_bars.call_count, 2)
        self.assertEqual(len(result.candles), 2)
        self.assertIn(
            "Default IEX request returned fewer than 2 daily bars; retried with explicit recent date window.",
            result.warnings,
        )

    def test_empty_default_response_retries_with_explicit_window(self):
        module = import_provider_module()
        provider = module.AlpacaMarketDataProvider(api_key="key", secret_key="secret")

        with patch.object(
            provider,
            "_fetch_bars",
            side_effect=[[], [make_bar(253.59), make_bar(258.87)]],
        ) as fetch_bars:
            result = provider.get_historical_bars(
                HistoricalBarsRequest(symbol="AAPL", timeframe="1Hour", limit=5)
            )

        self.assertEqual(fetch_bars.call_count, 2)
        self.assertEqual(len(result.candles), 2)
        self.assertIn(
            "Default IEX request returned no bars; retried with explicit recent date window.",
            result.warnings,
        )


if __name__ == "__main__":
    unittest.main()
