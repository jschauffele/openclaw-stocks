from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from types import SimpleNamespace

from data_models import Candle, HistoricalBarsRequest, HistoricalBarsResult
from market_data import (
    FRESHNESS_CLEAN,
    FRESHNESS_QUARANTINED,
    FRESHNESS_RECENCY_CAVEATED,
    classify_market_data_freshness,
    normalized_closes_from_bars,
)


def _install_alpaca_import_stubs() -> None:
    exceptions = types.ModuleType("alpaca.common.exceptions")
    exceptions.APIError = type("APIError", (Exception,), {})
    stock = types.ModuleType("alpaca.data.historical.stock")
    stock.StockHistoricalDataClient = type("StockHistoricalDataClient", (), {})
    requests = types.ModuleType("alpaca.data.requests")
    requests.StockBarsRequest = type("StockBarsRequest", (), {})
    timeframe = types.ModuleType("alpaca.data.timeframe")

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
    ]:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules.setdefault("alpaca.common.exceptions", exceptions)
    sys.modules.setdefault("alpaca.data.historical.stock", stock)
    sys.modules.setdefault("alpaca.data.requests", requests)
    sys.modules.setdefault("alpaca.data.timeframe", timeframe)
    sys.modules.setdefault("dotenv", dotenv)


def _bars_result(
    *,
    timestamp: datetime,
    warnings: tuple[str, ...] = (),
    requested_start: datetime | None = None,
    requested_end: datetime | None = None,
):
    return HistoricalBarsResult(
        symbol="msft",
        timeframe="15Min",
        source="alpaca",
        provider="alpaca",
        feed="iex",
        adjustment_type="raw",
        is_adjusted=False,
        candles=(
            Candle(
                symbol="msft",
                timestamp=timestamp,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
            ),
            Candle(
                symbol="msft",
                timestamp=timestamp,
                open=100.5,
                high=102.0,
                low=100.0,
                close=101.5,
                volume=1100,
            ),
        ),
        warnings=warnings,
        requested_start=requested_start,
        requested_end=requested_end,
    )


def test_strategy_consumes_normalized_candles_not_alpaca_client_internals() -> None:
    result = _bars_result(
        timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc)
    )

    assert normalized_closes_from_bars(result) == [100.5, 101.5]


def test_freshness_prior_date_data_is_not_d11_countable() -> None:
    freshness = classify_market_data_freshness(
        latest_candle_timestamp="2026-06-15T20:00:00Z",
        run_timestamp="2026-06-17T13:30:00Z",
        warnings=(),
    )

    assert freshness.freshness_classification == FRESHNESS_QUARANTINED
    assert freshness.d11_countable is False
    assert freshness.warning_reason == "latest_candle_prior_to_run_date"


def test_freshness_same_day_no_warning_can_be_clean() -> None:
    freshness = classify_market_data_freshness(
        latest_candle_timestamp="2026-06-17T13:30:00Z",
        run_timestamp="2026-06-17T13:45:00Z",
        warnings=(),
    )

    assert freshness.freshness_classification == FRESHNESS_CLEAN
    assert freshness.d11_countable is True


def test_diagnostic_reports_no_execution_or_broker_authority() -> None:
    _install_alpaca_import_stubs()
    from tools.ops.market_data_freshness_diagnostic import run_diagnostic

    class FakeProvider:
        def get_historical_bars(self, request):
            return _bars_result(
                timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
                requested_start=request.start,
                requested_end=request.end,
            )

    result = run_diagnostic(
        provider=FakeProvider(),
        symbols=("MSFT",),
        timeframe="15Min",
        limit=5,
        run_timestamp=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
    )

    assert result["results"][0]["provider"] == "alpaca"
    assert result["results"][0]["feed"] == "iex"
    assert result["results"][0]["requested_start"] is not None
    assert result["results"][0]["requested_end"] is not None
    assert (
        result["results"][0]["requested_start"]
        < result["results"][0]["requested_end"]
    )
    assert result["results"][0]["freshness_classification"] == FRESHNESS_CLEAN
    assert result["package_capture"] is False
    assert result["replay"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["broker_api_authority"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False
    assert result["unit_12_opening"] is False


def test_diagnostic_explicit_window_and_stale_data_remains_caveated() -> None:
    _install_alpaca_import_stubs()
    from tools.ops.market_data_freshness_diagnostic import run_diagnostic

    captured_requests = []

    class FakeProvider:
        def get_historical_bars(self, request):
            captured_requests.append(request)
            return _bars_result(
                timestamp=datetime(2026, 6, 17, 7, 23, tzinfo=timezone.utc),
                requested_start=request.start,
                requested_end=request.end,
            )

    result = run_diagnostic(
        provider=FakeProvider(),
        symbols=("AAPL",),
        timeframe="15Min",
        limit=5,
        run_timestamp=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        requested_end=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        lookback_minutes=120,
    )

    request = captured_requests[0]
    assert request.start == datetime(2026, 6, 17, 11, 45, tzinfo=timezone.utc)
    assert request.end == datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc)
    assert result["results"][0]["requested_start"] == "2026-06-17T11:45:00+00:00"
    assert result["results"][0]["requested_end"] == "2026-06-17T13:45:00+00:00"
    assert result["results"][0]["provider"] == "alpaca"
    assert result["results"][0]["feed"] == "iex"
    assert result["results"][0]["freshness_classification"] == (
        FRESHNESS_RECENCY_CAVEATED
    )
    assert result["results"][0]["d11_countable"] is False
    assert result["broker_api_authority"] is False
    assert result["execution_authority"] is False


def test_alpaca_iex_provider_reports_explicit_request_window(monkeypatch) -> None:
    _install_alpaca_import_stubs()
    import alpaca_data_provider

    captured_request_kwargs = []

    class FakeStockBarsRequest:
        def __init__(self, **kwargs):
            captured_request_kwargs.append(kwargs)

    class FakeClient:
        def get_stock_bars(self, _request):
            return SimpleNamespace(
                data={
                    "MSFT": [
                        SimpleNamespace(
                            timestamp=datetime(
                                2026, 6, 17, 13, 30, tzinfo=timezone.utc
                            ),
                            open=100.0,
                            high=101.0,
                            low=99.0,
                            close=100.5,
                            volume=1000,
                        )
                    ]
                }
            )

    monkeypatch.setattr(alpaca_data_provider, "StockBarsRequest", FakeStockBarsRequest)
    provider = alpaca_data_provider.AlpacaMarketDataProvider.__new__(
        alpaca_data_provider.AlpacaMarketDataProvider
    )
    provider.client = FakeClient()

    start = datetime(2026, 6, 17, 11, 45, tzinfo=timezone.utc)
    end = datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc)
    result = provider.get_historical_bars(
        HistoricalBarsRequest(
            symbol="MSFT",
            timeframe="15Min",
            limit=5,
            start=start,
            end=end,
        )
    )

    assert captured_request_kwargs[0]["start"] == start
    assert captured_request_kwargs[0]["end"] == end
    assert captured_request_kwargs[0]["feed"] == "iex"
    assert result.provider == "alpaca"
    assert result.feed == "iex"
    assert result.requested_start == start
    assert result.requested_end == end
