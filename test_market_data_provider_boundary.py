from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from data_models import Candle, HistoricalBarsRequest, HistoricalBarsResult
from ibkr_market_data_diagnostic_contract import (
    D11_STATUS_INSUFFICIENT,
    IBKR_DIAGNOSTIC_REQUIRED_OUTPUT_FIELDS,
    IBKR_PROVIDER_KEY,
    IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
    UNIT_12_STATUS_BLOCKED,
    evaluate_ibkr_diagnostic_result,
    ibkr_read_only_diagnostic_contract,
)
from ibkr_read_only_implementation_design import (
    DESIGN_STATUS_DESIGN_ONLY,
    IBKR_CONNECTION_CONFIG_CONTRACT_FIELDS,
    IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY,
    IBKR_READ_ONLY_IMPLEMENTATION_DESIGN_STATUSES,
    IBKR_READ_ONLY_IMPLEMENTATION_REQUIREMENTS,
    ibkr_read_only_implementation_design,
)
from tools.ops.ibkr_market_data_freshness_diagnostic import (
    IBKR_DIAGNOSTIC_NOT_AUTHORIZED_REASON,
    IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY,
    build_scaffold_result,
)
from tools.ops.ibkr_market_data_read_only_smoke import (
    IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY,
    IBKR_READ_ONLY_SMOKE_DEPENDENCY_UNAVAILABLE_REASON,
    build_smoke_result,
    run_smoke_diagnostic,
)
from tools.ops.ibkr_market_data_vps_read_only_freshness_proof import (
    VPS_REPO_ROOT,
    VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY,
    build_vps_read_only_freshness_proof,
)
from market_data import (
    FRESHNESS_CLEAN,
    FRESHNESS_QUARANTINED,
    FRESHNESS_RECENCY_CAVEATED,
    classify_market_data_freshness,
    normalized_closes_from_bars,
)
from market_data_provider_registry import (
    PROVIDER_REGISTRY_AUTHORITY_BOUNDARY,
    PROVIDER_STATUS_NOT_CONFIGURED,
    PROVIDER_STATUS_SUSPECT,
    PROVIDER_STATUS_UNAVAILABLE,
    get_provider_registry_entry,
    list_provider_registry,
)
from market_data_provider_selection import (
    CANDIDATE_STATUS_CANDIDATE,
    D11_PRIMARY_PROVIDER_SELECTION_CRITERIA,
    PROVIDER_SELECTION_AUTHORITY_BOUNDARY,
    candidate_can_count_for_d11,
    get_provider_candidate,
    list_provider_candidates,
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


def test_freshness_after_utc_midnight_uses_us_equity_session_date() -> None:
    freshness = classify_market_data_freshness(
        latest_candle_timestamp="2026-06-17T19:45:00Z",
        run_timestamp="2026-06-18T02:15:00Z",
        warnings=(),
    )

    assert freshness.freshness_classification == FRESHNESS_RECENCY_CAVEATED
    assert freshness.d11_countable is False
    assert freshness.warning_reason == (
        "regular_session_closed_latest_candle_valid_for_last_session"
    )
    assert freshness.latest_candle_timestamp == "2026-06-17T19:45:00+00:00"
    assert freshness.run_timestamp == "2026-06-18T02:15:00+00:00"


def test_freshness_truly_older_us_equity_session_quarantines() -> None:
    freshness = classify_market_data_freshness(
        latest_candle_timestamp="2026-06-16T19:45:00Z",
        run_timestamp="2026-06-18T02:15:00Z",
        warnings=(),
    )

    assert freshness.freshness_classification == FRESHNESS_QUARANTINED
    assert freshness.d11_countable is False
    assert freshness.warning_reason == "latest_candle_prior_to_run_date"


def test_freshness_warning_bearing_data_remains_quarantined() -> None:
    freshness = classify_market_data_freshness(
        latest_candle_timestamp="2026-06-17T19:45:00Z",
        run_timestamp="2026-06-18T02:15:00Z",
        warnings=("POSSIBLE_STALE_DATA",),
    )

    assert freshness.freshness_classification == FRESHNESS_QUARANTINED
    assert freshness.d11_countable is False
    assert freshness.warning_reason == "market_input_captured_warnings_present"


def test_freshness_missing_or_naive_timestamps_fail_closed() -> None:
    missing_latest = classify_market_data_freshness(
        latest_candle_timestamp=None,
        run_timestamp="2026-06-18T02:15:00Z",
        warnings=(),
    )
    naive_run = classify_market_data_freshness(
        latest_candle_timestamp="2026-06-17T19:45:00Z",
        run_timestamp=datetime(2026, 6, 18, 2, 15),
        warnings=(),
    )

    assert missing_latest.freshness_classification == FRESHNESS_QUARANTINED
    assert missing_latest.warning_reason == (
        "missing_or_malformed_latest_candle_timestamp"
    )
    assert naive_run.freshness_classification == FRESHNESS_QUARANTINED
    assert naive_run.warning_reason == "missing_or_malformed_run_timestamp"


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
    assert result["results"][0]["provider_role"] == "secondary"
    assert result["results"][0]["provider_status"] == PROVIDER_STATUS_SUSPECT
    assert result["results"][0]["d11_primary_eligible"] is False
    assert "explicit-window Alpaca/IEX diagnostic" in result["results"][0]["reason"]
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
                timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
                requested_start=request.start,
                requested_end=request.end,
            )

    result = run_diagnostic(
        provider=FakeProvider(),
        symbols=("AAPL",),
        timeframe="15Min",
        limit=5,
        run_timestamp=datetime(2026, 6, 17, 14, 15, tzinfo=timezone.utc),
        requested_end=datetime(2026, 6, 17, 14, 15, tzinfo=timezone.utc),
        lookback_minutes=120,
    )

    request = captured_requests[0]
    assert request.start == datetime(2026, 6, 17, 12, 15, tzinfo=timezone.utc)
    assert request.end == datetime(2026, 6, 17, 14, 15, tzinfo=timezone.utc)
    assert result["results"][0]["requested_start"] == "2026-06-17T12:15:00+00:00"
    assert result["results"][0]["requested_end"] == "2026-06-17T14:15:00+00:00"
    assert result["results"][0]["provider"] == "alpaca"
    assert result["results"][0]["feed"] == "iex"
    assert result["results"][0]["provider_status"] == PROVIDER_STATUS_SUSPECT
    assert result["results"][0]["d11_primary_eligible"] is False
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


def test_provider_registry_marks_alpaca_iex_not_d11_primary_eligible() -> None:
    entry = get_provider_registry_entry(provider="alpaca", feed="iex")

    assert entry["provider_key"] == "alpaca_iex"
    assert entry["provider_role"] == "secondary"
    assert entry["provider_status"] == PROVIDER_STATUS_SUSPECT
    assert entry["d11_primary_eligible"] is False
    assert "122-167 minute stale" in entry["reason"]
    assert "recency_caveated" in entry["reason"]


def test_provider_registry_contains_unconfigured_future_primary_slot() -> None:
    entries = {
        str(entry["provider_key"]): entry for entry in list_provider_registry()
    }

    future_primary = entries["future_primary"]
    assert future_primary["provider_role"] == "primary"
    assert future_primary["provider_status"] == PROVIDER_STATUS_NOT_CONFIGURED
    assert future_primary["d11_primary_eligible"] is False
    assert "not configured" in str(future_primary["reason"])


def test_unavailable_or_not_configured_providers_cannot_count_for_d11() -> None:
    unknown = get_provider_registry_entry(provider="unknown_vendor", feed="sip")
    future_primary = get_provider_registry_entry(provider="future_primary")

    assert unknown["provider_status"] == PROVIDER_STATUS_UNAVAILABLE
    assert unknown["d11_primary_eligible"] is False
    assert future_primary["provider_status"] == PROVIDER_STATUS_NOT_CONFIGURED
    assert future_primary["d11_primary_eligible"] is False


def test_provider_registry_is_metadata_only_no_network_or_authority() -> None:
    import market_data_provider_registry

    source = Path(market_data_provider_registry.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "requests",
        "urllib",
        "from alpaca",
        "import alpaca",
        "ibkr",
        "subprocess",
        "import socket",
        "from socket",
        "open(",
        "get_stock_bars",
        "submit",
        "package_execution_orchestrator",
    ):
        assert forbidden not in source
    assert "no_network_api_calls" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_broker_api_authority" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_order_authority" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_execution_authority" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_package_capture" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_replay" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_scoring" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_candidate_generation" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY
    assert "no_unit_12_opening" in PROVIDER_REGISTRY_AUTHORITY_BOUNDARY


def test_provider_selection_candidates_are_not_primary_eligible_by_default() -> None:
    candidates = list_provider_candidates()

    assert {candidate["provider_key"] for candidate in candidates} == {
        "ibkr_market_data_candidate",
        "polygon_candidate",
        "tiingo_candidate",
        "schwab_market_data_candidate",
        "manual_csv_offline_candidate",
    }
    assert all(candidate["d11_primary_eligible"] is False for candidate in candidates)
    assert all(candidate_can_count_for_d11(candidate) is False for candidate in candidates)


def test_provider_selection_ibkr_candidate_has_no_order_or_execution_authority() -> None:
    candidate = get_provider_candidate("ibkr_market_data_candidate")

    assert candidate["d11_primary_candidate_status"] == CANDIDATE_STATUS_CANDIDATE
    assert candidate["broker_coupled"] is True
    assert candidate["order_authority"] is False
    assert candidate["execution_authority"] is False
    assert candidate["d11_primary_eligible"] is False
    assert "IBKR/TWS/Gateway not opened" in candidate["reason"]


def test_provider_selection_credentials_required_candidates_not_configured() -> None:
    for provider_key in (
        "ibkr_market_data_candidate",
        "polygon_candidate",
        "tiingo_candidate",
        "schwab_market_data_candidate",
    ):
        candidate = get_provider_candidate(provider_key)
        assert candidate["auth_required"] is True
        assert candidate["credentials_configured"] is False
        assert candidate["d11_primary_eligible"] is False


def test_provider_selection_criteria_include_d11_primary_gate_requirements() -> None:
    assert "explicit_request_windows_required" in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    assert "provider_feed_metadata_required" in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    assert (
        "latest_candle_freshness_clean_under_d11_8"
        in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    )
    assert "target_symbols_supported" in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    assert (
        "timezone_aware_utc_timestamps_required"
        in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    )
    assert (
        "no_strategy_risk_execution_coupling"
        in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    )
    assert (
        "no_broker_order_authority_through_data_path"
        in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    )
    assert (
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility"
        in D11_PRIMARY_PROVIDER_SELECTION_CRITERIA
    )


def test_provider_selection_module_has_no_network_client_or_authority_imports() -> None:
    import market_data_provider_selection

    source = Path(market_data_provider_selection.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "requests",
        "urllib",
        "from alpaca",
        "import alpaca",
        "from ib",
        "import ib",
        "from polygon",
        "import polygon",
        "from tiingo",
        "import tiingo",
        "from schwab",
        "import schwab",
        "subprocess",
        "import socket",
        "from socket",
        "open(",
        "get_stock_bars",
        "submit",
        "package_execution_orchestrator",
    ):
        assert forbidden not in source
    assert "no_credentials" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_network_api_calls" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_broker_api_authority" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_order_authority" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_execution_authority" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_package_capture" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_replay" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_scoring" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_candidate_generation" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY
    assert "no_unit_12_opening" in PROVIDER_SELECTION_AUTHORITY_BOUNDARY


def _valid_ibkr_diagnostic_result(**overrides):
    result = {
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": "IBKR read-only market-data diagnostic candidate",
        "connection_mode": "paper_read_only",
        "read_only": True,
        "requested_start": "2026-06-17T13:00:00+00:00",
        "requested_end": "2026-06-17T13:45:00+00:00",
        "symbol": "MSFT",
        "timeframe": "15Min",
        "latest_candle_timestamp": "2026-06-17T13:30:00+00:00",
        "lag_minutes": 15.0,
        "freshness_classification": FRESHNESS_CLEAN,
        "d11_countable": True,
        "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
        "d11_primary_eligible": False,
        "failure_reason": "",
        "authority_boundary": IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY,
        "credentials_configured": True,
        "account_capability": False,
        "order_capability": False,
        "position_capability": False,
        "portfolio_capability": False,
        "warnings": (),
    }
    result.update(overrides)
    return result


def test_ibkr_read_only_diagnostic_contract_is_metadata_only() -> None:
    contract = ibkr_read_only_diagnostic_contract()

    assert contract["provider_key"] == IBKR_PROVIDER_KEY
    assert contract["read_only"] is True
    assert contract["d11_primary_eligible"] is False
    assert contract["d11_status"] == D11_STATUS_INSUFFICIENT
    assert contract["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    for field in IBKR_DIAGNOSTIC_REQUIRED_OUTPUT_FIELDS:
        assert field in contract["required_output_fields"]
    assert "no_ibkr_client_imports" in IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY
    assert "no_order_place_modify_cancel_route" in (
        IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY
    )
    assert "no_unit_12_opening" in IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY
    assert "no_d11_completion_authority" in (
        IBKR_READ_ONLY_DIAGNOSTIC_AUTHORITY_BOUNDARY
    )


def test_ibkr_contract_module_has_no_client_network_or_systemd_imports() -> None:
    import ibkr_market_data_diagnostic_contract

    source = Path(ibkr_market_data_diagnostic_contract.__file__).read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "ibapi",
        "ib_insync",
        "import socket",
        "from socket",
        "requests",
        "urllib",
        "subprocess",
        "systemctl",
        "from ibapi",
        "import ibapi",
        "from ib_insync",
        "import ib_insync",
        "open(",
        "placeOrder",
        "cancelOrder",
        "reqPositions",
        "accountSummary",
    ):
        assert forbidden not in source


def test_ibkr_candidate_remains_no_order_execution_and_not_primary_eligible() -> None:
    candidate = get_provider_candidate("ibkr_market_data_candidate")

    assert candidate["order_authority"] is False
    assert candidate["execution_authority"] is False
    assert candidate["d11_primary_eligible"] is False
    assert candidate_can_count_for_d11(candidate) is False


def test_ibkr_contract_fail_closed_rules_reject_bad_results() -> None:
    cases = (
        (
            {"requested_start": None},
            "missing or non-UTC explicit request window",
        ),
        (
            {"requested_start": "2026-06-17T13:00:00"},
            "missing or non-UTC explicit request window",
        ),
        (
            {
                "latest_candle_timestamp": "2026-06-17T07:23:00+00:00",
                "lag_minutes": 382.0,
            },
            "stale latest candle",
        ),
        (
            {"warnings": ("farm disconnected",)},
            "warning-bearing diagnostic result",
        ),
        (
            {"account_capability": True},
            "account/order/position capability detected",
        ),
        (
            {"order_capability": True},
            "account/order/position capability detected",
        ),
        (
            {"connection_mode": "unavailable"},
            "unavailable TWS/Gateway or unauthorized connection mode",
        ),
        (
            {"credentials_configured": False},
            "credentials/config not present",
        ),
    )
    for overrides, reason in cases:
        evaluation = evaluate_ibkr_diagnostic_result(
            _valid_ibkr_diagnostic_result(**overrides)
        )
        assert evaluation["valid"] is False
        assert evaluation["failure_reason"] == reason
        assert evaluation["d11_status"] == D11_STATUS_INSUFFICIENT
        assert evaluation["unit_12_status"] == UNIT_12_STATUS_BLOCKED


def test_ibkr_contract_cannot_mark_d11_complete_or_open_unit_12() -> None:
    evaluation = evaluate_ibkr_diagnostic_result(_valid_ibkr_diagnostic_result())

    assert evaluation["valid"] is False
    assert "later separate governance record" in evaluation["failure_reason"]
    assert evaluation["d11_status"] == D11_STATUS_INSUFFICIENT
    assert evaluation["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert evaluation["package_capture"] is False
    assert evaluation["replay"] is False
    assert evaluation["scoring"] is False
    assert evaluation["candidate_generation"] is False
    assert evaluation["broker_api_authority"] is False
    assert evaluation["order_authority"] is False
    assert evaluation["execution_authority"] is False
    assert evaluation["d11_completion_authority"] is False


def test_ibkr_diagnostic_scaffold_output_is_fail_closed() -> None:
    result = build_scaffold_result(
        symbols=("MSFT",),
        timeframe="15Min",
        limit=5,
        requested_end=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        lookback_minutes=120,
    )

    row = result["results"][0]
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert row["provider_key"] == IBKR_PROVIDER_KEY
    assert row["connection_mode"] == "not_opened"
    assert row["read_only"] is True
    assert row["requested_start"] == "2026-06-17T11:45:00+00:00"
    assert row["requested_end"] == "2026-06-17T13:45:00+00:00"
    assert row["requested_start"] < row["requested_end"]
    assert row["latest_candle_timestamp"] is None
    assert row["lag_minutes"] is None
    assert row["freshness_classification"] == "unavailable"
    assert row["d11_countable"] is False
    assert row["d11_primary_candidate_status"] == CANDIDATE_STATUS_CANDIDATE
    assert row["d11_primary_eligible"] is False
    assert row["failure_reason"] == IBKR_DIAGNOSTIC_NOT_AUTHORIZED_REASON
    assert result["package_capture"] is False
    assert result["replay"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["broker_api_authority"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False
    assert result["d11_completion_authority"] is False


def test_ibkr_diagnostic_scaffold_cli_returns_fail_closed_json(capsys) -> None:
    from tools.ops.ibkr_market_data_freshness_diagnostic import main

    exit_code = main(
        [
            "--symbol",
            "msft",
            "--timeframe",
            "15Min",
            "--limit",
            "5",
            "--requested-end",
            "2026-06-17T13:45:00Z",
            "--lookback-minutes",
            "120",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"connection_mode": "not_opened"' in captured.out
    assert '"d11_countable": false' in captured.out
    assert '"d11_primary_eligible": false' in captured.out
    assert '"no_ibkr_connection"' in captured.out


def test_ibkr_diagnostic_scaffold_has_no_client_network_or_systemd_imports() -> None:
    import tools.ops.ibkr_market_data_freshness_diagnostic as scaffold

    source = Path(scaffold.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "ibapi",
        "ib_insync",
        "import socket",
        "from socket",
        "requests",
        "urllib",
        "subprocess",
        "systemctl",
        "from ibapi",
        "import ibapi",
        "from ib_insync",
        "import ib_insync",
        "open(",
        "placeOrder",
        "cancelOrder",
        "reqPositions",
        "accountSummary",
    ):
        assert forbidden not in source
    assert "no_ibkr_connection" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_tws_gateway_start" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_credentials_read" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_account_query" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_position_query" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_margin_query" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_portfolio_query" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_order_authority" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_execution_authority" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_package_capture" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_replay" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_scoring" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_candidate_generation" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_unit_12_opening" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY
    assert "no_d11_completion" in IBKR_DIAGNOSTIC_SCAFFOLD_AUTHORITY_BOUNDARY


def test_ibkr_read_only_implementation_design_is_metadata_only() -> None:
    design = ibkr_read_only_implementation_design()

    assert design["provider_key"] == IBKR_PROVIDER_KEY
    assert design["design_status"] == DESIGN_STATUS_DESIGN_ONLY
    assert design["d11_status"] == D11_STATUS_INSUFFICIENT
    assert design["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert design["d11_primary_eligible"] is False
    assert design["broker_api_authority"] is False
    assert design["order_authority"] is False
    assert design["execution_authority"] is False
    assert design["package_capture"] is False
    assert design["replay"] is False
    assert design["scoring"] is False
    assert design["candidate_generation"] is False
    assert design["credentials_read"] is False
    assert design["connection_opened"] is False
    assert design["tws_gateway_started"] is False
    assert design["account_query_authority"] is False
    assert design["position_query_authority"] is False
    assert design["margin_query_authority"] is False
    assert design["buying_power_query_authority"] is False
    assert design["portfolio_query_authority"] is False


def test_ibkr_read_only_implementation_design_config_contract_is_inert() -> None:
    expected_fields = {
        "host",
        "port",
        "client_id",
        "readonly_mode",
        "connection_mode",
        "market_data_type",
        "timeout_seconds",
        "symbols",
        "timeframe",
        "requested_start",
        "requested_end",
        "outside_rth",
        "exchange",
        "currency",
        "sec_type",
    }

    assert set(IBKR_CONNECTION_CONFIG_CONTRACT_FIELDS) == expected_fields
    design = ibkr_read_only_implementation_design()
    assert set(design["config_contract_fields"]) == expected_fields
    assert design["future_connection_config_contract"] == (
        design["config_contract_fields"]
    )
    assert design["requirements"] == design["implementation_requirements"]
    assert (
        "output_must_conform_to_d11_12_diagnostic_contract"
        in IBKR_READ_ONLY_IMPLEMENTATION_REQUIREMENTS
    )
    assert (
        "clean_d11_8_freshness_proof_required_before_primary_eligibility"
        in IBKR_READ_ONLY_IMPLEMENTATION_REQUIREMENTS
    )


def test_ibkr_read_only_implementation_design_status_vocabulary() -> None:
    assert IBKR_READ_ONLY_IMPLEMENTATION_DESIGN_STATUSES == (
        "design_only",
        "awaiting_local_authorization",
        "awaiting_manual_tws_gateway",
        "awaiting_credentials_configuration",
        "ready_for_local_read_only_smoke",
        "rejected",
    )


def test_ibkr_read_only_implementation_design_has_no_client_or_connection_code() -> None:
    import ibkr_read_only_implementation_design

    source = Path(ibkr_read_only_implementation_design.__file__).read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "ibapi",
        "ib_insync",
        "import socket",
        "from socket",
        "requests",
        "urllib",
        "subprocess",
        "systemctl",
        "from ibapi",
        "import ibapi",
        "from ib_insync",
        "import ib_insync",
        "connect(",
        "EClient",
        "EWrapper",
        "reqHistoricalData",
        "placeOrder",
        "cancelOrder",
        "reqPositions",
        "accountSummary",
        "os.getenv",
        "load_dotenv",
        "open(",
    ):
        assert forbidden not in source
    assert "no_connection_code" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_credentials_read" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_account_query" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_position_query" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_margin_query" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_buying_power_query" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_portfolio_query" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_order_authority" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_execution_authority" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_package_capture" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_replay" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_scoring" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_candidate_generation" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_unit_12_opening" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY
    assert "no_d11_completion" in IBKR_READ_ONLY_IMPLEMENTATION_AUTHORITY_BOUNDARY


def test_ibkr_scaffold_remains_fail_closed_after_design_gate() -> None:
    result = build_scaffold_result(
        symbols=("AAPL",),
        timeframe="15Min",
        limit=5,
        requested_end=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        lookback_minutes=120,
    )

    row = result["results"][0]
    assert row["connection_mode"] == "not_opened"
    assert row["d11_countable"] is False
    assert row["d11_primary_eligible"] is False
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert result["package_capture"] is False
    assert result["replay"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False


def test_ibkr_read_only_smoke_default_matches_fail_closed_scaffold(monkeypatch) -> None:
    import tools.ops.ibkr_market_data_read_only_smoke as smoke

    def fail_if_called():
        raise AssertionError("IBKR dependency loader must not be called")

    monkeypatch.setattr(smoke, "_load_ib_insync", fail_if_called)
    kwargs = {
        "symbols": ("MSFT",),
        "timeframe": "15Min",
        "limit": 5,
        "requested_end": datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        "lookback_minutes": 120,
    }

    assert build_smoke_result(**kwargs) == build_scaffold_result(**kwargs)


def test_ibkr_read_only_smoke_exports_public_run_smoke_diagnostic() -> None:
    from tools.ops.ibkr_market_data_read_only_smoke import run_smoke_diagnostic

    def fail_if_called():
        raise AssertionError("IBKR dependency loader must not be called")

    kwargs = {
        "symbols": ("MSFT",),
        "timeframe": "15Min",
        "requested_end": datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        "lookback_minutes": 120,
        "ibkr_dependency_loader": fail_if_called,
    }

    assert run_smoke_diagnostic(**kwargs) == build_scaffold_result(
        symbols=("MSFT",),
        timeframe="15Min",
        limit=5,
        requested_end=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        lookback_minutes=120,
    )


def test_ibkr_read_only_smoke_dependency_missing_fails_closed(monkeypatch) -> None:
    import tools.ops.ibkr_market_data_read_only_smoke as smoke

    def raise_missing_dependency():
        raise ImportError("ib_insync unavailable")

    monkeypatch.setattr(smoke, "_load_ib_insync", raise_missing_dependency)
    result = build_smoke_result(
        symbols=("TSLA",),
        timeframe="15Min",
        limit=5,
        requested_end=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        lookback_minutes=120,
        authorize_local_ibkr_read_only_smoke=True,
    )

    row = result["results"][0]
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert row["connection_mode"] == "local_read_only_smoke"
    assert row["requested_start"] == "2026-06-17T11:45:00+00:00"
    assert row["requested_end"] == "2026-06-17T13:45:00+00:00"
    assert row["latest_candle_timestamp"] is None
    assert row["lag_minutes"] is None
    assert row["freshness_classification"] == "unavailable"
    assert row["d11_countable"] is False
    assert row["d11_primary_eligible"] is False
    assert row["failure_reason"] == IBKR_READ_ONLY_SMOKE_DEPENDENCY_UNAVAILABLE_REASON
    assert result["package_capture"] is False
    assert result["replay"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["broker_api_authority"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False


def test_ibkr_read_only_smoke_public_api_dependency_missing_fails_closed() -> None:
    def raise_missing_dependency():
        raise ImportError("ib_insync unavailable")

    result = run_smoke_diagnostic(
        symbols=("TSLA",),
        timeframe="15Min",
        requested_end=datetime(2026, 6, 17, 13, 45, tzinfo=timezone.utc),
        lookback_minutes=120,
        authorize_local_ibkr_read_only_smoke=True,
        ibkr_dependency_loader=raise_missing_dependency,
    )

    row = result["results"][0]
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert row["connection_mode"] == "local_read_only_smoke"
    assert row["freshness_classification"] == "unavailable"
    assert row["d11_countable"] is False
    assert row["d11_primary_eligible"] is False
    assert row["failure_reason"] == IBKR_READ_ONLY_SMOKE_DEPENDENCY_UNAVAILABLE_REASON
    assert result["broker_api_authority"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False


def test_ibkr_read_only_smoke_after_hours_session_caveat_not_primary_eligible() -> None:
    class FakeIB:
        def __init__(self):
            self.connected = False

        def connect(self, *args, **kwargs):
            self.connected = True

        def reqHistoricalData(self, *args, **kwargs):
            return [
                SimpleNamespace(
                    date=datetime(2026, 6, 17, 19, 45, tzinfo=timezone.utc)
                )
            ]

        def isConnected(self):
            return self.connected

        def disconnect(self):
            self.connected = False

    fake_ibkr = SimpleNamespace(
        IB=FakeIB,
        Contract=lambda: SimpleNamespace(),
    )

    result = run_smoke_diagnostic(
        symbols=("AAPL",),
        timeframe="15Min",
        requested_end=datetime(2026, 6, 18, 2, 15, tzinfo=timezone.utc),
        lookback_minutes=120,
        authorize_local_ibkr_read_only_smoke=True,
        ibkr_dependency_loader=lambda: fake_ibkr,
    )

    row = result["results"][0]
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert row["connection_mode"] == "local_read_only_smoke"
    assert row["latest_candle_timestamp"] == "2026-06-17T19:45:00+00:00"
    assert row["freshness_classification"] == FRESHNESS_RECENCY_CAVEATED
    assert row["d11_countable"] is False
    assert row["d11_primary_eligible"] is False
    assert row["failure_reason"] == (
        "regular_session_closed_latest_candle_valid_for_last_session"
    )
    assert result["package_capture"] is False
    assert result["replay"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["broker_api_authority"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False


def test_ibkr_read_only_smoke_regular_session_clean_remains_not_primary_eligible() -> None:
    class FakeIB:
        def __init__(self):
            self.connected = False

        def connect(self, *args, **kwargs):
            self.connected = True

        def reqHistoricalData(self, *args, **kwargs):
            return [
                SimpleNamespace(
                    date=datetime(2026, 6, 18, 13, 45, tzinfo=timezone.utc)
                )
            ]

        def isConnected(self):
            return self.connected

        def disconnect(self):
            self.connected = False

    fake_ibkr = SimpleNamespace(
        IB=FakeIB,
        Contract=lambda: SimpleNamespace(),
    )

    result = run_smoke_diagnostic(
        symbols=("AAPL",),
        timeframe="15Min",
        requested_end=datetime(2026, 6, 18, 14, 0, 33, tzinfo=timezone.utc),
        lookback_minutes=120,
        authorize_local_ibkr_read_only_smoke=True,
        ibkr_dependency_loader=lambda: fake_ibkr,
    )

    row = result["results"][0]
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert row["connection_mode"] == "local_read_only_smoke"
    assert row["latest_candle_timestamp"] == "2026-06-18T13:45:00+00:00"
    assert row["freshness_classification"] == FRESHNESS_CLEAN
    assert row["d11_countable"] is True
    assert row["d11_primary_eligible"] is False
    assert row["failure_reason"] == ""
    assert result["package_capture"] is False
    assert result["replay"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["broker_api_authority"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False


def test_d11_19_optional_diagnostics_pin_and_no_primary_approval() -> None:
    base_requirements = (
        Path("requirements.txt").read_text(encoding="utf-8")
        + "\n"
        + Path("requirements-test.txt").read_text(encoding="utf-8")
    )
    diagnostics_requirements = Path("requirements-diagnostics.txt").read_text(
        encoding="utf-8"
    )
    assert "ib_insync" not in base_requirements
    assert diagnostics_requirements.splitlines() == ["ib_insync==0.9.86"]

    candidate = get_provider_candidate("ibkr_market_data_candidate")
    assert candidate["d11_primary_candidate_status"] == CANDIDATE_STATUS_CANDIDATE
    assert candidate["d11_primary_eligible"] is False
    assert candidate["order_authority"] is False
    assert candidate["execution_authority"] is False
    assert candidate_can_count_for_d11(candidate) is False

    contract_result = evaluate_ibkr_diagnostic_result(
        {
            "provider_key": IBKR_PROVIDER_KEY,
            "provider_name": "IBKR read-only market-data diagnostic candidate",
            "connection_mode": "gateway_read_only",
            "read_only": True,
            "requested_start": "2026-06-18T12:00:33+00:00",
            "requested_end": "2026-06-18T14:00:33+00:00",
            "symbol": "AAPL",
            "timeframe": "15Min",
            "latest_candle_timestamp": "2026-06-18T13:45:00+00:00",
            "lag_minutes": 15.5661366,
            "freshness_classification": FRESHNESS_CLEAN,
            "d11_countable": True,
            "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
            "d11_primary_eligible": False,
            "failure_reason": "",
            "authority_boundary": IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY,
            "credentials_configured": True,
        }
    )

    assert contract_result["valid"] is False
    assert contract_result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert contract_result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert "separate governance record" in contract_result["failure_reason"]
    assert contract_result["package_capture"] is False
    assert contract_result["replay"] is False
    assert contract_result["scoring"] is False
    assert contract_result["candidate_generation"] is False
    assert contract_result["broker_api_authority"] is False
    assert contract_result["order_authority"] is False
    assert contract_result["execution_authority"] is False


def test_d11_20_primary_provider_and_sufficiency_require_separate_approval() -> None:
    candidate = get_provider_candidate("ibkr_market_data_candidate")
    assert candidate["d11_primary_candidate_status"] == CANDIDATE_STATUS_CANDIDATE
    assert candidate["d11_primary_eligible"] is False
    assert candidate["credentials_configured"] is False
    assert candidate["order_authority"] is False
    assert candidate["execution_authority"] is False
    assert candidate_can_count_for_d11(candidate) is False

    clean_diagnostic = {
        "provider_key": IBKR_PROVIDER_KEY,
        "provider_name": "IBKR read-only market-data diagnostic candidate",
        "connection_mode": "gateway_read_only",
        "read_only": True,
        "requested_start": "2026-06-18T12:00:33+00:00",
        "requested_end": "2026-06-18T14:00:33+00:00",
        "symbol": "AAPL",
        "timeframe": "15Min",
        "latest_candle_timestamp": "2026-06-18T13:45:00+00:00",
        "lag_minutes": 15.5661366,
        "freshness_classification": FRESHNESS_CLEAN,
        "d11_countable": True,
        "d11_primary_candidate_status": CANDIDATE_STATUS_CANDIDATE,
        "d11_primary_eligible": False,
        "failure_reason": "",
        "authority_boundary": IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY,
        "credentials_configured": True,
    }
    result = evaluate_ibkr_diagnostic_result(clean_diagnostic)

    assert result["valid"] is False
    assert result["failure_reason"] == (
        "read-only diagnostic may pass freshness checks, but D11 primary "
        "eligibility requires a later separate governance record"
    )
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert result["d11_completion_authority"] is False
    assert result["package_capture"] is False
    assert result["replay"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["broker_api_authority"] is False
    assert result["order_authority"] is False
    assert result["execution_authority"] is False


def test_d11_21_repeatability_protocol_is_documented_without_authority() -> None:
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "### D11.21 IBKR Repeatability Evidence Plan" in map_text
    assert "at least **3 successful read-only diagnostic runs**" in map_text
    assert "3 distinct regular-session trading days" in map_text
    assert "AAPL, MSFT, NVDA, TSLA, and MSTR" in map_text
    assert "timeframe: `15Min`" in map_text
    assert "requested_start" in map_text
    assert "requested_end" in map_text
    assert "latest candle timestamp" in map_text
    assert "lag minutes" in map_text
    assert 'freshness_classification="clean"' in map_text
    assert "`d11_countable=true`" in map_text
    assert "ib_insync==0.9.86" in map_text
    assert "dirty worktree before or after the run" in map_text
    assert "dependency-version mismatch" in map_text
    assert "authority breach" in map_text
    assert "Repeatability evidence remains separate from D11 sufficiency" in map_text
    assert "D11 remains **INSUFFICIENT**" in map_text
    assert "IBKR primary eligibility remains **NOT APPROVED**" in map_text
    assert "Unit 12 remains **BLOCKED**" in map_text
    assert "does not authorize package capture, replay, scoring" in map_text


def test_d11_22_repeatability_ledger_records_run_1_without_primary_authority() -> None:
    ledger_path = Path("docs/ibkr_market_data_repeatability_ledger_template.md")
    ledger_text = ledger_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.22 IBKR Market-Data Repeatability Ledger Template" in ledger_text
    assert "`ledger_status` | `active_repeatability_ledger`" in ledger_text
    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert "`ibkr_provider_status` | `ibkr_market_data_candidate`" in ledger_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in ledger_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in ledger_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in ledger_text
    assert "`package_capture` | `BLOCKED`" in ledger_text
    assert "`order_authority` | `false`" in ledger_text
    assert "`execution_authority` | `false`" in ledger_text
    assert "`vps_runtime` | `PARKED`" in ledger_text
    assert (
        "| 1 | 2026-06-22 | "
        "b63d0d2d31b3023b07f7308c84e0ba2e4f38e931 | "
        "AAPL, MSFT, NVDA, TSLA, MSTR | 15Min | clean | true | completed |"
    ) in ledger_text
    assert "| _none_ | _none_ | _none_ | _none_ | _none_ |" in ledger_text
    assert (
        "| 2 | 2026-06-23 | "
        "43057a4b2689da57a1f7a6517159eaf4109f83ca | "
        "AAPL, MSFT, NVDA, TSLA, MSTR | 15Min | clean | true | completed |"
    ) in ledger_text
    assert (
        "| 3 | 2026-06-24 | "
        "8d3565208fcfeb62ad5230ada72a38a08852eb8b | "
        "AAPL, MSFT, NVDA, TSLA, MSTR | 15Min | clean | true | completed |"
    ) in ledger_text
    assert "### Run 3 Ledger Entry" in ledger_text
    assert "`run_sequence_number` | `3`" in ledger_text
    assert "`run_command_timestamp_utc` | `2026-06-24T14:10:56Z`" in ledger_text
    assert "`expected_source_commit` | `8d3565208fcfeb62ad5230ada72a38a08852eb8b`" in ledger_text
    assert "`observed_head` | `8d3565208fcfeb62ad5230ada72a38a08852eb8b`" in ledger_text
    assert "`requested_start` | `2026-06-24T12:00:00+00:00`" in ledger_text
    assert "`requested_end` | `2026-06-24T14:00:00+00:00`" in ledger_text
    assert "`latest_candle_timestamp` | `2026-06-24T13:45:00+00:00`" in ledger_text
    assert "`cleanup_authority` | `false`" in ledger_text
    assert "`flatten_authority` | `false`" in ledger_text
    assert "`sell_authority` | `false`" in ledger_text
    assert "`cancel_authority` | `false`" in ledger_text
    assert "`live_trading_authority` | `false`" in ledger_text
    assert "`run_sequence_number` | `2`" in ledger_text
    assert "`run_command_timestamp_utc` | `2026-06-23T14:11:28Z`" in ledger_text
    assert "`expected_source_commit` | `43057a4b2689da57a1f7a6517159eaf4109f83ca`" in ledger_text
    assert "`requested_start` | `2026-06-23T12:00:00+00:00`" in ledger_text
    assert "`requested_end` | `2026-06-23T14:00:00+00:00`" in ledger_text
    assert "`latest_candle_timestamp` | `2026-06-23T13:45:00+00:00`" in ledger_text
    assert "`run_command_timestamp_utc` | `2026-06-22T14:08:04Z`" in ledger_text
    assert "`supplement_timestamp_utc` | `2026-06-22T14:13:54Z`" in ledger_text
    assert "`expected_source_commit` | `b63d0d2d31b3023b07f7308c84e0ba2e4f38e931`" in ledger_text
    assert "`observed_head` | `b63d0d2d31b3023b07f7308c84e0ba2e4f38e931`" in ledger_text
    assert "`worktree_status_before_run` | `clean`" in ledger_text
    assert "`worktree_status_after_run` | `clean`" in ledger_text
    assert "`dependency_contract` | `requirements-diagnostics.txt / ib_insync==0.9.86`" in ledger_text
    assert "`observed_dependency` | `ib_insync==0.9.86`" in ledger_text
    assert "`no_rerun_performed` | `true`" in ledger_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in ledger_text
    assert "`timer_service` | `NOT_TOUCHED`" in ledger_text
    assert "`package_capture` | `BLOCKED`" in ledger_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in ledger_text
    assert "--symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR" in ledger_text
    assert "`result_type` | `ibkr_local_read_only_market_data_smoke`" in ledger_text
    assert "`provider_key` | `ibkr_market_data_candidate`" in ledger_text
    assert "`connection_mode` | `local_read_only_smoke`" in ledger_text
    assert "`read_only` | `true`" in ledger_text
    assert "`symbols` | `AAPL, MSFT, NVDA, TSLA, MSTR`" in ledger_text
    assert "`freshness_classification` | `clean`" in ledger_text
    assert "`d11_countable` | `true`" in ledger_text
    assert "`d11_primary_candidate_status` | `candidate`" in ledger_text
    assert "`d11_primary_eligible` | `false`" in ledger_text
    assert "`broker_api_authority` | `false`" in ledger_text
    assert "`order_authority` | `false`" in ledger_text
    assert "`execution_authority` | `false`" in ledger_text
    assert "`d11_completion_authority` | `false`" in ledger_text
    assert "`replay` | `false`" in ledger_text
    assert "`scoring` | `false`" in ledger_text
    assert "`candidate_generation` | `false`" in ledger_text
    assert "`package_capture_authority` | `false`" in ledger_text
    assert (
        "`account_position_margin_buying_power_portfolio_order_balance_execution_query` | `false`"
        in ledger_text
    )
    assert "does not approve IBKR as primary" in ledger_text
    assert "does not complete D11" in ledger_text
    assert "Stop and do not count the run" in ledger_text
    assert "Final Provider-Approval Review Template" in ledger_text
    assert "This runbook is not an authorization to run diagnostics" in ledger_text
    assert "does not authorize package capture, replay, scoring" in ledger_text
    assert "account, position, margin, buying power, portfolio" in ledger_text

    assert "docs/ibkr_market_data_repeatability_ledger_template.md" in map_text
    assert "D11.26 IBKR Repeatability Run 1 Ledger Recording" in map_text
    assert "### D11.30 IBKR Repeatability Run 2 Ledger Recording" in map_text
    assert "### D11.32 IBKR Repeatability Run 3 Ledger / Adjudication Update" in map_text
    assert "`completed_repeatability_runs=3`" in map_text
    assert "`invalidated_repeatability_runs=0`" in map_text
    assert "`NO_RERUN_PERFORMED=true`" in map_text
    assert "satisfy the D11.21 evidence-count and distinct-day\nrequirements only" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`ORDER_AUTHORITY=NONE`" in map_text
    assert "`EXECUTION_AUTHORITY=NONE`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_31_run_3_preflight_packet_preserves_repeatability_and_authority() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_repeatability_run_3_preflight_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    ledger_text = Path(
        "docs/ibkr_market_data_repeatability_ledger_template.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.31 IBKR Repeatability Run 3 Preflight Packet" in packet_text
    assert "control-packet preparation | `CODEX_LOCAL`" in packet_text
    assert "read-only diagnostic | `LOCAL_MAC` only" in packet_text
    assert "Post-commit source-controlled validation | `VPS` only" in packet_text
    assert "not run a diagnostic and does not approve one" in packet_text
    assert "separate explicit authorization" in packet_text
    assert "Market open is not required to prepare this packet" in packet_text
    assert "Broker/TWS is not involved in this preparation" in packet_text
    assert "`completed_repeatability_runs` | `2`" in packet_text
    assert "`invalidated_repeatability_runs` | `0`" in packet_text
    assert "`run_1_date` | `2026-06-22`" in packet_text
    assert "`run_2_date` | `2026-06-23`" in packet_text
    assert "`run_3_completed` | `false`" in packet_text
    assert "`run_3_invalidated` | `false`" in packet_text
    assert "distinct future U.S. equity regular-session trading" in packet_text
    assert "same read-only diagnostic scope" in packet_text
    assert "clean, countable, and free of warnings or failures" in packet_text
    assert "no authority expansion" in packet_text
    assert "repository branch, HEAD, origin alignment" in packet_text
    assert "working tree is dirty before intended" in packet_text
    assert "Run #1/Run #2/D11.27/D11.28/D11.29/" in packet_text
    assert "broker, runtime, VPS, systemd, scheduler, strategy, risk, or execution" in packet_text
    assert "order, account, submit, cancel, flatten, sell, cleanup, or remediation" in packet_text
    assert "`PASS`" in packet_text
    assert "`BLOCKED`" in packet_text
    assert "`BUG`" in packet_text
    assert "`PARKED`" in packet_text
    assert "does not perform Run #3" in packet_text
    assert "does not approve IBKR as primary" in packet_text
    assert "does not complete D11" in packet_text
    assert "unblock Unit 12" in packet_text
    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert "### D11.31 IBKR Repeatability Run 3 Preflight Packet" in map_text
    assert str(packet_path) in map_text
    assert "D11.32 IBKR Repeatability Run 3 Ledger / Adjudication Update" in map_text
    assert "`completed_repeatability_runs=3`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text


def test_d11_33_evidence_count_completion_preserves_sufficiency_boundaries() -> None:
    ledger_text = Path(
        "docs/ibkr_market_data_repeatability_ledger_template.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert "| 1 | 2026-06-22 |" in ledger_text
    assert "| 2 | 2026-06-23 |" in ledger_text
    assert "| 3 | 2026-06-24 |" in ledger_text
    assert "### D11.33 Evidence-Count Completion / Sufficiency-Boundary Review" in map_text
    assert "`completed_repeatability_runs=3`" in map_text
    assert "`invalidated_repeatability_runs=0`" in map_text
    assert "completes the\nD11.21 three-run evidence-count and distinct-day requirement only" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`ibkr_market_data_candidate`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text
    assert "separately authorized final\nprovider-approval review" in map_text
    assert "remains separate from\nD11 sufficiency, Unit 12" in map_text
    assert "package capture, replay, scoring" in map_text
    assert "candidate generation, broker/API or account/position/margin/buying-power/" in map_text
    assert "portfolio/order/balance/execution queries" in map_text
    assert "runtime, timer, service, systemd,\nstrategy, risk, execution, orders, cleanup, flatten, sell, cancel, or live\ntrading" in map_text
    assert "`EVIDENCE_COUNT_COMPLETE`" in map_text
    assert "`IBKR_CANDIDATE_ONLY`" in map_text


def test_d11_34_final_provider_review_is_not_approved_without_vps_proof() -> None:
    ledger_text = Path(
        "docs/ibkr_market_data_repeatability_ledger_template.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert "### D11.34 Final IBKR Market-Data Provider-Approval Review" in map_text
    assert "Decision: `NOT_APPROVED`" in map_text
    assert "D11.11 requires a separate VPS read-only freshness proof before primary\neligibility" in map_text
    assert "accepted repeatability evidence is `LOCAL_MAC` only" in map_text
    assert "no\nseparate VPS proof is recorded" in map_text
    assert "diagnostic credentials/configuration status without storing\ncredentials" in map_text
    assert "`ibkr_market_data_candidate`" in map_text
    assert "`d11_primary_candidate_status=candidate`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "D11 remains `D11_INSUFFICIENT`" in map_text
    assert "Unit 12 remains `UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text
    assert "no\npackage capture, replay, scoring, candidate generation" in map_text
    assert "broker/API or account/\nposition/margin/buying-power/portfolio/order/balance/execution query" in map_text
    assert "runtime,\ntimer, service, systemd, strategy, risk, execution, order, cleanup, flatten,\nsell, cancel, or live-trading authority" in map_text
    assert "separately authorized VPS read-only freshness\nproof" in map_text
    assert "remains separate from D11 sufficiency, Unit 12, package\ncapture, replay, scoring, candidate generation" in map_text


def test_d11_35_vps_freshness_control_prep_preserves_all_boundaries() -> None:
    packet_path = Path("docs/ibkr_market_data_vps_freshness_preflight_packet.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.35 VPS Read-Only Freshness Proof / Credential-Configuration Control Prep" in packet_text
    assert "source-controlled control preparation only" in packet_text
    assert "does not run a\nVPS proof" in packet_text
    assert "`vps_freshness_proof_run` | `false`" in packet_text
    assert "`credential_configuration_recorded` | `false`" in packet_text
    assert "`credentials_stored_in_repository` | `false`" in packet_text
    assert "existing `tools.ops.ibkr_market_data_read_only_smoke` command is explicitly\nlocal-only" in packet_text
    assert "No VPS diagnostic command is currently authorized" in packet_text
    assert "`requirements-diagnostics.txt` and\n  `ib_insync==0.9.86`" in packet_text
    assert "no credential value is\n  printed or committed" in packet_text
    assert "`secrets_captured=false`" in packet_text
    assert "`execution_context=VPS`, `read_only=true`" in packet_text
    assert "`vps_runtime=NOT_TOUCHED`" in packet_text
    assert "`timer_service=NOT_TOUCHED`" in packet_text
    assert "`package_capture=false`, `replay=false`, `scoring=false`" in packet_text
    assert "`candidate_generation=false`, `broker_api_authority=false`" in packet_text
    assert "`order_authority=false`, `execution_authority=false`" in packet_text
    assert "`d11_completion_authority=false`" in packet_text
    assert "must not\nquery account, position, margin, buying power, portfolio, order, balance, or\nexecution state" in packet_text
    assert "place, modify, route, cancel, flatten, sell, or\notherwise trade" in packet_text
    assert "No exact VPS command exists yet" in packet_text
    assert "<approved-vps-read-only-diagnostic-module>" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `PARKED`" in packet_text
    assert "D11.35 does not authorize provider approval, D11 completion, Unit 12 opening" in packet_text
    assert "separate authorization of the VPS-specific\nread-only command contract and the bounded VPS proof" in packet_text

    assert "### D11.35 VPS Read-Only Freshness Proof / Credential-Configuration Control Prep" in map_text
    assert str(packet_path) in map_text
    assert "It records no VPS proof and no credentials" in map_text
    assert "local-only and cannot be used as a VPS command" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_36_vps_command_contract_is_prep_only_and_non_secret() -> None:
    packet_path = Path("docs/ibkr_market_data_vps_read_only_command_contract.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.36 VPS Read-Only Market-Data Freshness Command Contract" in packet_text
    assert "source-controlled command contract only" in packet_text
    assert "does not implement the\nnamed module, run a VPS proof" in packet_text
    assert "`vps_freshness_proof_run` | `false`" in packet_text
    assert "`credential_configuration_recorded` | `false`" in packet_text
    assert "`credentials_stored_in_repository` | `false`" in packet_text
    assert "local-only `tools.ops.ibkr_market_data_read_only_smoke` module" in packet_text
    assert "explicitly prohibited from\nthis VPS contract" in packet_text
    assert "/opt/openclaw-stocks/venv/bin/python -m tools.ops.ibkr_market_data_vps_read_only_freshness_proof" in packet_text
    assert "--repo-root /opt/openclaw-stocks" in packet_text
    assert "--expected-source-commit <authorized-40-hex-commit>" in packet_text
    assert "--execution-context VPS" in packet_text
    assert "--symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR" in packet_text
    assert "--timeframe 15Min --requested-end <authorized-utc-z> --lookback-minutes 120" in packet_text
    assert "--authorize-vps-ibkr-read-only-freshness-proof" in packet_text
    assert "neither is implemented or\nauthorized by D11.36" in packet_text
    assert "`credentials_stored_in_repository=false`, `credential_values_emitted=false`" in packet_text
    assert "`secrets_captured=false`" in packet_text
    assert "`execution_context=VPS`, `repo_root=/opt/openclaw-stocks`" in packet_text
    assert "`connection_mode=vps_read_only_historical_market_data`" in packet_text
    assert "`vps_runtime=NOT_TOUCHED`" in packet_text
    assert "`package_capture=false`, `replay=false`" in packet_text
    assert "`broker_api_authority=false`,\n`account_query_authority=false`" in packet_text
    assert "`cleanup_authority=false`" in packet_text
    assert "`flatten_authority=false`" in packet_text
    assert "`sell_authority=false`" in packet_text
    assert "`cancel_authority=false`" in packet_text
    assert "`live_trading_authority=false`" in packet_text
    assert "must not read\nor print secrets; query account, position, margin, buying power, portfolio" in packet_text
    assert "place, modify, route, cancel, flatten,\nsell, or otherwise trade" in packet_text
    assert "capture packages, replay, score, generate\ncandidates, mutate timer/service/systemd/runtime state" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `PARKED`" in packet_text
    assert "separate authorization to implement or otherwise approve\nthis VPS-specific command contract and execute one bounded VPS proof" in packet_text

    assert "### D11.36 VPS-Specific Read-Only Diagnostic Command Contract" in map_text
    assert str(packet_path) in map_text
    assert "neither implements nor authorizes the command, runs no VPS\nproof" in map_text
    assert "its `venv` Python path" in map_text
    assert ".venv-312 Python path" not in map_text
    assert "does not permit the local-only IBKR smoke command on VPS" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_37_vps_read_only_proof_is_fail_closed_and_preserves_boundaries() -> None:
    import tools.ops.ibkr_market_data_vps_read_only_freshness_proof as proof

    module_path = Path(proof.__file__)
    source = module_path.read_text(encoding="utf-8")
    packet_text = Path(
        "docs/ibkr_market_data_vps_read_only_implementation_packet.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")
    result = build_vps_read_only_freshness_proof(
        repo_root=VPS_REPO_ROOT,
        expected_source_commit="a" * 40,
        execution_context="VPS",
        symbols=("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"),
        timeframe="15Min",
        requested_end=datetime(2026, 6, 24, 14, 0, tzinfo=timezone.utc),
        lookback_minutes=120,
        host="127.0.0.1",
        port=7497,
        client_id=9118,
        exchange="SMART",
        currency="USD",
        sec_type="STK",
        timeout_seconds=10,
    )

    assert module_path.name == "ibkr_market_data_vps_read_only_freshness_proof.py"
    assert "--authorize-vps-ibkr-read-only-freshness-proof" in source
    assert result["vps_freshness_proof_run"] is False
    assert json.dumps(result, indent=2, sort_keys=True)
    assert result["failure_reason"] == (
        "explicit --authorize-vps-ibkr-read-only-freshness-proof flag required"
    )
    assert result["credential_configuration_status"] == (
        "operator_managed_tws_gateway_session_attested"
    )
    assert result["credentials_stored_in_repository"] is False
    assert result["credential_values_emitted"] is False
    assert result["secrets_captured"] is False
    assert result["ibkr_primary_eligibility"] == "NOT_APPROVED"
    assert result["d11_primary_candidate_status"] == CANDIDATE_STATUS_CANDIDATE
    assert result["d11_primary_eligible"] is False
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT
    assert result["unit_12_status"] == UNIT_12_STATUS_BLOCKED
    assert result["vps_runtime"] == "NOT_TOUCHED"
    for field in (
        "package_capture", "replay", "scoring", "candidate_generation",
        "broker_api_authority", "account_query_authority", "order_authority",
        "execution_authority", "cleanup_authority", "flatten_authority",
        "sell_authority", "cancel_authority", "live_trading_authority",
        "d11_completion_authority",
    ):
        assert result[field] is False
    assert "no_account_query" in VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY
    assert "no_order_placement" in VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY
    assert "no_package_capture" in VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY
    assert "no_replay" in VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY
    assert "no_timer_service_systemd_runtime_mutation" in VPS_READ_ONLY_PROOF_AUTHORITY_BOUNDARY
    assert "D11.37 VPS Read-Only Freshness Proof Implementation Packet" in packet_text
    assert "No VPS proof has been run by D11.37" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=PARKED`" in packet_text
    assert "### D11.37 VPS Read-Only Freshness Proof Implementation" in map_text
    assert "D11.37 does not run a VPS proof or approve IBKR" in map_text


def test_d11_37_vps_read_only_proof_enforces_vps_root_and_context_without_connecting() -> None:
    kwargs = {
        "repo_root": VPS_REPO_ROOT,
        "expected_source_commit": "b" * 40,
        "execution_context": "VPS",
        "symbols": ("AAPL",),
        "timeframe": "15Min",
        "requested_end": datetime(2026, 6, 24, 14, 0, tzinfo=timezone.utc),
        "lookback_minutes": 120,
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 9118,
        "exchange": "SMART",
        "currency": "USD",
        "sec_type": "STK",
        "timeout_seconds": 10,
    }
    wrong_context = build_vps_read_only_freshness_proof(
        **{**kwargs, "execution_context": "LOCAL_MAC"}
    )
    wrong_root = build_vps_read_only_freshness_proof(
        **{**kwargs, "repo_root": "/tmp/openclaw-stocks"}
    )

    assert wrong_context["failure_reason"] == "execution_context must be VPS"
    assert wrong_context["vps_freshness_proof_run"] is False
    assert wrong_root["failure_reason"] == "repo_root must be /opt/openclaw-stocks"
    assert wrong_root["vps_freshness_proof_run"] is False


def test_d11_37_authorized_path_records_source_state_with_injected_historical_read(monkeypatch) -> None:
    import tools.ops.ibkr_market_data_vps_read_only_freshness_proof as proof

    expected_commit = "c" * 40
    monkeypatch.setattr(proof, "_pinned_dependency_contract_present", lambda _: True)

    def inspect(_: str) -> dict[str, str]:
        return {
            "branch": "main",
            "observed_head": expected_commit,
            "worktree_status": "clean",
        }

    def fetch(**_: object) -> datetime:
        return datetime(2026, 6, 24, 13, 45, tzinfo=timezone.utc)

    result = proof.build_vps_read_only_freshness_proof(
        repo_root=VPS_REPO_ROOT,
        expected_source_commit=expected_commit,
        execution_context="VPS",
        symbols=("AAPL",),
        timeframe="15Min",
        requested_end=datetime(2026, 6, 24, 14, 0, tzinfo=timezone.utc),
        lookback_minutes=120,
        host="127.0.0.1",
        port=7497,
        client_id=9118,
        exchange="SMART",
        currency="USD",
        sec_type="STK",
        timeout_seconds=10,
        authorize_vps_ibkr_read_only_freshness_proof=True,
        repo_state_inspector=inspect,
        ibkr_dependency_loader=lambda: SimpleNamespace(__version__="0.9.86"),
        historical_fetcher=fetch,
    )

    assert result["vps_freshness_proof_run"] is True
    assert result["branch"] == "main"
    assert result["observed_head"] == expected_commit
    assert result["worktree_status_before_run"] == "clean"
    assert result["branch_after_run"] == "main"
    assert result["observed_head_after_run"] == expected_commit
    assert result["worktree_status_after_run"] == "clean"
    assert result["results"][0]["d11_countable"] is True
    assert result["results"][0]["latest_candle_timestamp"] == "2026-06-24T13:45:00+00:00"
    assert isinstance(result["results"][0]["latest_candle_timestamp"], str)
    assert json.dumps(result, indent=2, sort_keys=True)
    assert result["results"][0]["d11_primary_eligible"] is False
    assert result["d11_status"] == D11_STATUS_INSUFFICIENT


def test_d11_38_vps_proof_authorization_packet_is_bounded_and_not_executed() -> None:
    packet_path = Path("docs/ibkr_market_data_vps_proof_authorization_packet.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.38 Bounded VPS Read-Only Freshness Proof Authorization Packet" in packet_text
    assert "source-controlled preparation for one later bounded VPS" in packet_text
    assert "`vps_freshness_proof_run` | `false`" in packet_text
    assert "`expected_source_commit` | `c175ac79191d6d82291dea27aaa1976c8bb6ca50`" in packet_text
    assert "`execution_context` | `VPS`" in packet_text
    assert "`repo_root` | `/opt/openclaw-stocks`" in packet_text
    assert "`python_path` | `/opt/openclaw-stocks/venv/bin/python`" in packet_text
    assert "--expected-source-commit c175ac79191d6d82291dea27aaa1976c8bb6ca50" in packet_text
    assert "--execution-context VPS" in packet_text
    assert "--authorize-vps-ibkr-read-only-freshness-proof" in packet_text
    assert "--symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR" in packet_text
    assert "--timeframe 15Min --requested-end <authorized-regular-session-utc-z> --lookback-minutes 120" in packet_text
    assert "--exchange SMART --currency USD" in packet_text
    assert "--sec-type STK --timeout-seconds 10" in packet_text
    assert "`requirements-diagnostics.txt / ib_insync==0.9.86`" in packet_text
    assert "credential_configuration_status=operator_managed_tws_gateway_session_attested" in packet_text
    assert "credentials_stored_in_repository=false" in packet_text
    assert "credential_values_emitted=false" in packet_text
    assert "secrets_captured=false" in packet_text
    assert "`vps_runtime=NOT_TOUCHED`" in packet_text
    assert "`timer_service=NOT_TOUCHED`" in packet_text
    assert "`package_capture=false`, `replay=false`, `scoring=false`" in packet_text
    assert "`candidate_generation=false`, `broker_api_authority=false`" in packet_text
    assert "`account_query_authority=false`, `order_authority=false`" in packet_text
    assert "`cleanup_authority=false`" in packet_text
    assert "`flatten_authority=false`" in packet_text
    assert "`sell_authority=false`" in packet_text
    assert "`cancel_authority=false`" in packet_text
    assert "`live_trading_authority=false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime_before_proof` | `PARKED`" in packet_text
    assert "does not approve IBKR, complete D11, unblock Unit 12" in packet_text
    assert "runtime-parameter addendum" in packet_text

    assert "### D11.38 Bounded VPS Read-Only Freshness Proof Authorization Packet" in map_text
    assert str(packet_path) in map_text
    assert "`c175ac79191d6d82291dea27aaa1976c8bb6ca50`" in map_text
    assert "`/opt/openclaw-stocks/venv/bin/python`" in map_text
    assert "No proof has run and no credentials are" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_39_runtime_parameter_addendum_is_pending_and_non_executable() -> None:
    packet_path = Path("docs/ibkr_market_data_vps_runtime_parameter_addendum.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.39 Narrow VPS Runtime-Parameter Addendum" in packet_text
    assert "runtime-parameter addendum only" in packet_text
    assert "`addendum_status` | `PREPARED_PENDING_OPERATOR_RUNTIME_VALUES`" in packet_text
    assert "`vps_freshness_proof_run` | `false`" in packet_text
    assert "proof command is not executable" in packet_text
    assert "`expected_source_commit` | `0fb3f459c519b622ed49a6dea580782242b93365`" in packet_text
    assert "`repo_root` | `/opt/openclaw-stocks`" in packet_text
    assert "`python_path` | `/opt/openclaw-stocks/venv/bin/python`" in packet_text
    assert "`execution_context` | `VPS`" in packet_text
    assert "`authorized_regular_session_utc_z` | `PENDING_OPERATOR_CONFIRMATION`" in packet_text
    assert "`authorized_vps_local_endpoint` | `PENDING_OPERATOR_CONFIRMATION`" in packet_text
    assert "`authorized_port` | `PENDING_OPERATOR_CONFIRMATION`" in packet_text
    assert "`authorized_read_only_client_id` | `PENDING_OPERATOR_CONFIRMATION`" in packet_text
    assert "--expected-source-commit 0fb3f459c519b622ed49a6dea580782242b93365" in packet_text
    assert "--execution-context VPS" in packet_text
    assert "--requested-end <authorized_regular_session_utc_z>" in packet_text
    assert "--authorize-vps-ibkr-read-only-freshness-proof" in packet_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in packet_text
    assert "Official market open is not the D11 diagnostic target" in packet_text
    assert "credential_configuration_status=operator_managed_tws_gateway_session_attested" in packet_text
    assert "credentials_stored_in_repository=false" in packet_text
    assert "credential_values_emitted=false" in packet_text
    assert "secrets_captured=false" in packet_text
    assert "`vps_runtime=NOT_TOUCHED`, `timer_service=NOT_TOUCHED`" in packet_text
    assert "`package_capture=false`, `replay=false`, `scoring=false`" in packet_text
    assert "`candidate_generation=false`, `broker_api_authority=false`" in packet_text
    assert "`account_query_authority=false`, `order_authority=false`" in packet_text
    assert "`cleanup_authority=false`" in packet_text
    assert "`flatten_authority=false`" in packet_text
    assert "`sell_authority=false`" in packet_text
    assert "`cancel_authority=false`" in packet_text
    assert "`live_trading_authority=false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime_before_proof` | `PARKED`" in packet_text
    assert "does not approve IBKR, complete D11, unblock Unit 12" in packet_text
    assert "pending runtime values with operator-confirmed values" in packet_text

    assert "### D11.39 Narrow VPS Runtime-Parameter Addendum" in map_text
    assert str(packet_path) in map_text
    assert "`0fb3f459c519b622ed49a6dea580782242b93365`" in map_text
    assert "`/opt/openclaw-stocks/venv/bin/python`" in map_text
    assert "at or after 7:00 AM\nPacific / 10:00 AM Eastern" in map_text
    assert "official market open is not the D11 diagnostic\ntarget" in map_text
    assert "`PREPARED_PENDING_OPERATOR_RUNTIME_VALUES`" in map_text
    assert "command is not executable" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_40_runtime_value_confirmation_is_bounded_and_not_executed() -> None:
    packet_path = Path("docs/ibkr_market_data_vps_runtime_value_confirmation.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.40 VPS Runtime-Value Confirmation" in packet_text
    assert "runtime-value confirmation only" in packet_text
    assert "`confirmation_status` | `RUNTIME_VALUES_CONFIRMED_PROOF_NOT_RUN`" in packet_text
    assert "`vps_freshness_proof_run` | `false`" in packet_text
    assert "`expected_source_commit` | `5e2d07110080a90b7d9f9d6f4a37c06f7e56c7b9`" in packet_text
    assert "`repo_root` | `/opt/openclaw-stocks`" in packet_text
    assert "`python_path` | `/opt/openclaw-stocks/venv/bin/python`" in packet_text
    assert "`execution_context` | `VPS`" in packet_text
    assert "`authorized_regular_session_utc_z` | `2026-06-24T14:00:00Z`" in packet_text
    assert "`authorized_vps_local_endpoint` | `127.0.0.1`" in packet_text
    assert "`authorized_port` | `7497`" in packet_text
    assert "`authorized_read_only_client_id` | `9118`" in packet_text
    assert "7:00 AM Pacific / 10:00 AM\nEastern" in packet_text
    assert "Official market open is not the D11 diagnostic target" in packet_text
    assert "exact future command is now source-controlled" in packet_text
    assert "does not execute\nit" in packet_text
    assert "--expected-source-commit 5e2d07110080a90b7d9f9d6f4a37c06f7e56c7b9" in packet_text
    assert "--execution-context VPS" in packet_text
    assert "--requested-end 2026-06-24T14:00:00Z" in packet_text
    assert "--host 127.0.0.1 --port 7497" in packet_text
    assert "--client-id 9118 --exchange SMART --currency USD" in packet_text
    assert "--authorize-vps-ibkr-read-only-freshness-proof" in packet_text
    assert "credential_configuration_status=operator_managed_tws_gateway_session_attested" in packet_text
    assert "credentials_stored_in_repository=false" in packet_text
    assert "credential_values_emitted=false" in packet_text
    assert "secrets_captured=false" in packet_text
    assert "`vps_runtime=NOT_TOUCHED`, `timer_service=NOT_TOUCHED`" in packet_text
    assert "`package_capture=false`, `replay=false`, `scoring=false`" in packet_text
    assert "`candidate_generation=false`, `broker_api_authority=false`" in packet_text
    assert "`account_query_authority=false`, `order_authority=false`" in packet_text
    assert "`cleanup_authority=false`" in packet_text
    assert "`flatten_authority=false`" in packet_text
    assert "`sell_authority=false`" in packet_text
    assert "`cancel_authority=false`" in packet_text
    assert "`live_trading_authority=false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime_before_proof` | `PARKED`" in packet_text
    assert "does not approve IBKR, complete D11, unblock Unit 12" in packet_text
    assert "does not permit account, position" in packet_text
    assert "separate operator terminal step on the VPS" in packet_text

    assert "### D11.40 VPS Runtime-Value Confirmation" in map_text
    assert str(packet_path) in map_text
    assert "`5e2d07110080a90b7d9f9d6f4a37c06f7e56c7b9`" in map_text
    assert "`/opt/openclaw-stocks/venv/bin/python`" in map_text
    assert "`authorized_regular_session_utc_z=2026-06-24T14:00:00Z`" in map_text
    assert "`authorized_vps_local_endpoint=127.0.0.1`" in map_text
    assert "`authorized_port=7497`" in map_text
    assert "`authorized_read_only_client_id=9118`" in map_text
    assert "official market open is not the D11 diagnostic target" in map_text
    assert "future command\nis now source-controlled but has not been executed" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_41_next_session_runtime_value_update_is_bounded_and_not_executed() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_next_session_runtime_value_update.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.41 Next-Session VPS Runtime-Value Update" in packet_text
    assert "next-session runtime-value update only" in packet_text
    assert (
        "`update_status` | `NEXT_SESSION_RUNTIME_VALUES_CONFIRMED_PROOF_NOT_RUN`"
        in packet_text
    )
    assert "`vps_freshness_proof_run` | `false`" in packet_text
    assert "`prior_bounded_proof_attempt_run` | `false`" in packet_text
    assert "`prior_failure_reason` | `ib_insync dependency unavailable`" in packet_text
    assert "`expected_source_commit` | `c90168d0c655c88183bdac03c4f5de2898387428`" in packet_text
    assert "`repo_root` | `/opt/openclaw-stocks`" in packet_text
    assert "`python_path` | `/opt/openclaw-stocks/venv/bin/python`" in packet_text
    assert "`execution_context` | `VPS`" in packet_text
    assert "`python_version_ready_after_hours` | `Python 3.12.3`" in packet_text
    assert (
        "`dependency_readiness_after_hours_verified` | "
        "`requirements-diagnostics.txt / ib_insync==0.9.86`" in packet_text
    )
    assert "`dependency_readiness_is_proof_evidence` | `false`" in packet_text
    assert "`vps_boundary_validation_after_hours` | `60 passed`" in packet_text
    assert "`superseded_authorized_regular_session_utc_z` | `2026-06-24T14:00:00Z`" in packet_text
    assert "`authorized_regular_session_utc_z` | `2026-06-25T14:00:00Z`" in packet_text
    assert "`authorized_vps_local_endpoint` | `127.0.0.1`" in packet_text
    assert "`authorized_port` | `7497`" in packet_text
    assert "`authorized_read_only_client_id` | `9118`" in packet_text
    assert "7:00 AM Pacific\n/ 10:00 AM Eastern" in packet_text
    assert "Official market open is not the D11\ndiagnostic target" in packet_text
    assert "after-hours VPS dependency readiness record only clears" in packet_text
    assert "is not market-data proof evidence" in packet_text
    assert "exact future command is source-controlled" in packet_text
    assert "D11.41 does not execute it" in packet_text
    assert "--expected-source-commit c90168d0c655c88183bdac03c4f5de2898387428" in packet_text
    assert "--execution-context VPS" in packet_text
    assert "--requested-end 2026-06-25T14:00:00Z" in packet_text
    assert "--host 127.0.0.1 --port 7497" in packet_text
    assert "--client-id 9118 --exchange SMART --currency USD" in packet_text
    assert "--authorize-vps-ibkr-read-only-freshness-proof" in packet_text
    assert "credential_configuration_status=operator_managed_tws_gateway_session_attested" in packet_text
    assert "credentials_stored_in_repository=false" in packet_text
    assert "credential_values_emitted=false" in packet_text
    assert "secrets_captured=false" in packet_text
    assert "`vps_runtime=NOT_TOUCHED`, `timer_service=NOT_TOUCHED`" in packet_text
    assert "`package_capture=false`, `replay=false`, `scoring=false`" in packet_text
    assert "`candidate_generation=false`, `broker_api_authority=false`" in packet_text
    assert "`account_query_authority=false`, `order_authority=false`" in packet_text
    assert "`cleanup_authority=false`" in packet_text
    assert "`flatten_authority=false`" in packet_text
    assert "`sell_authority=false`" in packet_text
    assert "`cancel_authority=false`" in packet_text
    assert "`live_trading_authority=false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime_before_proof` | `PARKED`" in packet_text
    assert "does not approve IBKR, complete D11, unblock Unit 12" in packet_text
    assert "does not permit account, position" in packet_text
    assert "separate operator terminal step on the VPS" in packet_text

    assert "### D11.41 Next-Session VPS Runtime-Value Update" in map_text
    assert str(packet_path) in map_text
    assert "`vps_freshness_proof_run=false`" in map_text
    assert "`ib_insync` was unavailable" in map_text
    assert "`/opt/openclaw-stocks/venv/bin/python`" in map_text
    assert "Python 3.12.3" in map_text
    assert "`requirements-diagnostics.txt / ib_insync==0.9.86`" in map_text
    assert "`60 passed`" in map_text
    assert "after-hours readiness is not proof evidence" in map_text
    assert "`2026-06-24T14:00:00Z`" in map_text
    assert "`2026-06-25T14:00:00Z`" in map_text
    assert "`127.0.0.1`" in map_text
    assert "`7497`" in map_text
    assert "`9118`" in map_text
    assert "`c90168d0c655c88183bdac03c4f5de2898387428`" in map_text
    assert "`/opt/openclaw-stocks`" in map_text
    assert "execution context `VPS`" in map_text
    assert "official market open is not the D11 diagnostic target" in map_text
    assert "future command\nis source-controlled but has not been executed" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_42_vps_connection_refused_adjudication_is_non_countable() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_proof_connection_refused_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.42 VPS Read-Only Freshness Proof Connection-Refused Adjudication"
        in packet_text
    )
    assert "`adjudication_status` | `PROOF_RUN_BUT_NON_COUNTABLE`" in packet_text
    assert "`vps_freshness_proof_run` | `true`" in packet_text
    assert "`d11_countable_evidence_produced` | `false`" in packet_text
    assert "`provider_approval_evidence` | `false`" in packet_text
    assert "`root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert (
        "`authorized_endpoint_status` | "
        "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert (
        "`observed_gateway_context` | "
        "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in packet_text
    )
    assert "`desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE`" in packet_text
    assert (
        "`broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE`"
        in packet_text
    )
    assert "`top_level_failure_reason` | `empty`" in packet_text
    assert "`execution_context` | `VPS`" in packet_text
    assert "`authorized_pacific` | `2026-06-25 07:00:00 PDT`" in packet_text
    assert "`authorized_utc` | `2026-06-25 14:00:00 UTC`" in packet_text
    assert "2026-06-25 14:12:49 UTC; 2026-06-25 14:13:35 UTC" in packet_text
    assert "`expected_source_commit` | `04e856c8a8d3387ccf2b0af5e55b493ea853a401`" in packet_text
    assert "`observed_head` | `04e856c8a8d3387ccf2b0af5e55b493ea853a401`" in packet_text
    assert "`branch` | `main`" in packet_text
    assert "`repo_root` | `/opt/openclaw-stocks`" in packet_text
    assert "`worktree_status_before_run` | `clean`" in packet_text
    assert "`worktree_status_after_run` | `clean`" in packet_text
    assert "`dependency_contract` | `requirements-diagnostics.txt / ib_insync==0.9.86`" in packet_text
    assert "`observed_dependency` | `ib_insync==0.9.86`" in packet_text
    assert "`requested_start` | `2026-06-25T12:00:00+00:00`" in packet_text
    assert "`requested_end` | `2026-06-25T14:00:00+00:00`" in packet_text
    assert "`symbols` | `AAPL, MSFT, NVDA, TSLA, MSTR`" in packet_text
    assert "`timeframe` | `15Min`" in packet_text
    assert "`host` | `127.0.0.1`" in packet_text
    assert "`port` | `7497`" in packet_text
    assert "`read_only` | `true`" in packet_text
    assert "API connection failed: ConnectionRefusedError" in packet_text
    assert "Connect call failed ('127.0.0.1', 7497)" in packet_text
    assert "openclaw-gateway` present on `127.0.0.1:18789`" in packet_text
    assert "`127.0.0.1:18791`" in packet_text
    assert "loopback of\nthe current process context" in packet_text
    assert "endpoint/context\nmismatch" in packet_text

    for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"):
        assert (
            f"| `{symbol}` | `unavailable` | `false` | `false` | "
            "`null` | `null` | "
            "`historical read-only request failed: ConnectionRefusedError` |"
        ) in packet_text

    assert "Because all five results are unavailable and non-countable" in packet_text
    assert "historical-market-data-only boundary" in packet_text
    assert "account, position, margin, buying-power, portfolio, order, balance" in packet_text
    assert "execution queries" in packet_text
    assert "flattening, selling, or live trading" in packet_text
    assert "package capture; replay; scoring;\ncandidate generation" in packet_text
    assert "timer, service, systemd, or runtime mutation" in packet_text
    assert "strategy, risk, or execution changes" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "vps_runtime=NOT_TOUCHED" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "broker_api_authority=false" in packet_text
    assert "account_query_authority=false" in packet_text
    assert "order_authority=false" in packet_text
    assert "execution_authority=false" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "d11_completion_authority=false" in packet_text
    assert "operator-managed VPS endpoint/context readiness\nconfirmation" in packet_text
    assert "not authorization for the bot to start or\nmutate gateway" in packet_text

    assert (
        "### D11.42 VPS Read-Only Freshness Proof Connection-Refused Adjudication"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`authorized_pacific=2026-06-25 07:00:00 PDT`" in map_text
    assert "`authorized_utc=2026-06-25 14:00:00 UTC`" in map_text
    assert "`04e856c8a8d3387ccf2b0af5e55b493ea853a401`" in map_text
    assert "`requirements-diagnostics.txt / ib_insync==0.9.86`" in map_text
    assert "`PROOF_RUN_BUT_NON_COUNTABLE`" in map_text
    assert "`vps_freshness_proof_run=true`" in map_text
    assert "`d11_countable_evidence_produced=false`" in map_text
    assert "`AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in map_text
    assert "`freshness_classification=unavailable`" in map_text
    assert "`d11_countable=false`" in map_text
    assert "`d11_primary_eligible=false`" in map_text
    assert "`latest_candle_timestamp=null`" in map_text
    assert "`lag_minutes=null`" in map_text
    assert "ConnectionRefusedError" in map_text
    assert "`127.0.0.1:7497`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in map_text
    assert "`NOT_PROVEN_TWS_ISSUE`" in map_text
    assert "`NOT_PROVEN_IB_GATEWAY_ISSUE`" in map_text
    assert "loopback of the current process context" in map_text
    assert "not provider approval evidence and does not complete D11" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "operator-managed VPS\nendpoint/context readiness confirmation" in map_text
    assert "not bot-started gateway/runtime" in map_text


def test_d11_43_endpoint_context_correction_gate_blocks_blind_endpoint_change() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_endpoint_context_correction_gate.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.43 VPS Endpoint/Context Correction Gate" in packet_text
    assert "`gate_status` | `ENDPOINT_CONTEXT_CORRECTION_REQUIRED`" in packet_text
    assert (
        "`current_validated_source_commit` | "
        "`de2fcb8efbc9843333f004db45c75c603c744312`" in packet_text
    )
    assert "`d11_42_vps_validation` | `62 passed in 1.47s`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`endpoint_replacement_selected` | `false`" in packet_text
    assert "`root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert (
        "`authorized_endpoint_status` | "
        "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert (
        "`observed_gateway_context` | "
        "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in packet_text
    )
    assert "`desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE`" in packet_text
    assert (
        "`broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE`"
        in packet_text
    )
    assert "`prior_authorized_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`prior_authorized_endpoint_context` | `VPS process context`" in packet_text
    assert "`prior_authorized_endpoint_listener_observed` | `false`" in packet_text
    assert "`observed_openclaw_gateway_process` | `Node process`" in packet_text
    assert (
        "`observed_openclaw_gateway_ports` | "
        "`127.0.0.1:18789; 127.0.0.1:18791`" in packet_text
    )
    assert "`openclaw_gateway_systemd_service_found` | `false`" in packet_text
    assert (
        "`loopback_doctrine` | "
        "`127.0.0.1 means loopback of the current process context`"
        in packet_text
    )
    assert (
        "`vps_or_codex_local_socket_valid_for_mac_local_tws` | `false`"
        in packet_text
    )
    assert "D11.42 is locked as committed, pushed, and VPS-validated" in packet_text
    assert "zero countable market-data evidence" in packet_text
    assert "D11.43 must not choose a new endpoint blindly" in packet_text
    assert "does not authorize changing\nthe proof command" in packet_text
    assert "127.0.0.1:18789" in packet_text
    assert "127.0.0.1:18791" in packet_text
    assert "separate\n   source-controlled approval" in packet_text
    assert "why that port is the approved read-only bridge" in packet_text
    assert "Create a separately source-controlled tunnel prerequisite" in packet_text
    assert "Abandon the VPS-local proof path and return to Mac-local IBKR evidence only" in packet_text
    assert "the VPS proof must\nnot be rerun" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "account, position,\nmargin, buying-power, portfolio, order, balance" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime mutation" in packet_text
    assert "gateway start/stop/restart/reload" in packet_text
    assert "strategy, risk, or execution changes" in packet_text

    assert "### D11.43 VPS Endpoint/Context Correction Gate" in map_text
    assert str(packet_path) in map_text
    assert "`de2fcb8efbc9843333f004db45c75c603c744312`" in map_text
    assert "`62 passed in 1.47s`" in map_text
    assert "`PROOF_RUN_BUT_NON_COUNTABLE`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in map_text
    assert "`NOT_PROVEN_TWS_ISSUE`" in map_text
    assert "`NOT_PROVEN_IB_GATEWAY_ISSUE`" in map_text
    assert "`127.0.0.1:7497` refused connection" in map_text
    assert "no listener was\nobserved on `127.0.0.1:7497`" in map_text
    assert "`openclaw-gateway` was present as a Node process" in map_text
    assert "`127.0.0.1:18789` and `127.0.0.1:18791`" in map_text
    assert "`openclaw-gateway.service` was not found in systemd" in map_text
    assert "`127.0.0.1` is process-context-local loopback" in map_text
    assert "not valid for Mac-local TWS evidence" in map_text
    assert "does not choose a new endpoint blindly" in map_text
    assert "forbids proof rerun until\nendpoint/context correction is source-controlled" in map_text
    assert "forbids\nchanging to `18789` or `18791`" in map_text
    assert "approved `openclaw-gateway` exposed local port" in map_text
    assert "separately\nsource-controlled tunnel prerequisite" in map_text
    assert "returning to Mac-local IBKR evidence only" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin, buying-power, portfolio, order" in map_text
    assert "gateway mutation" in map_text


def test_d11_44_operator_endpoint_context_evidence_packet_is_identity_only() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_endpoint_context_operator_evidence_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.44 VPS Endpoint/Context Operator Evidence Packet" in packet_text
    assert (
        "`evidence_packet_status` | "
        "`OPERATOR_ENDPOINT_CONTEXT_EVIDENCE_DEFINED`" in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`3905f9ab4cf993103ff9aaa3c4619851ba00ae2d`" in packet_text
    )
    assert "`d11_43_vps_validation` | `63 passed in 1.10s`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`endpoint_replacement_selected` | `false`" in packet_text
    assert "`proof_command_allowed` | `false`" in packet_text
    assert "`ibkr_tws_gateway_connection_allowed` | `false`" in packet_text
    assert "`account_order_execution_access_allowed` | `false`" in packet_text
    assert "`gateway_mutation_allowed` | `false`" in packet_text
    assert "`root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert (
        "`authorized_endpoint_status` | "
        "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert (
        "`observed_gateway_context` | "
        "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in packet_text
    )
    assert "`desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE`" in packet_text
    assert (
        "`broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE`"
        in packet_text
    )
    assert "`prior_failed_vps_endpoint` | `127.0.0.1:7497`" in packet_text
    assert (
        "`observed_openclaw_gateway_ports` | "
        "`127.0.0.1:18789; 127.0.0.1:18791`" in packet_text
    )
    assert (
        "`openclaw_gateway_ports_approved_as_proof_endpoints` | `false`"
        in packet_text
    )
    assert (
        "`endpoint_liveness_is_provider_approval_evidence` | `false`"
        in packet_text
    )
    assert (
        "`open_tcp_port_is_approved_read_only_ibkr_market_data_bridge` | `false`"
        in packet_text
    )
    assert "`execution_context_for_future_evidence` | `VPS`" in packet_text
    assert (
        "`future_evidence_is_read_only_process_port_identity_only` | `true`"
        in packet_text
    )
    assert "not approved proof endpoints" in packet_text
    assert "Future Read-Only Operator Evidence Commands" in packet_text
    assert "must not run the proof command" in packet_text
    assert "connect to IBKR/TWS/Gateway" in packet_text
    assert "query account,\norder, or execution state" in packet_text
    assert "mutate `openclaw-gateway`" in packet_text
    assert "git status --short" in packet_text
    assert "git rev-parse HEAD" in packet_text
    assert "git log -1 --oneline" in packet_text
    assert "ss -ltnp | grep -E '(:18789|:18791|:7497)'" in packet_text
    assert "ps -fp <openclaw_gateway_pid>" in packet_text
    assert "readlink -f /proc/<openclaw_gateway_pid>/exe" in packet_text
    assert "pwdx <openclaw_gateway_pid>" in packet_text
    assert "tr '\\0' ' ' < /proc/<openclaw_gateway_pid>/cmdline" in packet_text
    assert 'rg -n "openclaw-gateway|18789|18791|7497" .' in packet_text
    assert 'printf \'%s\\n\' "--- pid=$pid ---"' in packet_text
    assert "raw TCP checks" in packet_text
    assert "endpoint\nliveness only" in packet_text
    assert "Endpoint liveness is not protocol approval" in packet_text
    assert "provider approval" in packet_text
    assert "market-data proof evidence" in packet_text
    assert "An open TCP port must not be treated as proof" in packet_text
    assert "approved read-only IBKR market-data bridge" in packet_text
    assert "D11.44 must not choose a new endpoint" in packet_text
    assert "must not authorize changing a future\nproof command" in packet_text
    assert "127.0.0.1:18789" in packet_text
    assert "127.0.0.1:18791" in packet_text
    assert "later\nsource-controlled approval identifies the protocol and bridge semantics" in packet_text
    assert "Approved `openclaw-gateway` bridge path" in packet_text
    assert "Separately source-controlled tunnel prerequisite path" in packet_text
    assert "Abandon VPS-local proof and return to Mac-local IBKR evidence only" in packet_text
    assert "no endpoint\nreplacement is selected and no proof rerun is authorized" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "account, position,\nmargin, buying-power, portfolio, order, balance" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime mutation" in packet_text
    assert "gateway start/stop/restart/reload" in packet_text
    assert "enable/disable, kill, or mutation" in packet_text
    assert "strategy, risk, or execution changes" in packet_text

    assert "### D11.44 VPS Endpoint/Context Operator Evidence Packet" in map_text
    assert str(packet_path) in map_text
    assert "`3905f9ab4cf993103ff9aaa3c4619851ba00ae2d`" in map_text
    assert "`63 passed in 1.10s`" in map_text
    assert "`PROOF_RUN_BUT_NON_COUNTABLE`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in map_text
    assert "`NOT_PROVEN_TWS_ISSUE`" in map_text
    assert "`NOT_PROVEN_IB_GATEWAY_ISSUE`" in map_text
    assert "no endpoint replacement selected and no proof rerun authorized" in map_text
    assert "`127.0.0.1:7497` as the prior failed VPS-local endpoint" in map_text
    assert "`127.0.0.1:18789` and `127.0.0.1:18791` as observed" in map_text
    assert "not approved proof endpoints" in map_text
    assert "Endpoint liveness\nis not provider approval evidence" in map_text
    assert "open TCP port is not proof" in map_text
    assert "future read-only operator evidence for VPS process/port identity\nonly" in map_text
    assert "`git status --short`" in map_text
    assert "`git rev-parse HEAD`" in map_text
    assert "`git log -1 --oneline`" in map_text
    assert "`ss -ltnp` filtered for `18789`, `18791`, and `7497`" in map_text
    assert "`ps` identity for the\n`openclaw-gateway` PID" in map_text
    assert "`readlink -f /proc/<pid>/exe`" in map_text
    assert "`pwdx <pid>`" in map_text
    assert "`/proc/<pid>/cmdline` with nulls converted to spaces" in map_text
    assert "repo references to\n`openclaw-gateway`, `18789`, `18791`, and `7497`" in map_text
    assert "does not choose a new endpoint" in map_text
    assert "forbids switching a proof command to\n`18789` or `18791`" in map_text
    assert "protocol/bridge semantics" in map_text
    assert "approved\nread-only bridge" in map_text
    assert "approved\n`openclaw-gateway` bridge path" in map_text
    assert "source-controlled tunnel\nprerequisite path" in map_text
    assert "returning to Mac-local\nIBKR evidence only" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin, buying-power, portfolio, order" in map_text
    assert "gateway mutation" in map_text


def test_d11_45_endpoint_context_evidence_adjudicates_liveness_only() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_endpoint_context_evidence_adjudication.md"
    )
    d11_44_packet_path = Path(
        "docs/ibkr_market_data_vps_endpoint_context_operator_evidence_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    d11_44_packet_text = d11_44_packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.45 VPS Endpoint/Context Evidence Adjudication" in packet_text
    assert (
        "`adjudication_status` | `OPERATOR_ENDPOINT_CONTEXT_EVIDENCE_ADJUDICATED`"
        in packet_text
    )
    assert "`execution_context` | `VPS`" in packet_text
    assert (
        "`source_commit_during_evidence_collection` | "
        "`7ca0f2904f4d3b7376df0d699d2bc6d6bd128a4b`" in packet_text
    )
    assert (
        "`source_commit_message` | "
        "`7ca0f29 Define D11 VPS endpoint context operator evidence`"
        in packet_text
    )
    assert "`current_utc` | `2026-06-25 15:29:39 UTC`" in packet_text
    assert "`d11_44_vps_validation` | `64 passed in 1.27s`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`endpoint_replacement_selected` | `false`" in packet_text
    assert "`provider_approval_evidence` | `false`" in packet_text
    assert "`market_data_proof_evidence` | `false`" in packet_text
    assert "`endpoint_liveness_confirmed_for_18789` | `true`" in packet_text
    assert "`endpoint_liveness_confirmed_for_18791` | `true`" in packet_text
    assert "`endpoint_liveness_confirmed_for_7497` | `false`" in packet_text
    assert "`openclaw_gateway_identity_confirmed` | `true`" in packet_text
    assert "`openclaw_gateway_protocol_approved` | `false`" in packet_text
    assert "`proof_endpoint_approved` | `false`" in packet_text
    assert "`root_operational_blocker` | `VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert (
        "`authorized_endpoint_status` | "
        "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert (
        "`observed_gateway_context` | "
        "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in packet_text
    )
    assert "`desktop_terminal_issue_status` | `NOT_PROVEN_TWS_ISSUE`" in packet_text
    assert (
        "`broker_gateway_issue_status` | `NOT_PROVEN_IB_GATEWAY_ISSUE`"
        in packet_text
    )
    assert (
        "| `127.0.0.1:18791` | `LISTEN` | `openclaw-gateway` | `846` | "
        "`29` | `OPEN_LIVENESS_ONLY` |"
    ) in packet_text
    assert (
        "| `127.0.0.1:18789` | `LISTEN` | `openclaw-gateway` | `846` | "
        "`22` | `OPEN_LIVENESS_ONLY` |"
    ) in packet_text
    assert (
        "| `[::1]:18789` | `LISTEN` | `openclaw-gateway` | `846` | "
        "`23` | `OPEN_LIVENESS_ONLY` |"
    ) in packet_text
    assert (
        "| `127.0.0.1:7497` | `CLOSED_OR_REFUSED` | `none observed` | "
        "`none` | `none` | `NOT_LISTENING_ON_VPS` |"
    ) in packet_text
    assert "`openclaw_gateway_pids` | `846`" in packet_text
    assert "`pid` | `846`" in packet_text
    assert "`command` | `openclaw-gateway`" in packet_text
    assert "`executable` | `/usr/bin/node`" in packet_text
    assert "`pwd` | `/root`" in packet_text
    assert "`cmdline` | `openclaw-gateway`" in packet_text
    assert "tcp_127_0_0_1_18789=OPEN_LIVENESS_ONLY" in packet_text
    assert "tcp_127_0_0_1_18791=OPEN_LIVENESS_ONLY" in packet_text
    assert "tcp_127_0_0_1_7497=CLOSED_OR_REFUSED" in packet_text
    assert "not approved proof endpoints" in packet_text
    assert "not approve their protocol semantics" in packet_text
    assert "not approve them as an IBKR read-only market-data bridge" in packet_text
    assert "authorize switching a future proof command" in packet_text
    assert "OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791" in packet_text
    assert "missing its final\n  `9`" in packet_text
    assert "missing its final `y`" in packet_text
    assert 'rg -n "openclaw-gateway|18789|18791|7497" .' in packet_text
    assert "printf '--- pid=%s ---\\n' \"$pid\"" in packet_text
    assert "-bash: printf: --: invalid option" in packet_text
    assert "printf: usage: printf [-v var] format [arguments]" in packet_text
    assert 'printf \'%s\\n\' "--- pid=$pid ---"' in packet_text
    assert "forbids treating open TCP liveness as approved protocol semantics" in packet_text
    assert "provider approval evidence" in packet_text
    assert "market-data proof evidence" in packet_text
    assert "forbids switching the proof command to\n`18789` or `18791`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "account, position, margin, buying-power, portfolio" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime mutation" in packet_text
    assert "gateway start/stop/restart/reload" in packet_text
    assert "enable/disable, kill, or mutation" in packet_text
    assert "strategy, risk, or execution changes" in packet_text

    assert 'rg -n "openclaw-gateway|18789|18791|7497" .' in d11_44_packet_text
    assert 'printf \'%s\\n\' "--- pid=$pid ---"' in d11_44_packet_text
    incorrect_repo_search = 'rg -n "openclaw-' + 'gatewa|18789|18791|7497" .'
    assert incorrect_repo_search not in d11_44_packet_text

    assert "### D11.45 VPS Endpoint/Context Evidence Adjudication" in map_text
    assert str(packet_path) in map_text
    assert "`OPERATOR_ENDPOINT_CONTEXT_EVIDENCE_ADJUDICATED`" in map_text
    assert "`7ca0f2904f4d3b7376df0d699d2bc6d6bd128a4b`" in map_text
    assert "`64 passed in 1.27s`" in map_text
    assert "`OPEN_LIVENESS_ONLY`" in map_text
    assert "`CLOSED_OR_REFUSED`" in map_text
    assert "`/usr/bin/node`" in map_text
    assert "`/root`" in map_text
    assert "`openclaw-gateway`" in map_text
    assert "`endpoint_liveness_confirmed_for_18789=true`" in map_text
    assert "`endpoint_liveness_confirmed_for_18791=true`" in map_text
    assert "`endpoint_liveness_confirmed_for_7497=false`" in map_text
    assert "`openclaw_gateway_identity_confirmed=true`" in map_text
    assert "`openclaw_gateway_protocol_approved=false`" in map_text
    assert "`proof_endpoint_approved=false`" in map_text
    assert "`provider_approval_evidence=false`" in map_text
    assert "`market_data_proof_evidence=false`" in map_text
    assert "`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`" in map_text
    assert 'rg -n "openclaw-gateway|18789|18791|7497" .' in map_text
    assert "omitted the final `9` in `18789`" in map_text
    assert "omitted the final `y` in `openclaw-gateway`" in map_text
    assert "avoid `printf '--- pid=%s ---\\n' \"$pid\"`" in map_text
    assert "`printf '%s\\n' \"--- pid=$pid ---\"`" in map_text
    assert "forbids treating open TCP liveness" in map_text
    assert "forbids switching the proof command to `18789` or `18791`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin, buying-power, portfolio, order" in map_text
    assert "gateway mutation" in map_text


def test_d11_46_bridge_protocol_decision_prerequisite_preserves_boundaries() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_bridge_protocol_decision_prerequisite.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.46 VPS Bridge/Protocol Decision Prerequisite" in packet_text
    assert (
        "`gate_status` | `BRIDGE_PROTOCOL_DECISION_PREREQUISITE_REQUIRED`"
        in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`73b3b22297ba82d61eb915351349eb758589724a`" in packet_text
    )
    assert "`d11_45_vps_validation` | `65 passed in 0.23s`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`proof_endpoint_approved` | `false`" in packet_text
    assert "`openclaw_gateway_protocol_approved` | `false`" in packet_text
    assert "`provider_approval_evidence` | `false`" in packet_text
    assert "`market_data_proof_evidence` | `false`" in packet_text
    assert "`endpoint_liveness_confirmed_for_18789` | `true`" in packet_text
    assert "`endpoint_liveness_confirmed_for_18791` | `true`" in packet_text
    assert "`endpoint_liveness_confirmed_for_7497` | `false`" in packet_text
    assert "`openclaw_gateway_identity_confirmed` | `true`" in packet_text
    assert "`openclaw_gateway_pid` | `846`" in packet_text
    assert "`openclaw_gateway_executable` | `/usr/bin/node`" in packet_text
    assert "`openclaw_gateway_pwd` | `/root`" in packet_text
    assert "`openclaw_gateway_cmdline` | `openclaw-gateway`" in packet_text
    assert "`port_18789_classification` | `OPEN_LIVENESS_ONLY`" in packet_text
    assert "`port_18791_classification` | `OPEN_LIVENESS_ONLY`" in packet_text
    assert "`port_7497_classification` | `CLOSED_OR_REFUSED`" in packet_text
    assert (
        "`source_commit_during_d11_44_evidence` | "
        "`7ca0f2904f4d3b7376df0d699d2bc6d6bd128a4b`" in packet_text
    )
    assert "`d11_44_evidence_timestamp_utc` | `2026-06-25 15:29:39 UTC`" in packet_text
    assert "open TCP liveness on `18789` and\n`18791` is not protocol approval" in packet_text
    assert "`127.0.0.1:7497` remains closed/refused" in packet_text
    assert "Node process at\n`/usr/bin/node`" in packet_text
    assert "working directory `/root`" in packet_text
    assert "cmdline `openclaw-gateway`" in packet_text
    assert "Future Evidence Required Before Any Bridge Approval" in packet_text
    assert "package/source provenance" in packet_text
    assert "protocol exposed on `127.0.0.1:18789` and `127.0.0.1:18791`" in packet_text
    assert "IBKR API, HTTP, WebSocket, RPC, proxy, tunnel" in packet_text
    assert "historical market-data read-only requests" in packet_text
    assert "without account, position, margin, buying-power, portfolio, order, balance" in packet_text
    assert "The exact command boundary for any future protocol probe" in packet_text
    assert "Separate source-controlled approval before executing any protocol probe" in packet_text
    assert "non-mutating, fail-closed protocol-probe design" in packet_text
    assert "if protocol semantics cannot be proven\n   source-controlled" in packet_text
    assert "must be separately source-controlled before execution" in packet_text
    assert "must not query account, position, margin, buying-power, portfolio" in packet_text
    assert "must not mutate gateway, runtime, timer, service, systemd" in packet_text
    assert "does not approve `18789` or `18791` as proof endpoints" in packet_text
    assert "does not\nauthorize a proof rerun" in packet_text
    assert "forbids treating liveness as bridge/protocol\napproval" in packet_text
    assert "forbids switching the proof command to `18789` or `18791`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "account, position, margin, buying-power, portfolio" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime\nmutation" in packet_text
    assert "gateway start/stop/restart/reload" in packet_text
    assert "enable/disable, kill, or mutation" in packet_text
    assert "strategy, risk, or execution changes" in packet_text

    assert "### D11.46 VPS Bridge/Protocol Decision Prerequisite" in map_text
    assert str(packet_path) in map_text
    assert "`73b3b22297ba82d61eb915351349eb758589724a`" in map_text
    assert "`65 passed in 0.23s`" in map_text
    assert "liveness-confirmed only" in map_text
    assert "`openclaw_gateway_protocol_approved=false`" in map_text
    assert "`proof_endpoint_approved=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`provider_approval_evidence=false`" in map_text
    assert "`market_data_proof_evidence=false`" in map_text
    assert "PID `846`" in map_text
    assert "executable `/usr/bin/node`" in map_text
    assert "working directory `/root`" in map_text
    assert "cmdline\n`openclaw-gateway`" in map_text
    assert "`OPEN_LIVENESS_ONLY`" in map_text
    assert "`CLOSED_OR_REFUSED`" in map_text
    assert "does not approve `18789` or `18791` as proof endpoints" in map_text
    assert "does not\nauthorize a proof rerun" in map_text
    assert "package/source provenance" in map_text
    assert "IBKR API, HTTP, WebSocket,\nRPC, proxy, tunnel" in map_text
    assert "historical market-data\nread-only requests" in map_text
    assert "without account/order/execution authority" in map_text
    assert "exact\ncommand boundaries" in map_text
    assert "separate approval before execution" in map_text
    assert "non-mutating fail-closed probe design" in map_text
    assert "if protocol semantics cannot be proven\nsource-controlled" in map_text
    assert "forbids treating liveness as bridge/protocol approval" in map_text
    assert "forbids switching the proof command to `18789` or `18791`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin, buying-power, portfolio, order" in map_text
    assert "gateway mutation" in map_text


def test_d11_47_bridge_protocol_static_evidence_packet_forbids_traffic() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_bridge_protocol_static_evidence_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.47 VPS Bridge/Protocol Static Evidence Packet" in packet_text
    assert (
        "`evidence_packet_status` | `BRIDGE_PROTOCOL_STATIC_EVIDENCE_DEFINED`"
        in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`2d68d0d3d5ca72be0fd39c751148bd4d1c392c9b`" in packet_text
    )
    assert "`d11_46_vps_validation` | `66 passed in 1.89s`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`proof_endpoint_approved` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`openclaw_gateway_protocol_approved` | `false`" in packet_text
    assert "`provider_approval_evidence` | `false`" in packet_text
    assert "`market_data_proof_evidence` | `false`" in packet_text
    assert "`endpoint_liveness_confirmed_for_18789` | `true`" in packet_text
    assert "`endpoint_liveness_confirmed_for_18791` | `true`" in packet_text
    assert "`endpoint_liveness_confirmed_for_7497` | `false`" in packet_text
    assert "`port_18789_classification` | `OPEN_LIVENESS_ONLY`" in packet_text
    assert "`port_18791_classification` | `OPEN_LIVENESS_ONLY`" in packet_text
    assert "`port_7497_classification` | `CLOSED_OR_REFUSED`" in packet_text
    assert "liveness on `18789` and `18791` is identity/liveness\nonly" in packet_text
    assert "package/source identity is not protocol\napproval" in packet_text
    assert "service identity is not protocol approval" in packet_text
    assert "liveness is not\nprotocol approval" in packet_text
    assert "Future Read-Only Static Evidence Commands" in packet_text
    assert "git status --short" in packet_text
    assert "git rev-parse HEAD" in packet_text
    assert "git log -1 --oneline" in packet_text
    assert "which openclaw-gateway" in packet_text
    assert "command -v openclaw-gateway" in packet_text
    assert 'readlink -f "$(command -v openclaw-gateway)"' in packet_text
    assert 'file "$(command -v openclaw-gateway)"' in packet_text
    assert 'ls -l "$(command -v openclaw-gateway)"' in packet_text
    assert 'dpkg -S "$(command -v openclaw-gateway)"' in packet_text
    assert "npm root -g" in packet_text
    assert "npm list -g --depth=0" in packet_text
    assert "node --version" in packet_text
    assert "npm --version" in packet_text
    assert "systemctl status openclaw-gateway --no-pager" in packet_text
    assert "service-identity evidence only and not service mutation" in packet_text
    assert (
        'rg -n "openclaw-gateway|18789|18791|7497|WebSocket|websocket|http|'
        'HTTP|rpc|RPC|proxy|tunnel|IBKR|market data|market-data" .'
        in packet_text
    )
    assert "repo-only static search" in packet_text
    assert "Explicitly Forbidden Evidence Collection" in packet_text
    assert "does not authorize protocol probing or traffic" in packet_text
    assert "curl" in packet_text
    assert "nc" in packet_text
    assert "telnet" in packet_text
    assert "/dev/tcp" in packet_text
    assert "protocol handshake" in packet_text
    assert "broker API import or connect" in packet_text
    assert "forbids treating package/source identity as protocol approval" in packet_text
    assert "service\nidentity as protocol approval" in packet_text
    assert "liveness as protocol approval" in packet_text
    assert "forbids\nswitching the proof command to `18789` or `18791`" in packet_text
    assert "Package/source provenance evidence is required before any protocol decision" in packet_text
    assert "Protocol semantics evidence is required before any bridge approval" in packet_text
    assert "Separate\nsource-controlled protocol-probe approval" in packet_text
    assert "before any traffic is\nsent to `18789` or `18791`" in packet_text
    assert "separately source-controlled, non-mutating,\nfail-closed" in packet_text
    assert "no account, position, margin, buying-power,\nportfolio, order, balance" in packet_text
    assert "no gateway/runtime/service/systemd mutation" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "account, position, margin, buying-power, portfolio" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime\nmutation" in packet_text
    assert "gateway start/stop/restart/reload" in packet_text
    assert "enable/disable, kill, or mutation" in packet_text
    assert "strategy, risk, or execution changes" in packet_text

    assert "### D11.47 VPS Bridge/Protocol Static Evidence Packet" in map_text
    assert str(packet_path) in map_text
    assert "`2d68d0d3d5ca72be0fd39c751148bd4d1c392c9b`" in map_text
    assert "`66 passed in 1.89s`" in map_text
    assert "`openclaw_gateway_protocol_approved=false`" in map_text
    assert "`proof_endpoint_approved=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`provider_approval_evidence=false`" in map_text
    assert "`market_data_proof_evidence=false`" in map_text
    assert "does not approve `18789` or `18791` as proof endpoints" in map_text
    assert "does not\nauthorize proof rerun" in map_text
    assert "does not authorize protocol probing" in map_text
    assert "read-only static evidence" in map_text
    assert "`which openclaw-gateway`" in map_text
    assert "`command -v`" in map_text
    assert "`readlink`" in map_text
    assert "`file`" in map_text
    assert "`ls -l`" in map_text
    assert "optional `dpkg -S`" in map_text
    assert "optional `npm root -g`" in map_text
    assert "optional `npm list -g --depth=0`" in map_text
    assert "optional `node --version`" in map_text
    assert "optional\n`npm --version`" in map_text
    assert "service-identity only" in map_text
    assert "repo-only `rg` search" in map_text
    assert "forbids `curl`, `nc`, `telnet`, `/dev/tcp`, protocol\nhandshake" in map_text
    assert "broker API import or connect" in map_text
    assert "any traffic to `18789`, `18791`,\nor `7497`" in map_text
    assert "forbids treating package/source identity, service identity, or\nliveness as protocol approval" in map_text
    assert "forbids switching the proof command to\n`18789` or `18791`" in map_text
    assert "package/source provenance evidence before any protocol decision" in map_text
    assert "protocol semantics evidence before any bridge approval" in map_text
    assert "protocol-probe approval before any traffic is sent to `18789`\nor `18791`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin" in map_text
    assert "gateway mutation" in map_text


def test_d11_48_static_provenance_adjudication_preserves_no_approval() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_bridge_protocol_static_evidence_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.48 VPS Bridge/Protocol Static Evidence Adjudication" in packet_text
    assert (
        "`adjudication_status` | `STATIC_PROVENANCE_EVIDENCE_ADJUDICATED`"
        in packet_text
    )
    assert (
        "`static_evidence_file_path` | "
        "`/tmp/d11_47_static_evidence_20260625T202035Z.txt`" in packet_text
    )
    assert "`static_evidence_file_existed` | `true`" in packet_text
    assert "`static_evidence_line_count` | `30022`" in packet_text
    assert "`static_evidence_byte_count` | `3132489`" in packet_text
    assert (
        "`static_evidence_sha256` | "
        "`26c21cdf1a3af3e4e15e8e7e8e9c9c3f3ce24c806c97110ede6a1a9050b2676c`"
        in packet_text
    )
    assert (
        "`source_commit_after_evidence_collection` | "
        "`3592b3068fd6bce0296d28db6ddd579ae90e8574`" in packet_text
    )
    assert (
        "`source_commit_message` | "
        "`3592b30 Define D11 VPS bridge protocol static evidence`" in packet_text
    )
    assert "`d11_47_vps_validation` | `67 passed in 1.67s`" in packet_text
    assert "`openclaw_gateway_command_v` | `empty`" in packet_text
    assert "`openclaw_gateway_binary` | `NOT_FOUND`" in packet_text
    assert "`openclaw_gateway_binary_on_path` | `false`" in packet_text
    assert "`npm_global_openclaw_package_observed` | `true`" in packet_text
    assert "`npm_global_openclaw_package` | `openclaw@2026.3.24`" in packet_text
    assert "`node_version` | `v24.13.0`" in packet_text
    assert "`npm_version` | `11.6.2`" in packet_text
    assert "`openclaw_gateway_service_found` | `false`" in packet_text
    assert "`repo_reference_search_too_broad` | `true`" in packet_text
    assert "`package_source_provenance_complete` | `false`" in packet_text
    assert "`protocol_semantics_proven` | `false`" in packet_text
    assert "`bridge_protocol_approved` | `false`" in packet_text
    assert "`proof_endpoint_approved` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`provider_approval_evidence` | `false`" in packet_text
    assert "`market_data_proof_evidence` | `false`" in packet_text
    assert "without rerunning the VPS proof" in packet_text
    assert "without protocol probing" in packet_text
    assert "without\ntraffic to `18789`, `18791`, or `7497`" in packet_text
    assert "without endpoint switch" in packet_text
    assert "without\ngateway/runtime/service/systemd mutation" in packet_text
    assert "openclaw_gateway_command_v` was empty" in packet_text
    assert "`openclaw_gateway_binary=NOT_FOUND`" in packet_text
    assert "`openclaw@2026.3.24`" in packet_text
    assert "`node_version=v24.13.0`" in packet_text
    assert "`npm_version=11.6.2`" in packet_text
    assert "`openclaw-gateway.service` could not be found" in packet_text
    assert "too broad/noisy for protocol approval" in packet_text
    assert "does not complete package/source provenance" in packet_text
    assert "does not prove\nprotocol semantics" in packet_text
    assert "does not approve `18789` or `18791` as proof endpoints" in packet_text
    assert "does not\nauthorize proof rerun" in packet_text
    assert "protocol probing" in packet_text
    assert "endpoint switch" in packet_text
    assert "account/order/execution access" in packet_text
    assert "forbids treating static package/source\nidentity" in packet_text
    assert "npm package observation" in packet_text
    assert "service absence" in packet_text
    assert "noisy repo references" in packet_text
    assert "open TCP liveness as approved protocol/bridge semantics" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "account, position, margin, buying-power, portfolio" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime\nmutation" in packet_text
    assert "gateway start/stop/restart/reload" in packet_text
    assert "enable/disable, kill, or mutation" in packet_text
    assert "strategy, risk, or execution changes" in packet_text

    assert "### D11.48 VPS Bridge/Protocol Static Evidence Adjudication" in map_text
    assert str(packet_path) in map_text
    assert "`STATIC_PROVENANCE_EVIDENCE_ADJUDICATED`" in map_text
    assert "`67 passed in 1.67s`" in map_text
    assert "`/tmp/d11_47_static_evidence_20260625T202035Z.txt`" in map_text
    assert "line count `30022`" in map_text
    assert "byte\ncount `3132489`" in map_text
    assert "`26c21cdf1a3af3e4e15e8e7e8e9c9c3f3ce24c806c97110ede6a1a9050b2676c`" in map_text
    assert "`3592b3068fd6bce0296d28db6ddd579ae90e8574`" in map_text
    assert "`3592b30 Define D11 VPS bridge protocol static evidence`" in map_text
    assert "`openclaw_gateway_command_v` was empty" in map_text
    assert "`openclaw_gateway_binary=NOT_FOUND`" in map_text
    assert "`openclaw_gateway_binary_on_path=false`" in map_text
    assert "`npm_global_openclaw_package_observed=true`" in map_text
    assert "`openclaw@2026.3.24`" in map_text
    assert "`node_version=v24.13.0`" in map_text
    assert "`npm_version=11.6.2`" in map_text
    assert "`openclaw_gateway_service_found=false`" in map_text
    assert "repo reference output was too\nbroad/noisy for protocol approval" in map_text
    assert "`package_source_provenance_complete=false`" in map_text
    assert "`protocol_semantics_proven=false`" in map_text
    assert "`bridge_protocol_approved=false`" in map_text
    assert "`proof_endpoint_approved=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`provider_approval_evidence=false`" in map_text
    assert "`market_data_proof_evidence=false`" in map_text
    assert "does not approve `18789` or `18791`" in map_text
    assert "does not authorize proof rerun" in map_text
    assert "does not authorize protocol\nprobing" in map_text
    assert "does not authorize endpoint switch" in map_text
    assert "does not authorize\naccount/order/execution access" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin" in map_text
    assert "gateway mutation" in map_text


def test_d11_49_negative_path_decision_closes_current_vps_bridge_path() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_bridge_protocol_negative_path_decision.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.49 VPS Bridge/Protocol Negative-Path Decision" in packet_text
    assert (
        "`decision_status` | `VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION`"
        in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`3c49b5cdfcb1e135fcad10c4af7a8af9ce00ab32`" in packet_text
    )
    assert "`d11_48_vps_validation` | `68 passed in 1.85s`" in packet_text
    assert "`current_vps_bridge_path_approved` | `false`" in packet_text
    assert "`current_18789_endpoint_approved` | `false`" in packet_text
    assert "`current_18791_endpoint_approved` | `false`" in packet_text
    assert "`current_7497_endpoint_available` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`bridge_protocol_approved` | `false`" in packet_text
    assert "`provider_approval_evidence` | `false`" in packet_text
    assert "`market_data_proof_evidence` | `false`" in packet_text
    assert "`d11_completion_authority` | `false`" in packet_text
    assert "`openclaw_gateway_binary_on_path` | `false`" in packet_text
    assert "`npm_global_openclaw_package_observed` | `true`" in packet_text
    assert "`openclaw_gateway_service_found` | `false`" in packet_text
    assert "`package_source_provenance_complete` | `false`" in packet_text
    assert "`repo_reference_search_too_broad` | `true`" in packet_text
    assert "`protocol_semantics_proven` | `false`" in packet_text
    assert "current VPS bridge/protocol path is not approved" in packet_text
    assert "liveness-only/non-approved endpoints" in packet_text
    assert "`7497` remains unavailable from the VPS proof context" in packet_text
    assert "No current VPS endpoint\ncan be used for D11 countable market-data proof" in packet_text
    assert "negative-path decision only" in packet_text
    assert "not a new test plan" in packet_text
    assert "closes the immediate current path to proof rerun" in packet_text
    assert "exact binary/source provenance" in packet_text
    assert "exact protocol semantics" in packet_text
    assert "explicit non-mutating probe boundary" in packet_text
    assert "explicit\noperator-output compression" in packet_text
    assert "separate authorization before any traffic" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "account, position, margin, buying-power, portfolio" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime\nmutation" in packet_text
    assert "gateway mutation" in packet_text
    assert "proof_rerun_authorized=false" in packet_text
    assert "protocol_probe_authorized=false" in packet_text
    assert "endpoint_switch_authorized=false" in packet_text

    assert "### D11.49 VPS Bridge/Protocol Negative-Path Decision" in map_text
    assert str(packet_path) in map_text
    assert "`VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION`" in map_text
    assert "`3c49b5cdfcb1e135fcad10c4af7a8af9ce00ab32`" in map_text
    assert "`68 passed in 1.85s`" in map_text
    assert "`openclaw_gateway_binary_on_path=false`" in map_text
    assert "`npm_global_openclaw_package_observed=true`" in map_text
    assert "`openclaw_gateway_service_found=false`" in map_text
    assert "`package_source_provenance_complete=false`" in map_text
    assert "`repo_reference_search_too_broad=true`" in map_text
    assert "`protocol_semantics_proven=false`" in map_text
    assert "current VPS bridge/protocol path is not approved" in map_text
    assert "liveness-only/non-approved\nendpoints" in map_text
    assert "`7497` remains unavailable from the VPS proof context" in map_text
    assert "No\ncurrent VPS endpoint can be used for D11 countable market-data proof" in (
        map_text
    )
    assert "negative-path decision, not a new test plan" in map_text
    assert "immediate current path is closed to proof rerun" in map_text
    assert "`current_vps_bridge_path_approved=false`" in map_text
    assert "`current_18789_endpoint_approved=false`" in map_text
    assert "`current_18791_endpoint_approved=false`" in map_text
    assert "`current_7497_endpoint_available=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`protocol_probe_authorized=false`" in map_text
    assert "`endpoint_switch_authorized=false`" in map_text
    assert "`bridge_protocol_approved=false`" in map_text
    assert "`provider_approval_evidence=false`" in map_text
    assert "`market_data_proof_evidence=false`" in map_text
    assert "`d11_completion_authority=false`" in map_text
    assert "exact\nbinary/source provenance" in map_text
    assert "exact protocol semantics" in map_text
    assert "explicit non-mutating probe\nboundary" in map_text
    assert "explicit operator-output compression" in map_text
    assert "separate authorization\nbefore any traffic" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin" in map_text
    assert "proof rerun,\nendpoint switch, or protocol-probe authority" in map_text


def test_d11_50_post_vps_routing_decision_routes_to_mac_review_only() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_post_vps_negative_path_routing_decision.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.50 Post-VPS Negative-Path Routing Decision" in packet_text
    assert (
        "`routing_status` | `POST_VPS_NEGATIVE_PATH_ROUTING_DECISION`"
        in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`ce132ae4334f2e9c315fbfdd9133affc1f070be5`" in packet_text
    )
    assert "`d11_49_vps_validation` | `69 passed in 1.75s`" in packet_text
    assert "`vps_bridge_path_closed` | `true`" in packet_text
    assert (
        "`current_vps_endpoint_available_for_countable_proof` | `false`"
        in packet_text
    )
    assert "`next_route` | `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`" in packet_text
    assert "`mac_local_market_test_authorized` | `false`" in packet_text
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION`" in packet_text
    assert "`current_vps_bridge_path_approved=false`" in packet_text
    assert "`current_18789_endpoint_approved=false`" in packet_text
    assert "`current_18791_endpoint_approved=false`" in packet_text
    assert "`current_7497_endpoint_available=false`" in packet_text
    assert "`bridge_protocol_approved=false`" in packet_text
    assert "`provider_approval_evidence=false`" in packet_text
    assert "`market_data_proof_evidence=false`" in packet_text
    assert "`d11_completion_authority=false`" in packet_text
    assert "current VPS bridge/protocol path is closed" in packet_text
    assert "Ports `18789` and `18791` are\nnot approved endpoints" in packet_text
    assert "`7497` remains unavailable from the VPS proof\ncontext" in packet_text
    assert "No current VPS endpoint can be used for D11 countable market-data\nproof" in packet_text
    assert "`MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`" in packet_text
    assert "does not\nauthorize a Mac-local market test yet" in packet_text
    assert "does not authorize a VPS market test" in packet_text
    assert "does not authorize a proof rerun" in packet_text
    assert "does not authorize a protocol probe" in packet_text
    assert "does\nnot authorize an endpoint switch" in packet_text
    assert "evidence/routing documentation, not proof execution" in packet_text
    assert "separately source-controlled\npreflight gate" in packet_text
    assert "explicit date and session window" in packet_text
    assert "explicit TWS/manual operator readiness\nboundary" in packet_text
    assert "explicit historical-market-data-only command" in packet_text
    assert "explicit compact output\nhandling" in packet_text
    assert "expected commit" in packet_text
    assert "clean worktree requirement" in packet_text
    assert "no\naccount/order/execution authority" in packet_text
    assert "account, position, margin, buying-power, portfolio" in packet_text
    assert "cleanup_authority=false" in packet_text
    assert "flatten_authority=false" in packet_text
    assert "sell_authority=false" in packet_text
    assert "cancel_authority=false" in packet_text
    assert "live_trading_authority=false" in packet_text
    assert "package_capture=false" in packet_text
    assert "replay=false" in packet_text
    assert "scoring=false" in packet_text
    assert "candidate_generation=false" in packet_text
    assert "timer_service=NOT_TOUCHED" in packet_text
    assert "service, systemd, or runtime\nmutation" in packet_text
    assert "gateway mutation" in packet_text
    assert "proof_rerun_authorized=false" in packet_text
    assert "protocol_probe_authorized=false" in packet_text
    assert "endpoint_switch_authorized=false" in packet_text
    assert "mac_local_market_test_authorized=false" in packet_text
    assert "vps_market_test_authorized=false" in packet_text

    assert "### D11.50 Post-VPS Negative-Path Routing Decision" in map_text
    assert str(packet_path) in map_text
    assert "`POST_VPS_NEGATIVE_PATH_ROUTING_DECISION`" in map_text
    assert "`ce132ae4334f2e9c315fbfdd9133affc1f070be5`" in map_text
    assert "`69 passed in 1.75s`" in map_text
    assert "`VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION`" in map_text
    assert "`current_vps_bridge_path_approved=false`" in map_text
    assert "`current_18789_endpoint_approved=false`" in map_text
    assert "`current_18791_endpoint_approved=false`" in map_text
    assert "`current_7497_endpoint_available=false`" in map_text
    assert "`bridge_protocol_approved=false`" in map_text
    assert "`provider_approval_evidence=false`" in map_text
    assert "`market_data_proof_evidence=false`" in map_text
    assert "`d11_completion_authority=false`" in map_text
    assert "`vps_bridge_path_closed=true`" in map_text
    assert "`current_vps_endpoint_available_for_countable_proof=false`" in map_text
    assert "Ports `18789` and\n`18791` are not approved endpoints" in map_text
    assert "`7497` remains unavailable from the VPS\nproof context" in map_text
    assert "no current VPS endpoint can be used for D11 countable\nmarket-data proof" in map_text
    assert "`next_route=MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`" in map_text
    assert "`mac_local_market_test_authorized=false`" in map_text
    assert "`vps_market_test_authorized=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`protocol_probe_authorized=false`" in map_text
    assert "`endpoint_switch_authorized=false`" in map_text
    assert "evidence/routing documentation, not proof execution" in map_text
    assert "separately source-controlled\npreflight gate" in map_text
    assert "explicit date and session window" in map_text
    assert "explicit TWS/manual\noperator readiness boundary" in map_text
    assert "explicit historical-market-data-only command" in map_text
    assert "explicit compact output handling" in map_text
    assert "expected commit" in map_text
    assert "clean worktree requirement" in map_text
    assert "no account/order/execution authority" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no account, position, margin" in map_text
    assert "protocol probe, or market-test authority" in map_text


def test_d11_51_mac_local_evidence_review_prerequisite_opens_review_only() -> None:
    packet_path = Path("docs/ibkr_market_data_mac_local_evidence_review_prerequisite.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.51 Mac-Local IBKR Evidence-Review Prerequisite" in packet_text
    assert (
        "`prerequisite_status` | `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_PREREQUISITE`"
        in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`cf7e9bb0a62c1d6e94524b0f7597090fe80596c6`" in packet_text
    )
    assert "`d11_50_vps_validation` | `70 passed in 0.21s`" in packet_text
    assert "`vps_bridge_path_closed` | `true`" in packet_text
    assert (
        "`current_vps_endpoint_available_for_countable_proof` | `false`"
        in packet_text
    )
    assert "`next_route` | `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`" in packet_text
    assert "`mac_local_evidence_review_authorized` | `true`" in packet_text
    assert "`mac_local_market_test_authorized` | `false`" in packet_text
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`tws_gateway_connection_commands_authorized` | `false`" in packet_text
    assert "`broker_api_import_connect_authorized` | `false`" in packet_text
    assert "`account_order_execution_access_authorized` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`POST_VPS_NEGATIVE_PATH_ROUTING_DECISION`" in packet_text
    assert "`vps_bridge_path_closed=true`" in packet_text
    assert "`current_vps_endpoint_available_for_countable_proof=false`" in (
        packet_text
    )
    assert "`next_route=MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`" in packet_text
    assert "VPS bridge/protocol path remains closed" in packet_text
    assert "No current VPS endpoint can be used\nfor D11 countable market-data proof" in packet_text
    assert "only active next route is Mac-local\nIBKR evidence review" in packet_text
    assert "authorizes documentation/evidence review" in packet_text
    assert "does not authorize Mac-local market testing yet" in packet_text
    assert "does not authorize TWS/Gateway connection commands" in packet_text
    assert "does not authorize\nbroker API import/connect" in packet_text
    assert "does not authorize proof rerun" in packet_text
    assert "authorize account/order/execution access" in packet_text
    assert "Exact future date" in packet_text
    assert "Explicit regular-session window" in packet_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in packet_text
    assert "6:55 AM Pacific readiness-check boundary only" in packet_text
    assert "Explicit expected source commit" in packet_text
    assert "Clean worktree requirement before and after" in packet_text
    assert "Explicit TWS/manual operator readiness boundary" in packet_text
    assert "Historical-market-data-only command" in packet_text
    assert "Explicit compact output handling" in packet_text
    assert "No account, position, margin, buying-power, portfolio" in packet_text
    assert "No package capture, replay, scoring, candidate generation" in packet_text
    assert "market-test authority" in packet_text
    assert "VPS proof authority" in packet_text
    assert "protocol-probe\nauthority" in packet_text
    assert "endpoint-switch authority" in packet_text
    assert "account/order/execution authority" in packet_text
    assert "timer/service/systemd\nor runtime mutation" in packet_text
    assert "gateway mutation" in packet_text
    assert "strategy/risk/execution authority" in packet_text
    assert "D11\ncompletion authority" in packet_text
    assert "Unit 12 opening authority" in packet_text
    assert "vps_proof_authority=false" in packet_text
    assert "d11_completion_authority=false" in packet_text
    assert "unit_12_opening_authority=false" in packet_text

    assert "### D11.51 Mac-Local IBKR Evidence-Review Prerequisite" in map_text
    assert str(packet_path) in map_text
    assert "`MAC_LOCAL_IBKR_EVIDENCE_REVIEW_PREREQUISITE`" in map_text
    assert "`cf7e9bb0a62c1d6e94524b0f7597090fe80596c6`" in map_text
    assert "`70 passed in 0.21s`" in map_text
    assert "`POST_VPS_NEGATIVE_PATH_ROUTING_DECISION`" in map_text
    assert "`vps_bridge_path_closed=true`" in map_text
    assert "`current_vps_endpoint_available_for_countable_proof=false`" in map_text
    assert "`next_route=MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`" in map_text
    assert "`mac_local_evidence_review_authorized=true`" in map_text
    assert "`mac_local_market_test_authorized=false`" in map_text
    assert "`vps_market_test_authorized=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`protocol_probe_authorized=false`" in map_text
    assert "`endpoint_switch_authorized=false`" in map_text
    assert "VPS bridge/protocol path remains closed" in map_text
    assert "no current VPS\nendpoint can be used for D11 countable market-data proof" in map_text
    assert "only active\nnext route is Mac-local IBKR evidence review" in map_text
    assert "documentation/evidence review only" in map_text
    assert "does not authorize\nMac-local market testing yet" in map_text
    assert "TWS/Gateway connection commands" in map_text
    assert "broker API\nimport/connect" in map_text
    assert "proof rerun" in map_text
    assert "account/order/execution access" in map_text
    assert "exact future date" in map_text
    assert "explicit regular-session window" in map_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in map_text
    assert "6:55 AM\nPacific readiness-check boundary only" in map_text
    assert "explicit expected source commit" in map_text
    assert "clean\nworktree requirement before and after" in map_text
    assert "explicit TWS/manual operator readiness\nboundary" in map_text
    assert "historical-market-data-only command" in map_text
    assert "explicit compact output handling" in map_text
    assert "no account/position/margin/buying-power/portfolio/order/balance/execution/" in map_text
    assert "no package capture,\nreplay, scoring, candidate generation" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "opens no market-test authority" in map_text
    assert "VPS proof authority" in map_text
    assert "protocol-probe\nauthority" in map_text
    assert "endpoint-switch authority" in map_text
    assert "D11\ncompletion authority" in map_text
    assert "Unit 12 opening authority" in map_text


def test_d11_52_official_ibkr_endpoint_docs_adjudication_preserves_boundaries() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_official_endpoint_documentation_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.52 Official IBKR Endpoint Documentation Adjudication" in packet_text
    assert (
        "`adjudication_status` | "
        "`OFFICIAL_IBKR_ENDPOINT_DOCUMENTATION_ADJUDICATION`" in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`79e5d354c1bba7b1b3b45d1b3ec8267c5a32e052`" in packet_text
    )
    assert "`d11_51_vps_validation` | `71 passed in 2.36s`" in packet_text
    assert "`official_tws_api_transport` | `TCP_SOCKET`" in packet_text
    assert "`official_tws_live_default_port` | `7496`" in packet_text
    assert "`official_tws_paper_default_port` | `7497`" in packet_text
    assert "`official_gateway_live_default_port` | `4001`" in packet_text
    assert "`official_gateway_paper_default_port` | `4002`" in packet_text
    assert "`configured_port_must_match_client_port` | `true`" in packet_text
    assert "`mac_local_endpoint_selection_authorized` | `false`" in packet_text
    assert "`mac_local_endpoint_inspection_authorized` | `false`" in packet_text
    assert "`mac_local_market_test_authorized` | `false`" in packet_text
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "https://interactivebrokers.github.io/tws-api/initial_setup.html" in (
        packet_text
    )
    assert "https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/" in packet_text
    assert (
        "https://ibkrcampus.com/campus/trading-lessons/"
        "accessing-the-tws-python-api-source-code/" in packet_text
    )
    assert "TWS API uses a TCP socket\nconnection" in packet_text
    assert "default TWS socket ports as `7496` for live TWS and `7497` for paper TWS" in packet_text
    assert "live IB\nGateway `4001`" in packet_text
    assert "simulated/paper IB Gateway\n`4002`" in packet_text
    assert "endpoint is not guessed" in packet_text
    assert "API client port and the configured TWS/Gateway\nsocket port must match" in packet_text
    assert "does not authorize endpoint inspection yet" in packet_text
    assert "does not authorize Mac-local market testing yet" in packet_text
    assert "TWS/Gateway connection commands" in packet_text
    assert "broker API import/connect" in packet_text
    assert "Exact expected source commit" in packet_text
    assert "Clean worktree requirement" in packet_text
    assert "Explicit operator-readiness boundary" in packet_text
    assert "Exact non-mutating inspection commands only" in packet_text
    assert "No broker API import/connect" in packet_text
    assert "No market-data request" in packet_text
    assert "No account/order/execution authority" in packet_text
    assert "Exact future date" in packet_text
    assert "Explicit regular-session window" in packet_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in packet_text
    assert "6:55 AM Pacific readiness-check boundary only" in packet_text
    assert "Explicit TWS/manual operator readiness boundary" in packet_text
    assert "Historical-market-data-only command" in packet_text
    assert "Explicit compact output handling" in packet_text
    assert "No account, position, margin, buying-power, portfolio" in packet_text
    assert "No package capture, replay, scoring, candidate generation" in packet_text
    assert "endpoint selection" in packet_text
    assert "endpoint inspection" in packet_text
    assert "market-test authority" in packet_text
    assert "VPS proof authority" in packet_text
    assert "protocol-probe authority" in packet_text
    assert "endpoint-switch authority" in packet_text
    assert "d11_completion_authority=false" in packet_text
    assert "unit_12_opening_authority=false" in packet_text

    assert "### D11.52 Official IBKR Endpoint Documentation Adjudication" in map_text
    assert str(packet_path) in map_text
    assert "`OFFICIAL_IBKR_ENDPOINT_DOCUMENTATION_ADJUDICATION`" in map_text
    assert "`79e5d354c1bba7b1b3b45d1b3ec8267c5a32e052`" in map_text
    assert "`71 passed in 2.36s`" in map_text
    assert "https://interactivebrokers.github.io/tws-api/initial_setup.html" in (
        map_text
    )
    assert "https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/" in map_text
    assert (
        "https://ibkrcampus.com/campus/trading-lessons/"
        "accessing-the-tws-python-api-source-code/" in map_text
    )
    assert "`official_tws_api_transport=TCP_SOCKET`" in map_text
    assert "`official_tws_live_default_port=7496`" in map_text
    assert "`official_tws_paper_default_port=7497`" in map_text
    assert "`official_gateway_live_default_port=4001`" in map_text
    assert "`official_gateway_paper_default_port=4002`" in map_text
    assert "`configured_port_must_match_client_port=true`" in map_text
    assert "endpoint is not guessed" in map_text
    assert "must match the configured TWS/Gateway socket port" in map_text
    assert "`mac_local_endpoint_selection_authorized=false`" in map_text
    assert "`mac_local_endpoint_inspection_authorized=false`" in map_text
    assert "`mac_local_market_test_authorized=false`" in map_text
    assert "`vps_market_test_authorized=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`protocol_probe_authorized=false`" in map_text
    assert "`endpoint_switch_authorized=false`" in map_text
    assert "does not authorize TWS/Gateway\nconnection commands" in map_text
    assert "broker API import/connect" in map_text
    assert "exact expected source commit" in map_text
    assert "clean worktree\nrequirement" in map_text
    assert "explicit operator-readiness boundary" in map_text
    assert "exact non-mutating inspection\ncommands only" in map_text
    assert "no broker API import/connect" in map_text
    assert "no market-data request" in map_text
    assert "no\naccount/order/execution authority" in map_text
    assert "exact future date" in map_text
    assert "explicit regular-session window" in map_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in map_text
    assert "6:55 AM\nPacific readiness-check boundary only" in map_text
    assert "historical-market-data-only command" in map_text
    assert "explicit compact output handling" in map_text
    assert "no account/position/margin/buying-power/portfolio/order/balance/execution/" in map_text
    assert "no package capture,\nreplay, scoring, candidate generation" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text


def test_d11_53_mac_local_endpoint_inspection_authorizes_listener_only() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_mac_local_endpoint_inspection_authorization.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.53 Mac-Local Endpoint Inspection Authorization" in packet_text
    assert (
        "`authorization_status` | `MAC_LOCAL_ENDPOINT_INSPECTION_AUTHORIZATION`"
        in packet_text
    )
    assert (
        "`current_validated_source_commit` | "
        "`6f50a0d1a795eed2ec69559c9b6ba61ed8875b18`" in packet_text
    )
    assert "`d11_52_vps_validation` | `72 passed in 1.76s`" in packet_text
    assert "`mac_local_endpoint_inspection_authorized` | `true`" in packet_text
    assert "`mac_local_endpoint_selection_authorized` | `false`" in packet_text
    assert "`mac_local_market_test_authorized` | `false`" in packet_text
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`official_tws_live_default_port` | `7496`" in packet_text
    assert "`official_tws_paper_default_port` | `7497`" in packet_text
    assert "`official_gateway_live_default_port` | `4001`" in packet_text
    assert "`official_gateway_paper_default_port` | `4002`" in packet_text
    assert "`configured_port_must_match_client_port` | `true`" in packet_text
    assert "`allowed_inspection_mode` | `LOCAL_LISTENER_INSPECTION_ONLY`" in (
        packet_text
    )
    assert "`broker_api_import_authorized` | `false`" in packet_text
    assert "`broker_connect_authorized` | `false`" in packet_text
    assert "`market_data_request_authorized` | `false`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "adjudicated official IBKR endpoints" in packet_text
    assert "endpoint is not guessed" in packet_text
    assert "must be observed locally and later matched to\nconfigured TWS/Gateway socket settings" in packet_text
    assert "authorizes only `LOCAL_LISTENER_INSPECTION_ONLY`" in packet_text
    assert "compact and may inspect only local listening sockets\nand process identity" in packet_text
    assert "- `7496`" in packet_text
    assert "- `7497`" in packet_text
    assert "- `4001`" in packet_text
    assert "- `4002`" in packet_text
    assert "does not authorize broker API import/connect" in packet_text
    assert "sending traffic to any\nendpoint" in packet_text
    assert "`nc`, `curl`, `telnet`, `/dev/tcp`, Python socket connect" in (
        packet_text
    )
    assert "broker API\nconnect" in packet_text
    assert "market-data requests" in packet_text
    assert "endpoint selection" in packet_text
    assert "Mac-local market testing" in packet_text
    assert "VPS market testing" in packet_text
    assert "proof rerun" in packet_text
    assert "Any later endpoint selection must be separately source-controlled" in (
        packet_text
    )
    assert "Exact future date" in packet_text
    assert "Explicit regular-session window" in packet_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in packet_text
    assert "6:55 AM Pacific readiness-check boundary only" in packet_text
    assert "Explicit expected source commit" in packet_text
    assert "Clean worktree requirement before and after" in packet_text
    assert "Explicit TWS/manual operator readiness boundary" in packet_text
    assert "Historical-market-data-only command" in packet_text
    assert "Explicit compact output handling" in packet_text
    assert "No account, position, margin, buying-power, portfolio" in packet_text
    assert "No package capture, replay, scoring, candidate generation" in packet_text
    assert "broker_api_import_authorized=false" in packet_text
    assert "broker_connect_authorized=false" in packet_text
    assert "market_data_request_authorized=false" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "d11_completion_authority=false" in packet_text
    assert "unit_12_opening_authority=false" in packet_text

    assert "### D11.53 Mac-Local Endpoint Inspection Authorization" in map_text
    assert str(packet_path) in map_text
    assert "`MAC_LOCAL_ENDPOINT_INSPECTION_AUTHORIZATION`" in map_text
    assert "`6f50a0d1a795eed2ec69559c9b6ba61ed8875b18`" in map_text
    assert "`72 passed in 1.76s`" in map_text
    assert "`official_tws_live_default_port=7496`" in map_text
    assert "`official_tws_paper_default_port=7497`" in map_text
    assert "`official_gateway_live_default_port=4001`" in map_text
    assert "`official_gateway_paper_default_port=4002`" in map_text
    assert "`configured_port_must_match_client_port=true`" in map_text
    assert "endpoint is not guessed" in map_text
    assert "must be observed locally and later matched" in map_text
    assert "`mac_local_endpoint_inspection_authorized=true`" in map_text
    assert "`allowed_inspection_mode=LOCAL_LISTENER_INSPECTION_ONLY`" in map_text
    assert "compact and may inspect only local listening sockets" in map_text
    assert "`7496`, `7497`, `4001`, and `4002`" in map_text
    assert "`mac_local_endpoint_selection_authorized=false`" in map_text
    assert "`mac_local_market_test_authorized=false`" in map_text
    assert "`vps_market_test_authorized=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`protocol_probe_authorized=false`" in map_text
    assert "`endpoint_switch_authorized=false`" in map_text
    assert "`broker_api_import_authorized=false`" in map_text
    assert "`broker_connect_authorized=false`" in map_text
    assert "`market_data_request_authorized=false`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "does not authorize sending traffic to any endpoint" in map_text
    assert "`nc`, `curl`, `telnet`, `/dev/tcp`, Python socket connect" in map_text
    assert "broker API connect" in map_text
    assert "market-data requests" in map_text
    assert "Any later endpoint selection must be separately\nsource-controlled" in (
        map_text
    )
    assert "exact future date" in map_text
    assert "explicit regular-session window" in map_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in map_text
    assert "6:55 AM\nPacific readiness-check boundary only" in map_text
    assert "explicit expected source commit" in map_text
    assert "clean\nworktree requirement before and after" in map_text
    assert "historical-market-data-only command" in map_text
    assert "explicit compact output handling" in map_text
    assert "no account/position/margin/buying-power/portfolio/order/balance/execution/" in map_text
    assert "no package capture,\nreplay, scoring, candidate generation" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text


def test_d11_54_mac_local_endpoint_listener_adjudication_preserves_boundaries() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_mac_local_endpoint_listener_evidence_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.54 Mac-Local Endpoint Listener Evidence Adjudication" in packet_text
    assert (
        "`adjudication_status` | "
        "`MAC_LOCAL_ENDPOINT_LISTENER_EVIDENCE_ADJUDICATION`" in packet_text
    )
    assert (
        "`source_commit` | `62ce269f9105f38f6ac9bde69e4263a8a282491c`"
        in packet_text
    )
    assert (
        "`source_commit_message` | "
        "`62ce269 Authorize D11 Mac-local endpoint inspection`" in packet_text
    )
    assert "`d11_53_vps_validation` | `73 passed in 2.28s`" in packet_text
    assert "`observed_mac_local_tws_paper_listener` | `true`" in packet_text
    assert "`observed_mac_local_tws_paper_port` | `7497`" in packet_text
    assert (
        "`observed_mac_local_tws_process` | "
        "`Trader Workstation JavaApplicationStub`" in packet_text
    )
    assert "`observed_mac_local_tws_live_listener` | `false`" in packet_text
    assert "`observed_mac_local_gateway_live_listener` | `false`" in packet_text
    assert "`observed_mac_local_gateway_paper_listener` | `false`" in packet_text
    assert "`candidate_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`endpoint_selection_authorized` | `false`" in packet_text
    assert "`mac_local_market_test_authorized` | `false`" in packet_text
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`broker_api_import_authorized` | `false`" in packet_text
    assert "`broker_connect_authorized` | `false`" in packet_text
    assert "`market_data_request_authorized` | `false`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "operator listener command was local-listener inspection only" in packet_text
    assert "COMMAND=JavaAppli" in packet_text
    assert "PID=13194" in packet_text
    assert "USER=openclawcontrol" in packet_text
    assert "TCP *:7497 (LISTEN)" in packet_text
    assert (
        "/Users/openclawcontrol/Applications/Trader Workstation/"
        "Trader Workstation.app/Contents/MacOS/JavaApplicationStub" in packet_text
    )
    assert "No listener was shown for official IBKR ports `7496`, `4001`, or `4002`" in packet_text
    assert "Port `7497` matches the official IBKR paper TWS default" in packet_text
    assert "resolves the prior endpoint ambiguity for Mac-local context only" in (
        packet_text
    )
    assert "does not retroactively make the VPS `127.0.0.1:7497` endpoint\nvalid" in (
        packet_text
    )
    assert "`127.0.0.1` on VPS and `127.0.0.1` on Mac are different process\ncontexts" in (
        packet_text
    )
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "`candidate_mac_local_endpoint=127.0.0.1:7497`" in packet_text
    assert "`endpoint_selection_authorized=false`" in packet_text
    assert "Mac-local market testing remains\nunauthorized" in packet_text
    assert "Broker API import/connect remains unauthorized" in packet_text
    assert "Market-data\nrequests remain unauthorized" in packet_text
    assert "Account/order/execution authority remains false" in packet_text
    assert "Any future endpoint selection must be separately source-controlled" in (
        packet_text
    )
    assert "Exact future date" in packet_text
    assert "Explicit regular-session window" in packet_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in packet_text
    assert "6:55 AM Pacific readiness-check boundary only" in packet_text
    assert "Explicit expected source commit" in packet_text
    assert "Clean worktree requirement before and after" in packet_text
    assert "Explicit TWS/manual operator readiness boundary" in packet_text
    assert "Historical-market-data-only command" in packet_text
    assert "Explicit compact output handling" in packet_text
    assert "No account, position, margin, buying-power, portfolio" in packet_text
    assert "No package capture, replay, scoring, candidate generation" in packet_text
    assert "broker_api_import_authorized=false" in packet_text
    assert "broker_connect_authorized=false" in packet_text
    assert "market_data_request_authorized=false" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "d11_completion_authority=false" in packet_text
    assert "unit_12_opening_authority=false" in packet_text

    assert "### D11.54 Mac-Local Endpoint Listener Evidence Adjudication" in map_text
    assert str(packet_path) in map_text
    assert "`MAC_LOCAL_ENDPOINT_LISTENER_EVIDENCE_ADJUDICATION`" in map_text
    assert "`source_commit=62ce269f9105f38f6ac9bde69e4263a8a282491c`" in map_text
    assert "`source_commit_message=62ce269 Authorize D11 Mac-local endpoint inspection`" in map_text
    assert "`73 passed in 2.28s`" in map_text
    assert "operator listener command was local-listener inspection\nonly" in map_text
    assert "`COMMAND=JavaAppli`" in map_text
    assert "`PID=13194`" in map_text
    assert "`USER=openclawcontrol`" in map_text
    assert "`TCP *:7497 (LISTEN)`" in map_text
    assert "Trader Workstation.app/Contents/MacOS/JavaApplicationStub" in map_text
    assert "`observed_mac_local_tws_paper_listener=true`" in map_text
    assert "`observed_mac_local_tws_paper_port=7497`" in map_text
    assert "`observed_mac_local_tws_process=Trader Workstation JavaApplicationStub`" in (
        map_text
    )
    assert "`observed_mac_local_tws_live_listener=false`" in map_text
    assert "`observed_mac_local_gateway_live_listener=false`" in map_text
    assert "`observed_mac_local_gateway_paper_listener=false`" in map_text
    assert "Port `7497` matches the official IBKR paper TWS default" in map_text
    assert "Mac-local context only" in map_text
    assert "not retroactively make the VPS `127.0.0.1:7497` endpoint valid" in (
        map_text
    )
    assert "`127.0.0.1` on VPS and `127.0.0.1` on Mac are different process contexts" in (
        map_text
    )
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a proven TWS issue" in map_text
    assert "`candidate_mac_local_endpoint=127.0.0.1:7497`" in map_text
    assert "`endpoint_selection_authorized=false`" in map_text
    assert "`mac_local_market_test_authorized=false`" in map_text
    assert "`broker_api_import_authorized=false`" in map_text
    assert "`broker_connect_authorized=false`" in map_text
    assert "`market_data_request_authorized=false`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "Any future endpoint selection must\nbe separately source-controlled" in (
        map_text
    )
    assert "exact future date" in map_text
    assert "explicit regular-session window" in map_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in map_text
    assert "6:55 AM\nPacific readiness-check boundary only" in map_text
    assert "historical-market-data-only command" in map_text
    assert "explicit compact output handling" in map_text
    assert "no account/position/margin/buying-power/portfolio/order/balance/execution/" in map_text
    assert "no package capture,\nreplay, scoring, candidate generation" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text


def test_d11_55_mac_local_endpoint_selection_adjudication_preserves_boundaries() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_mac_local_endpoint_selection_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.55 Mac-Local Endpoint Selection Adjudication" in packet_text
    assert (
        "`adjudication_status` | `MAC_LOCAL_ENDPOINT_SELECTION_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `90545de3c6fcfb8ebacea282a751ae3305b78f26`"
        in packet_text
    )
    assert "`d11_54_vps_validation` | `74 passed in 2.24s`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_endpoint_port` | `7497`" in packet_text
    assert (
        "`selected_endpoint_basis` | "
        "`D11.54 observed Mac-local TWS paper listener evidence`" in packet_text
    )
    assert "`endpoint_selection_authorized` | `true`" in packet_text
    assert "`mac_local_market_test_authorized` | `false`" in packet_text
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`broker_api_import_authorized` | `false`" in packet_text
    assert "`broker_connect_authorized` | `false`" in packet_text
    assert "`market_data_request_authorized` | `false`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "Trader Workstation JavaApplicationStub listening on\n`TCP *:7497`" in (
        packet_text
    )
    assert "Port `7497` matches the official IBKR paper TWS default" in packet_text
    assert "`candidate_mac_local_endpoint=127.0.0.1:7497`" in packet_text
    assert "`selected_mac_local_endpoint=127.0.0.1:7497`" in packet_text
    assert "valid only for the `LOCAL_MAC` process context" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "does not authorize Mac-local\nmarket testing" in packet_text
    assert "broker API import/connect" in packet_text
    assert "market-data requests" in packet_text
    assert "account/order/\nexecution authority" in packet_text
    assert "Exact future date" in packet_text
    assert "Explicit regular-session window" in packet_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in packet_text
    assert "6:55 AM Pacific readiness-check boundary only" in packet_text
    assert "Explicit expected source commit" in packet_text
    assert "Clean worktree requirement before and after" in packet_text
    assert "Explicit TWS/manual operator readiness boundary" in packet_text
    assert "Historical-market-data-only command" in packet_text
    assert "Explicit compact output handling" in packet_text
    assert "No account, position, margin, buying-power, portfolio" in packet_text
    assert "No package capture, replay, scoring, candidate generation" in packet_text
    assert "broker_api_import_authorized=false" in packet_text
    assert "broker_connect_authorized=false" in packet_text
    assert "market_data_request_authorized=false" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "d11_completion_authority=false" in packet_text
    assert "unit_12_opening_authority=false" in packet_text

    assert "### D11.55 Mac-Local Endpoint Selection Adjudication" in map_text
    assert str(packet_path) in map_text
    assert "`MAC_LOCAL_ENDPOINT_SELECTION_ADJUDICATION`" in map_text
    assert "`source_commit=90545de3c6fcfb8ebacea282a751ae3305b78f26`" in map_text
    assert "`74 passed in 2.24s`" in map_text
    assert "`observed_mac_local_tws_paper_listener=true`" in map_text
    assert "`observed_mac_local_tws_paper_port=7497`" in map_text
    assert "`observed_mac_local_tws_process=Trader Workstation JavaApplicationStub`" in (
        map_text
    )
    assert "`candidate_mac_local_endpoint=127.0.0.1:7497`" in map_text
    assert "Trader Workstation JavaApplicationStub listening on\n`TCP *:7497`" in (
        map_text
    )
    assert "`7497` matches the official IBKR paper TWS default" in map_text
    assert "`selected_mac_local_endpoint=127.0.0.1:7497`" in map_text
    assert "`selected_endpoint_context=LOCAL_MAC`" in map_text
    assert "`selected_endpoint_type=TWS_PAPER`" in map_text
    assert "`selected_endpoint_port=7497`" in map_text
    assert (
        "`selected_endpoint_basis=D11.54 observed Mac-local TWS paper listener "
        "evidence`" in map_text
    )
    assert "valid only for the `LOCAL_MAC` process context" in map_text
    assert "not validate VPS `127.0.0.1:7497`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a proven TWS issue" in map_text
    assert "`endpoint_selection_authorized=true`" in map_text
    assert "`mac_local_market_test_authorized=false`" in map_text
    assert "`vps_market_test_authorized=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`protocol_probe_authorized=false`" in map_text
    assert "`endpoint_switch_authorized=false`" in map_text
    assert "`broker_api_import_authorized=false`" in map_text
    assert "`broker_connect_authorized=false`" in map_text
    assert "`market_data_request_authorized=false`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "exact future date" in map_text
    assert "explicit regular-session window" in map_text
    assert "at or after 7:00 AM Pacific / 10:00 AM Eastern" in map_text
    assert "6:55 AM\nPacific readiness-check boundary only" in map_text
    assert "historical-market-data-only command" in map_text
    assert "explicit compact output handling" in map_text
    assert "no account/position/margin/buying-power/portfolio/order/balance/execution/" in map_text
    assert "no package capture,\nreplay, scoring, candidate generation" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text


def test_d11_56_mac_local_historical_data_preflight_authorizes_bounded_future_run() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_mac_local_historical_data_test_preflight.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.56 Mac-Local Historical Market-Data Test Preflight" in packet_text
    assert (
        "`preflight_status` | `MAC_LOCAL_HISTORICAL_MARKET_DATA_TEST_PREFLIGHT`"
        in packet_text
    )
    assert (
        "`source_commit` | `d64ee84942533a4727df66b72c9e4175bb6713c1`"
        in packet_text
    )
    assert "`d11_55_vps_validation` | `75 passed in 2.07s`" in packet_text
    assert "`test_date` | `2026-06-26`" in packet_text
    assert "`readiness_check_time_pacific` | `06:55`" in packet_text
    assert "`readiness_check_time_eastern` | `09:55`" in packet_text
    assert "`diagnostic_not_before_pacific` | `07:00`" in packet_text
    assert "`diagnostic_not_before_eastern` | `10:00`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_endpoint_port` | `7497`" in packet_text
    assert "`mac_local_market_test_preflight_authorized` | `true`" in packet_text
    assert (
        "`mac_local_market_test_authorized_for_2026_06_26_after_0700_pacific` "
        "| `true`" in packet_text
    )
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`proof_rerun_authorized` | `false`" in packet_text
    assert "`protocol_probe_authorized` | `false`" in packet_text
    assert "`endpoint_switch_authorized` | `false`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert (
        "`diagnostic_command_status` | "
        "`AUTHORIZED_FROM_EXISTING_LOCAL_READ_ONLY_SMOKE_PATTERN`" in packet_text
    )
    assert "`selected_mac_local_endpoint=127.0.0.1:7497`" in packet_text
    assert "valid only for the `LOCAL_MAC` process context" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "future diagnostic is Mac-local only" in packet_text
    assert "VPS is only for source sync and tests" in packet_text
    assert "Trader Workstation must be manually open and logged\ninto paper mode" in (
        packet_text
    )
    assert "Source worktree must be clean before and\nafter the diagnostic" in (
        packet_text
    )
    assert "`06:55` Pacific / `09:55` Eastern time is a readiness-check boundary only" in (
        packet_text
    )
    assert "must not run before `07:00` Pacific /\n`10:00` Eastern" in packet_text
    assert "Do not use 6:30 AM Pacific / 9:30 AM Eastern" in packet_text
    assert "docs/ibkr_market_data_repeatability_ledger_template.md" in packet_text
    assert "tools.ops.ibkr_market_data_read_only_smoke" in packet_text
    assert "--authorize-local-ibkr-read-only-smoke" in packet_text
    assert "cd /Users/openclawcontrol/Documents/openclaw-stocks" in packet_text
    assert ".venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke" in (
        packet_text
    )
    assert "REQUESTED_END_UTC='2026-06-26T14:00:00Z'" in packet_text
    assert "--host 127.0.0.1" in packet_text
    assert "--port 7497" in packet_text
    assert "--lookback-minutes 120" in packet_text
    assert "SUMMARY_START" in packet_text
    assert "SUMMARY_END" in packet_text
    for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"):
        assert f"--symbol {symbol}" in packet_text
        assert f"`{symbol}`" in packet_text
    assert "Timeframe: `15Min`" in packet_text
    assert "historical-market-data-only" in packet_text
    assert "market-data freshness and 15-minute candle timing" in packet_text
    assert "command used" in packet_text
    assert "source commit" in packet_text
    assert "clean pre-worktree" in packet_text
    assert "clean post-worktree" in packet_text
    assert "dependency versions" in packet_text
    assert "endpoint host and port" in packet_text
    assert "requested UTC window" in packet_text
    assert "latest candle timestamp per instrument" in packet_text
    assert "pass/fail classification" in packet_text
    assert "no account/order/execution fields" in packet_text
    assert "no account, position, margin, buying-power" in packet_text
    assert "no package capture, replay, scoring, candidate\ngeneration" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "d11_completion_authority=false" in packet_text
    assert "unit_12_opening_authority=false" in packet_text

    assert "### D11.56 Mac-Local Historical Market-Data Test Preflight" in map_text
    assert str(packet_path) in map_text
    assert "`MAC_LOCAL_HISTORICAL_MARKET_DATA_TEST_PREFLIGHT`" in map_text
    assert "`source_commit=d64ee84942533a4727df66b72c9e4175bb6713c1`" in map_text
    assert "`75 passed in 2.07s`" in map_text
    assert "`selected_mac_local_endpoint=127.0.0.1:7497`" in map_text
    assert "`selected_endpoint_context=LOCAL_MAC`" in map_text
    assert "`selected_endpoint_type=TWS_PAPER`" in map_text
    assert "`selected_endpoint_port=7497`" in map_text
    assert "not validate VPS `127.0.0.1:7497`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "`test_date=2026-06-26`" in map_text
    assert "`readiness_check_time_pacific=06:55`" in map_text
    assert "`diagnostic_not_before_pacific=07:00`" in map_text
    assert "must not use 6:30 AM Pacific / 9:30\nAM Eastern" in map_text
    assert "`mac_local_market_test_preflight_authorized=true`" in map_text
    assert "`mac_local_market_test_authorized_for_2026_06_26_after_0700_pacific=true`" in (
        map_text
    )
    assert "`vps_market_test_authorized=false`" in map_text
    assert "`proof_rerun_authorized=false`" in map_text
    assert "`protocol_probe_authorized=false`" in map_text
    assert "`endpoint_switch_authorized=false`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "future diagnostic is Mac-local only" in map_text
    assert "VPS is only for source sync and tests" in map_text
    assert "TWS must be manually open and logged into paper mode" in map_text
    assert "worktree must be clean before and after" in map_text
    assert ".venv-312/bin/python -m\ntools.ops.ibkr_market_data_read_only_smoke" in (
        map_text
    )
    assert "`--authorize-local-ibkr-read-only-smoke`" in map_text
    assert "host `127.0.0.1`, port `7497`" in map_text
    assert "symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in map_text
    assert "`--requested-end 2026-06-26T14:00:00Z`" in map_text
    assert "`--lookback-minutes 120`" in map_text
    assert "cd /Users/openclawcontrol/Documents/openclaw-stocks" in map_text
    assert "`SUMMARY_START` and `SUMMARY_END`" in map_text
    assert "latest candle timestamp per instrument" in map_text
    assert "market-data freshness and 15-minute candle timing" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text


def test_d11_57_mac_local_historical_diagnostic_evidence_adjudication() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_mac_local_historical_data_diagnostic_evidence_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.57 Mac-Local Historical Market-Data Diagnostic Evidence Adjudication"
        in packet_text
    )
    assert (
        "`classification` | "
        "`MAC_LOCAL_HISTORICAL_MARKET_DATA_DIAGNOSTIC_EVIDENCE_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `5fa8a8e221b79219c86eb3abcd67ad491692de21`"
        in packet_text
    )
    assert "`d11_56_vps_validation` | `76 passed in 2.49s`" in packet_text
    assert "`diagnostic_date` | `2026-06-26`" in packet_text
    assert "`authorized_utc` | `2026-06-26T14:00:00Z`" in packet_text
    assert "`observed_run_utc` | `2026-06-26T14:00:26Z`" in packet_text
    assert "`diagnostic_window_guard` | `PASSED`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_endpoint_port` | `7497`" in packet_text
    assert "`observed_listener` | `TCP *:7497 (LISTEN)`" in packet_text
    assert "`observed_dependency_ib_insync` | `0.9.86`" in packet_text
    assert "`symbols` | `AAPL,MSFT,NVDA,TSLA,MSTR`" in packet_text
    assert "`timeframe` | `15Min`" in packet_text
    assert "`requested_start_utc` | `2026-06-26T12:00:00+00:00`" in packet_text
    assert "`requested_end_utc` | `2026-06-26T14:00:00+00:00`" in packet_text
    assert "`worktree_before` | `CLEAN`" in packet_text
    assert "`worktree_after` | `CLEAN`" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`d11_primary_candidate_status` | `candidate`" in packet_text
    assert "`d11_primary_eligible` | `false`" in packet_text
    assert "`mac_local_historical_diagnostic_evidence` | `ACCEPTED`" in packet_text
    assert "`vps_market_test_authorized` | `false`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "after the authorized\n`2026-06-26T14:00:00Z` boundary" in packet_text
    assert "valid only for the\n`LOCAL_MAC` process context" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "historical-market-data-only" in packet_text
    assert "No account, position, margin, buying-power, portfolio, order, execution" in (
        packet_text
    )
    assert "No package capture, replay,\nscoring, candidate generation" in packet_text
    assert "does not approve IBKR as primary" in packet_text
    assert "does not complete D11" in packet_text
    assert "does not unblock Unit 12" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in packet_text
    for symbol, timestamp, lag in (
        ("AAPL", "2026-06-26T13:30:00+00:00", "30.0"),
        ("MSFT", "2026-06-26T13:30:00+00:00", "30.0"),
        ("NVDA", "2026-06-26T13:45:00+00:00", "15.0"),
        ("TSLA", "2026-06-26T13:45:00+00:00", "15.0"),
        ("MSTR", "2026-06-26T13:45:00+00:00", "15.0"),
    ):
        assert f"| `{symbol}` | `true` | `clean` | `{timestamp}` | `{lag}` |" in (
            packet_text
        )

    assert "### D11.57 Mac-Local Historical Diagnostic Evidence Adjudication" in (
        map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`MAC_LOCAL_HISTORICAL_MARKET_DATA_DIAGNOSTIC_EVIDENCE_ADJUDICATION`"
        in map_text
    )
    assert "`source_commit=5fa8a8e221b79219c86eb3abcd67ad491692de21`" in map_text
    assert "`76 passed in 2.49s`" in map_text
    assert "`authorized_utc=2026-06-26T14:00:00Z`" in map_text
    assert "`observed_run_utc=2026-06-26T14:00:26Z`" in map_text
    assert "`diagnostic_window_guard=PASSED`" in map_text
    assert "`worktree_before=CLEAN`" in map_text
    assert "`worktree_after=CLEAN`" in map_text
    assert "`selected_mac_local_endpoint=127.0.0.1:7497`" in map_text
    assert "`selected_endpoint_context=LOCAL_MAC`" in map_text
    assert "`selected_endpoint_type=TWS_PAPER`" in map_text
    assert "`selected_endpoint_port=7497`" in map_text
    assert "`observed_listener=TCP *:7497 (LISTEN)`" in map_text
    assert "`observed_dependency_ib_insync=0.9.86`" in map_text
    assert "does not validate VPS\n`127.0.0.1:7497`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "`requested_start_utc=2026-06-26T12:00:00+00:00`" in map_text
    assert "`requested_end_utc=2026-06-26T14:00:00+00:00`" in map_text
    assert "All five symbols returned\n`d11_countable=true`" in map_text
    assert "`freshness_classification=clean`" in map_text
    assert "`AAPL=2026-06-26T13:30:00+00:00/30.0`" in map_text
    assert "`MSFT=2026-06-26T13:30:00+00:00/30.0`" in map_text
    assert "`NVDA=2026-06-26T13:45:00+00:00/15.0`" in map_text
    assert "`TSLA=2026-06-26T13:45:00+00:00/15.0`" in map_text
    assert "`MSTR=2026-06-26T13:45:00+00:00/15.0`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`vps_market_test_authorized=false`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "grants no account, order, execution, package capture, replay" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text


def test_d11_58_ibkr_primary_eligibility_adjudication_fails_closed() -> None:
    packet_path = Path("docs/ibkr_market_data_primary_eligibility_adjudication.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.58 IBKR Primary Market-Data Eligibility Adjudication" in packet_text
    assert (
        "`classification` | `IBKR_PRIMARY_MARKET_DATA_ELIGIBILITY_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `4839f8ff3f09f746edcca3ab464a4771ae922f0d`"
        in packet_text
    )
    assert (
        "`d11_57_vps_validation` | "
        "`77 passed in 3.05s and 77 passed in 0.25s`" in packet_text
    )
    assert "`mac_local_historical_diagnostic_evidence` | `ACCEPTED`" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_endpoint_port` | `7497`" in packet_text
    assert "`endpoint_scope` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`vps_127_0_0_1_7497_validated` | `false`" in packet_text
    assert (
        "`prior_vps_failure` | "
        "`VPS_LOCALHOST_CONTEXT_MISMATCH / "
        "AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert (
        "`d11_primary_eligibility_adjudication` | "
        "`BLOCKED_CRITERIA_UNRESOLVED`" in packet_text
    )
    assert "`d11_primary_candidate_status` | `candidate`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "Decision: fail closed" in packet_text
    assert (
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility"
        in packet_text
    )
    assert "D11.34" in packet_text
    assert "D11.56 preflight" in packet_text
    assert "D11.57 accepted Mac-local historical diagnostic evidence" in packet_text
    assert "All five were clean and countable" in packet_text
    assert "endpoint scope is\n  `LOCAL_MAC_ONLY`" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "candidate_can_count_for_d11` is not satisfied" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "records no package capture, replay, scoring, candidate generation" in (
        packet_text
    )
    assert "Unit 12 opening" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in packet_text

    assert "### D11.58 IBKR Primary Market-Data Eligibility Adjudication" in (
        map_text
    )
    assert str(packet_path) in map_text
    assert "`IBKR_PRIMARY_MARKET_DATA_ELIGIBILITY_ADJUDICATION`" in map_text
    assert "`source_commit=4839f8ff3f09f746edcca3ab464a4771ae922f0d`" in map_text
    assert "`77 passed in 3.05s and 77 passed in 0.25s`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`all_symbols_d11_countable=true`" in map_text
    assert "`all_symbols_freshness_classification=clean`" in map_text
    assert "fails closed on primary eligibility" in map_text
    assert (
        "`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`"
        in map_text
    )
    assert "`endpoint_scope=LOCAL_MAC_ONLY`" in map_text
    assert "`vps_127_0_0_1_7497_validated=false`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a proven TWS issue" in map_text
    assert "absent separate VPS read-only freshness proof" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert (
        "`d11_primary_eligibility_adjudication=BLOCKED_CRITERIA_UNRESOLVED`"
        in map_text
    )
    assert "`d11_primary_candidate_status=candidate`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_59_vps_proof_requirement_route_adjudication_safe_preflight() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_proof_requirement_route_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.59 IBKR VPS Proof Requirement Route Adjudication" in packet_text
    assert (
        "`classification` | `IBKR_VPS_PROOF_REQUIREMENT_ROUTE_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `874544fb1b860bf753d788f20bf3f143b027ff11`"
        in packet_text
    )
    assert "`d11_58_vps_validation` | `78 passed in 2.39s`" in packet_text
    assert "`d11_58_result` | `BLOCKED_CRITERIA_UNRESOLVED`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`mac_local_historical_diagnostic_evidence` | `ACCEPTED`" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`endpoint_scope` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`vps_127_0_0_1_7497_validated` | `false`" in packet_text
    assert (
        "`prior_vps_failure` | "
        "`VPS_LOCALHOST_CONTEXT_MISMATCH / "
        "AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert (
        "`vps_proof_requirement_route` | "
        "`REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.60_SOURCE_CONTROLLED_VPS_PROOF_SAFE_PREFLIGHT_OR_FORMAL_LOCAL_MAC_CRITERIA_REVISION`"
        in packet_text
    )
    assert (
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility"
        in packet_text
    )
    assert "does not find an existing\nsource-controlled rule that retires" in (
        packet_text
    )
    assert "`127.0.0.1` is process-context local" in packet_text
    assert "VPS `127.0.0.1:7497` was not listening" in packet_text
    assert "previous VPS proof failed from the VPS process context" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "`NOT_PROVEN_TWS_ISSUE`" in packet_text
    assert "`NOT_PROVEN_IB_GATEWAY_ISSUE`" in packet_text
    assert (
        "cannot target `127.0.0.1:7497` unless that endpoint is\n"
        "observed listening in the VPS process context and separately authorized"
        in packet_text
    )
    assert "explicitly validated\n   VPS-accessible endpoint" in packet_text
    assert "formal source-controlled criteria revision" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "records no package capture, replay, scoring, candidate generation" in (
        packet_text
    )
    assert "Unit 12 opening" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in packet_text

    assert "### D11.59 IBKR VPS Proof Requirement Route Adjudication" in map_text
    assert str(packet_path) in map_text
    assert "`IBKR_VPS_PROOF_REQUIREMENT_ROUTE_ADJUDICATION`" in map_text
    assert "`source_commit=874544fb1b860bf753d788f20bf3f143b027ff11`" in map_text
    assert "`78 passed in 2.39s`" in map_text
    assert "`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`all_symbols_d11_countable=true`" in map_text
    assert "`all_symbols_freshness_classification=clean`" in map_text
    assert "`selected_endpoint_context=LOCAL_MAC`" in map_text
    assert "`selected_endpoint_type=TWS_PAPER`" in map_text
    assert "`selected_mac_local_endpoint=127.0.0.1:7497`" in map_text
    assert "`endpoint_scope=LOCAL_MAC_ONLY`" in map_text
    assert "`vps_127_0_0_1_7497_validated=false`" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a proven TWS issue" in map_text
    assert (
        "`vps_proof_requirement_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`"
        in map_text
    )
    assert (
        "`next_permissible_gate="
        "D11.60_SOURCE_CONTROLLED_VPS_PROOF_SAFE_PREFLIGHT_OR_FORMAL_LOCAL_MAC_CRITERIA_REVISION`"
        in map_text
    )
    assert "not `127.0.0.1:7497` unless observed listening" in map_text
    assert "formally revise the\nsource-controlled criteria" in map_text
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_60_vps_safe_preflight_or_local_mac_revision_fails_closed() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_proof_safe_preflight_or_local_mac_criteria_revision.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.60 IBKR VPS Proof Safe Preflight Or LOCAL_MAC Criteria Revision"
        in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_VPS_PROOF_SAFE_PREFLIGHT_OR_LOCAL_MAC_CRITERIA_REVISION`"
        in packet_text
    )
    assert (
        "`source_commit` | `002602313f022ea2581cd7d30d3453aca9b4f50f`"
        in packet_text
    )
    assert "`d11_59_vps_validation` | `79 passed in 2.77s`" in packet_text
    assert "`d11_59_route` | `REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`" in packet_text
    assert "`d11_58_result` | `BLOCKED_CRITERIA_UNRESOLVED`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`mac_local_historical_diagnostic_evidence` | `ACCEPTED`" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`endpoint_scope` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`vps_127_0_0_1_7497_validated` | `false`" in packet_text
    assert (
        "`prior_vps_failure` | "
        "`VPS_LOCALHOST_CONTEXT_MISMATCH / "
        "AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert "`vps_proof_safe_target_status` | `NO_VALIDATED_TARGET`" in packet_text
    assert "`local_mac_criteria_revision_status` | `NOT_SUPPORTED`" in packet_text
    assert (
        "`d11_60_decision` | "
        "`BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.61_SOURCE_CONTROLLED_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE`"
        in packet_text
    )
    assert (
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility"
        in packet_text
    )
    assert "finds no source-controlled, validated, VPS-accessible endpoint" in (
        packet_text
    )
    assert "VPS `127.0.0.1:7497`: rejected unless" in packet_text
    assert "`127.0.0.1` is process-context local" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS" in packet_text
    assert "prior VPS proof failed because VPS `127.0.0.1:7497` was not listening" in (
        packet_text
    )
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "not a proven IB Gateway issue" in packet_text
    assert (
        "cannot target `127.0.0.1:7497` unless that endpoint is\n"
        "observed listening in the VPS process context and separately authorized"
        in packet_text
    )
    assert "VPS `127.0.0.1:18789` and `127.0.0.1:18791`" in packet_text
    assert "not approved market-data\n  endpoints" in packet_text
    assert "finds no source-controlled basis to retire or narrow" in packet_text
    assert "no validated VPS-accessible endpoint suitable for market-data proof" in (
        packet_text
    )
    assert "no source-controlled basis to retire or narrow" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "records no package capture, replay, scoring, candidate generation" in (
        packet_text
    )
    assert "Unit 12 opening" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in packet_text

    assert "### D11.60 VPS Proof Safe Preflight Or LOCAL_MAC Criteria Revision" in (
        map_text
    )
    assert str(packet_path) in map_text
    assert "`IBKR_VPS_PROOF_SAFE_PREFLIGHT_OR_LOCAL_MAC_CRITERIA_REVISION`" in (
        map_text
    )
    assert "`source_commit=002602313f022ea2581cd7d30d3453aca9b4f50f`" in map_text
    assert "`79 passed in 2.77s`" in map_text
    assert "`d11_59_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`" in map_text
    assert "`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`" in map_text
    assert "`d11_60_decision=BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`" in (
        map_text
    )
    assert "`vps_proof_safe_target_status=NO_VALIDATED_TARGET`" in map_text
    assert "`local_mac_criteria_revision_status=NOT_SUPPORTED`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`all_symbols_d11_countable=true`" in map_text
    assert "`all_symbols_freshness_classification=clean`" in map_text
    assert "`endpoint_scope=LOCAL_MAC_ONLY`" in map_text
    assert "`vps_127_0_0_1_7497_validated=false`" in map_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a proven TWS issue" in map_text
    assert "`18789` and `18791` are not approved market-data endpoints" in map_text
    assert (
        "`D11.61_SOURCE_CONTROLLED_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE`"
        in map_text
    )
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_61_vps_endpoint_or_criteria_revision_prerequisite_dual_path() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_vps_endpoint_evidence_or_criteria_revision_prerequisite.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.61 IBKR VPS Endpoint Evidence Or Criteria Revision Prerequisite"
        in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE`"
        in packet_text
    )
    assert (
        "`source_commit` | `fd2258ee6efaff23886914b519b971b2f58c15c9`"
        in packet_text
    )
    assert "`d11_60_vps_validation` | `80 passed in 2.54s`" in packet_text
    assert (
        "`d11_60_decision` | "
        "`BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`" in packet_text
    )
    assert "`d11_59_route` | `REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`" in packet_text
    assert "`d11_58_result` | `BLOCKED_CRITERIA_UNRESOLVED`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`mac_local_historical_diagnostic_evidence` | `ACCEPTED`" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`endpoint_scope` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`vps_127_0_0_1_7497_validated` | `false`" in packet_text
    assert (
        "`prior_vps_failure` | "
        "`VPS_LOCALHOST_CONTEXT_MISMATCH / "
        "AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert "`vps_endpoint_evidence_prerequisite` | `REQUIRED`" in packet_text
    assert "`local_mac_criteria_revision_prerequisite` | `REQUIRED`" in packet_text
    assert "`d11_61_decision` | `DUAL_PREREQUISITE_REQUIRED`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`D11.62_SOURCE_CONTROLLED_PREREQUISITE_PATH_SELECTION_FOR_VPS_ENDPOINT_EVIDENCE_OR_LOCAL_MAC_CRITERIA_REVISION`"
        in packet_text
    )
    assert (
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility"
        in packet_text
    )
    assert "D11.57 accepted Mac-local historical diagnostic evidence" in packet_text
    assert "All five symbols were clean and countable" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "no validated VPS-accessible IBKR market-data endpoint" in packet_text
    assert "VPS `127.0.0.1:7497` was not listening" in packet_text
    assert "`18789` and `18791` are not approved IBKR market-data endpoints" in (
        packet_text
    )
    assert "no source-controlled proof that a VPS process can safely reach" in (
        packet_text
    )
    assert "`127.0.0.1` is process-context local" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "not a proven IB Gateway\n  issue" in packet_text
    assert (
        "No future VPS proof may target `127.0.0.1:7497` unless that endpoint is\n"
        "  observed listening in the VPS process context and separately authorized"
        in packet_text
    )
    assert "No future proof may target `18789` or `18791`" in packet_text
    assert "source-controlled authorization gate before any endpoint inspection" in (
        packet_text
    )
    assert "no service, timer, runtime, systemd, TWS, Gateway" in packet_text
    assert "no market-data request" in packet_text
    assert "no broker connection" in packet_text
    assert "no protocol probe" in packet_text
    assert "compact output only" in packet_text
    assert "evidence must identify process context" in packet_text
    assert "evidence must identify listening endpoints" in packet_text
    assert "evidence must identify process names" in packet_text
    assert "approved or only observed" in packet_text
    assert "identify the superseded rule exactly" in packet_text
    assert "`LOCAL_MAC_ONLY` market-data architecture is intended" in packet_text
    assert "prove no account/order/execution authority expansion" in packet_text
    assert "preserve `UNIT_12_BLOCKED` unless" in packet_text
    assert "add focused boundary tests before any approval" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "records no package capture, replay, scoring, candidate generation" in (
        packet_text
    )
    assert "Unit 12 opening" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in packet_text

    assert (
        "### D11.61 VPS Endpoint Evidence Or Criteria Revision Prerequisite"
        in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE`"
        in map_text
    )
    assert "`source_commit=fd2258ee6efaff23886914b519b971b2f58c15c9`" in map_text
    assert "`80 passed in 2.54s`" in map_text
    assert (
        "`d11_60_decision=BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`"
        in map_text
    )
    assert "`d11_59_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`" in map_text
    assert "`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`" in map_text
    assert "`d11_61_decision=DUAL_PREREQUISITE_REQUIRED`" in map_text
    assert "`vps_endpoint_evidence_prerequisite=REQUIRED`" in map_text
    assert "`local_mac_criteria_revision_prerequisite=REQUIRED`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`all_symbols_d11_countable=true`" in map_text
    assert "`all_symbols_freshness_classification=clean`" in map_text
    assert "`endpoint_scope=LOCAL_MAC_ONLY`" in map_text
    assert "does\nnot validate VPS `127.0.0.1:7497`" in map_text
    assert "no validated VPS-accessible IBKR\nmarket-data endpoint" in map_text
    assert "`18789` and `18791` are not approved IBKR market-data endpoints" in (
        map_text
    )
    assert "no explicit\nsource-controlled rule yet states" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a\nproven TWS issue or proven IB Gateway issue" in map_text
    assert "non-mutating only" in map_text
    assert "no market-data request" in map_text
    assert "no broker connection" in map_text
    assert "no protocol probe" in map_text
    assert "identifying process context, listening endpoints, process names" in map_text
    assert "identifying the superseded rule" in map_text
    assert (
        "`D11.62_SOURCE_CONTROLLED_PREREQUISITE_PATH_SELECTION_FOR_VPS_ENDPOINT_EVIDENCE_OR_LOCAL_MAC_CRITERIA_REVISION`"
        in map_text
    )
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_62_prerequisite_path_selection_selects_local_mac_revision() -> None:
    packet_path = Path("docs/ibkr_market_data_d11_62_prerequisite_path_selection.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.62 IBKR Prerequisite Path Selection" in packet_text
    assert (
        "`classification` | `IBKR_D11_PREREQUISITE_PATH_SELECTION`"
        in packet_text
    )
    assert (
        "`source_commit` | `eb54ef6d8affb13ec8f6909208b0a8c1de729bde`"
        in packet_text
    )
    assert "`d11_61_vps_validation` | `81 passed in 3.42s`" in packet_text
    assert "`d11_61_decision` | `DUAL_PREREQUISITE_REQUIRED`" in packet_text
    assert (
        "`d11_60_decision` | "
        "`BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`" in packet_text
    )
    assert "`d11_59_route` | `REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`" in packet_text
    assert "`d11_58_result` | `BLOCKED_CRITERIA_UNRESOLVED`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`mac_local_historical_diagnostic_evidence` | `ACCEPTED`" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`endpoint_scope` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`vps_127_0_0_1_7497_validated` | `false`" in packet_text
    assert (
        "`prior_vps_failure` | "
        "`VPS_LOCALHOST_CONTEXT_MISMATCH / "
        "AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert "`vps_endpoint_evidence_path` | `NOT_SELECTED`" in packet_text
    assert "`local_mac_criteria_revision_path` | `SELECTED`" in packet_text
    assert (
        "`d11_62_decision` | "
        "`LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION`"
        in packet_text
    )
    assert (
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility"
        in packet_text
    )
    assert "all five symbols were clean/countable" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "no validated VPS-accessible IBKR market-data endpoint" in packet_text
    assert "VPS `127.0.0.1:7497` was not listening" in packet_text
    assert "`18789` and `18791` are not approved IBKR market-data endpoints" in (
        packet_text
    )
    assert "`127.0.0.1` is process-context local" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "not a proven IB Gateway\n  issue" in packet_text
    assert (
        "No future VPS proof may target `127.0.0.1:7497` unless that endpoint is\n"
        "  observed listening in the VPS process context and separately authorized"
        in packet_text
    )
    assert "No future proof may target `18789` or `18791`" in packet_text
    assert "Path A, VPS endpoint evidence, is not selected" in packet_text
    assert "Path B, LOCAL_MAC criteria revision, is selected" in packet_text
    assert "Path C, blocked/no path selected, is not selected" in packet_text
    assert "without broker traffic, runtime mutation, account/order/execution" in (
        packet_text
    )
    assert "D11.63 must evaluate whether `LOCAL_MAC_ONLY` accepted" in packet_text
    assert "must not run broker traffic, endpoint inspection" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "records no package capture, replay, scoring, candidate generation" in (
        packet_text
    )
    assert "Unit 12 opening" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in packet_text

    assert "### D11.62 IBKR Prerequisite Path Selection" in map_text
    assert str(packet_path) in map_text
    assert "`IBKR_D11_PREREQUISITE_PATH_SELECTION`" in map_text
    assert "`source_commit=eb54ef6d8affb13ec8f6909208b0a8c1de729bde`" in map_text
    assert "`81 passed in 3.42s`" in map_text
    assert "`d11_61_decision=DUAL_PREREQUISITE_REQUIRED`" in map_text
    assert (
        "`d11_60_decision=BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`"
        in map_text
    )
    assert "`d11_59_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`" in map_text
    assert "`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`" in map_text
    assert "`d11_62_decision=LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED`" in map_text
    assert "`vps_endpoint_evidence_path=NOT_SELECTED`" in map_text
    assert "`local_mac_criteria_revision_path=SELECTED`" in map_text
    assert (
        "`D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION`"
        in map_text
    )
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`all_symbols_d11_countable=true`" in map_text
    assert "`all_symbols_freshness_classification=clean`" in map_text
    assert "`endpoint_scope=LOCAL_MAC_ONLY`" in map_text
    assert "`vps_127_0_0_1_7497_validated=false`" in map_text
    assert "no validated\nVPS-accessible IBKR market-data endpoint" in map_text
    assert "`18789` and `18791` are not\napproved IBKR market-data endpoints" in (
        map_text
    )
    assert "`127.0.0.1` is process-context local" in map_text
    assert "LOCAL_MAC\n`127.0.0.1:7497` is not equivalent to VPS" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a proven TWS issue or\nproven IB Gateway issue" in map_text
    assert "No future VPS proof may target `127.0.0.1:7497`" in map_text
    assert "No future proof may target `18789` or `18791`" in map_text
    assert (
        "evaluates whether\n`LOCAL_MAC_ONLY` accepted historical diagnostic evidence"
        in map_text
    )
    assert "must not run broker traffic, endpoint inspection" in map_text
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_63_formal_local_mac_criteria_revision_fails_closed() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_63_formal_local_mac_only_criteria_revision.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.63 Formal LOCAL_MAC-Only IBKR Criteria Revision" in packet_text
    assert (
        "`classification` | "
        "`IBKR_D11_LOCAL_MAC_ONLY_CRITERIA_REVISION_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `94fdbbe93ff4b9d4b46018a3a9cef211dd142049`"
        in packet_text
    )
    assert (
        "`d11_62_decision` | `LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED`"
        in packet_text
    )
    assert (
        "`d11_62_next_gate` | "
        "`D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION`"
        in packet_text
    )
    assert "`criteria_revision_result` | `NOT_APPROVED`" in packet_text
    assert (
        "`d11_63_decision` | "
        "`BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`" in packet_text
    )
    assert "`primary_eligibility_revision` | `NOT_REVISED`" in packet_text
    assert "`separate_vps_proof_rule_revision` | `NOT_REVISED`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`mac_local_historical_diagnostic_evidence` | `ACCEPTED`" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`selected_endpoint_context` | `LOCAL_MAC`" in packet_text
    assert "`selected_endpoint_type` | `TWS_PAPER`" in packet_text
    assert "`selected_mac_local_endpoint` | `127.0.0.1:7497`" in packet_text
    assert "`endpoint_scope` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`vps_127_0_0_1_7497_validated` | `false`" in packet_text
    assert (
        "`prior_vps_failure` | "
        "`VPS_LOCALHOST_CONTEXT_MISMATCH / "
        "AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.64_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN`"
        in packet_text
    )
    assert (
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility"
        in packet_text
    )
    assert "`d11_primary_candidate_status=candidate`" in packet_text
    assert "`d11_primary_eligible=false`" in packet_text
    assert "`broker_coupled=true`" in packet_text
    assert "Historical data availability evidence" in packet_text
    assert "Endpoint locality evidence" in packet_text
    assert "Provider primary eligibility" in packet_text
    assert "Runtime deployment eligibility" in packet_text
    assert "Broker submit readiness" in packet_text
    assert "Live trading readiness" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "does not validate\nruntime deployment" in packet_text
    assert "does not approve provider primary eligibility" in packet_text
    assert "does not\nprove broker submit readiness" in packet_text
    assert "does not prove live trading readiness" in packet_text
    assert "D11.63 does not revise" in packet_text
    assert "approving primary eligibility\nwould require a production" in packet_text
    assert "`127.0.0.1` is process-context local" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not\nequivalent to VPS" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "not a proven TWS issue" in packet_text
    assert "not a proven IB Gateway issue" in packet_text
    assert "`18789` and `18791` remain not approved market-data endpoints" in (
        packet_text
    )
    assert "preserves separation between LOCAL_MAC evidence and VPS production" in (
        packet_text
    )
    assert "Process defect avoided" in packet_text
    assert "does not infer approval from the LOCAL_MAC lane" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "no broker/TWS/API/runtime/network/service/scheduler/systemd" in (
        packet_text
    )
    assert "no submit, cancel, flatten, sell, cleanup" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12_BLOCKED`" in packet_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in packet_text
    assert "`VPS_RUNTIME=NOT_TOUCHED`" in packet_text

    assert "### D11.63 Formal LOCAL_MAC-Only IBKR Criteria Revision" in map_text
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_LOCAL_MAC_ONLY_CRITERIA_REVISION_ADJUDICATION`" in map_text
    )
    assert "`source_commit=94fdbbe93ff4b9d4b46018a3a9cef211dd142049`" in (
        map_text
    )
    assert "`d11_62_decision=LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED`" in (
        map_text
    )
    assert (
        "`d11_63_decision=BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`"
        in map_text
    )
    assert "`criteria_revision_result=NOT_APPROVED`" in map_text
    assert "`primary_eligibility_revision=NOT_REVISED`" in map_text
    assert "`separate_vps_proof_rule_revision=NOT_REVISED`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`all_symbols_d11_countable=true`" in map_text
    assert "`all_symbols_freshness_classification=clean`" in map_text
    assert "`endpoint_scope=LOCAL_MAC_ONLY`" in map_text
    assert "historical data availability evidence from endpoint\nlocality" in (
        map_text
    )
    assert "broker submit readiness, and live trading readiness" in map_text
    assert (
        "`candidate_can_count_for_d11`, and `ibkr_market_data_candidate` remains"
        in map_text
    )
    assert "`d11_primary_candidate_status=candidate`" in map_text
    assert "`d11_primary_eligible=false`" in map_text
    assert "`broker_coupled=true`" in map_text
    assert "`127.0.0.1` is process-context local" in map_text
    assert "LOCAL_MAC\n`127.0.0.1:7497` is not equivalent to VPS" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "not a proven TWS issue or\nproven IB Gateway issue" in map_text
    assert "`18789` and `18791` remain not approved market-data" in map_text
    assert "preserves separation between LOCAL_MAC evidence and VPS production" in (
        map_text
    )
    assert (
        "`D11.64_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN`"
        in map_text
    )
    assert "must not\nimply broker/TWS/API/runtime/network/service" in map_text
    assert "broker submit readiness, or live trading readiness" in map_text
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_23_preflight_packet_is_control_prep_only_without_authority() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_repeatability_run_1_preflight_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    ledger_text = Path(
        "docs/ibkr_market_data_repeatability_ledger_template.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.23 IBKR Repeatability Run 1 Preflight Packet" in packet_text
    assert "Control Prep Only" in packet_text
    assert "not the live diagnostic run" in packet_text
    assert "not authorization to run immediately" in packet_text
    assert "not authorization to run outside a valid U.S. regular-session window" in (
        packet_text
    )
    assert "future run is `LOCAL_MAC` only" in packet_text
    assert "TWS/Gateway must be opened manually" in packet_text
    assert "VPS runtime remains parked" in packet_text
    assert "`openclaw.timer` and `openclaw.service` remain off" in packet_text
    assert "AAPL" in packet_text
    assert "MSFT" in packet_text
    assert "NVDA" in packet_text
    assert "TSLA" in packet_text
    assert "MSTR" in packet_text
    assert "Target timeframe: 15Min" in packet_text
    assert "`requirements-diagnostics.txt`" in packet_text
    assert "`ib_insync==0.9.86`" in packet_text
    assert "`completed_repeatability_runs` | `0`" in packet_text
    assert "`invalidated_repeatability_runs` | `0`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`order_authority` | `NONE`" in packet_text
    assert "`execution_authority` | `NONE`" in packet_text
    assert "`vps_runtime` | `PARKED`" in packet_text
    assert "Required Paste-Back Fields" in packet_text
    assert "D11.24 ledger recording review" in packet_text
    assert "invalidated evidence review" in packet_text
    assert "do not rerun by impulse" in packet_text
    assert "account, position, margin, buying power, portfolio" in packet_text
    assert "does not record repeatability run 1 as completed" in packet_text
    assert "does not mutate the D11.22 ledger counts" in packet_text

    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert str(packet_path) in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`ORDER_AUTHORITY=NONE`" in map_text
    assert "`EXECUTION_AUTHORITY=NONE`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_24_adjudication_packet_is_review_prep_only_without_authority() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_repeatability_run_1_adjudication_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    ledger_text = Path(
        "docs/ibkr_market_data_repeatability_ledger_template.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.24 IBKR Repeatability Run 1 Adjudication Packet" in packet_text
    assert "Control Prep Only" in packet_text
    assert "not the diagnostic run" in packet_text
    assert "not evidence recording" in packet_text
    assert "not authorization to mutate ledger counts" in packet_text
    assert "`completed_repeatability_runs` | `0`" in packet_text
    assert "`invalidated_repeatability_runs` | `0`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`order_authority` | `NONE`" in packet_text
    assert "`execution_authority` | `NONE`" in packet_text
    assert "`vps_runtime` | `PARKED`" in packet_text
    assert "Acceptance Criteria For Ledger-Recording Review" in packet_text
    assert "local timestamp UTC is present" in packet_text
    assert "HEAD equals the expected source commit" in packet_text
    assert "command used is present and matches the D11.23 source-controlled command" in (
        packet_text
    )
    assert "`result_type` is `ibkr_local_read_only_market_data_smoke`" in packet_text
    assert "target symbols all present: AAPL, MSFT, NVDA, TSLA, MSTR" in packet_text
    assert "timeframe is `15Min`" in packet_text
    assert "`connection_mode` is `local_read_only_smoke`" in packet_text
    assert "`read_only=true`" in packet_text
    assert '`freshness_classification="clean"` for every symbol' in packet_text
    assert "`d11_countable=true` for every symbol" in packet_text
    assert '`d11_primary_candidate_status="candidate"`' in packet_text
    assert "`d11_primary_eligible=false`" in packet_text
    assert "`failure_reason` is empty for every symbol" in packet_text
    assert "no warnings are present" in packet_text
    assert "`broker_api_authority=false`" in packet_text
    assert "`order_authority=false`" in packet_text
    assert "`execution_authority=false`" in packet_text
    assert "`d11_completion_authority=false`" in packet_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in packet_text
    assert "`authority_boundary` is present" in packet_text
    assert "ACCEPT_FOR_D11_24_LEDGER_RECORDING_REVIEW" in packet_text
    assert "INVALIDATED_EVIDENCE_REVIEW_REQUIRED" in packet_text
    assert "BLOCKED_FOR_SOURCE_CONTROL_OR_AUTHORITY_DEFECT" in packet_text
    assert "Do not rerun by impulse" in packet_text
    assert "account, position, margin, buying power, portfolio" in packet_text
    assert "does not record repeatability run 1 as completed" in packet_text
    assert "does not record repeatability run 1 as invalidated" in packet_text
    assert "does not mutate the D11.22 ledger counts" in packet_text

    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert str(packet_path) in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`ORDER_AUTHORITY=NONE`" in map_text
    assert "`EXECUTION_AUTHORITY=NONE`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text


def test_d11_27_run_2_preflight_packet_is_control_prep_only_without_authority() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_repeatability_run_2_preflight_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    ledger_text = Path(
        "docs/ibkr_market_data_repeatability_ledger_template.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.27 IBKR Repeatability Run 2 Preflight Packet" in packet_text
    assert "Control Prep Only" in packet_text
    assert "not the live diagnostic run" in packet_text
    assert "not authorization to run today" in packet_text
    assert "distinct U.S. regular-session trading day after Run #1" in packet_text
    assert "future run is `LOCAL_MAC` only" in packet_text
    assert "TWS/Gateway must be opened manually" in packet_text
    assert "VPS runtime remains parked" in packet_text
    assert "`openclaw.timer` and `openclaw.service` remain off" in packet_text
    assert "Run #3 remains future and pending" in packet_text
    assert "`completed_repeatability_runs` | `1`" in packet_text
    assert "`invalidated_repeatability_runs` | `0`" in packet_text
    assert "`completed_run_1_only` | `true`" in packet_text
    assert "`run_2_completed` | `false`" in packet_text
    assert "`run_2_invalidated` | `false`" in packet_text
    assert "`ibkr_provider_status` | `ibkr_market_data_candidate`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`order_authority` | `NONE`" in packet_text
    assert "`execution_authority` | `NONE`" in packet_text
    assert "`vps_runtime` | `PARKED`" in packet_text
    assert "EXPECTED_SOURCE_COMMIT" in packet_text
    assert "future Run #2 authorization must supply the exact" in packet_text
    assert "this packet does not supply live-run commit" in packet_text
    assert "HEAD must equal that authorization-supplied" in packet_text
    assert "02339cba3239b9148ca352e2970cb658bdacc58a" in packet_text
    assert "historical context only, not the" in packet_text
    assert "expected source commit for a future Run #2" in packet_text
    assert "AAPL" in packet_text
    assert "MSFT" in packet_text
    assert "NVDA" in packet_text
    assert "TSLA" in packet_text
    assert "MSTR" in packet_text
    assert "Target timeframe: 15Min" in packet_text
    assert "`requirements-diagnostics.txt`" in packet_text
    assert "`ib_insync==0.9.86`" in packet_text
    assert "<UTC_REQUESTED_END_FOR_DISTINCT_RUN_2_DAY>" in packet_text
    assert "--symbol AAPL" in packet_text
    assert "--symbol MSFT" in packet_text
    assert "--symbol NVDA" in packet_text
    assert "--symbol TSLA" in packet_text
    assert "--symbol MSTR" in packet_text
    assert "Required Paste-Back Fields" in packet_text
    assert "timestamp UTC" in packet_text
    assert "expected source commit" in packet_text
    assert "worktree before" in packet_text
    assert "worktree after" in packet_text
    assert "observed dependency version" in packet_text
    assert "authority_boundary" in packet_text
    assert "confirmation that VPS runtime was not touched" in packet_text
    assert "confirmation that timer and service remained off" in packet_text
    assert "Future LOCAL_MAC-Only Operator Paste-Back Wrapper" in packet_text
    assert "Run it in the intended" in packet_text
    assert "`LOCAL_MAC` terminal only; do not copy it to a VPS terminal" in (
        packet_text
    )
    assert "automation host. It uses no heredoc" in packet_text
    assert "timestamp_utc=" in packet_text
    assert "expected_source_commit=" in packet_text
    assert "branch=" in packet_text
    assert "head=" in packet_text
    assert "worktree_before=CLEAN" in packet_text
    assert "dependency_contract=requirements-diagnostics.txt / ib_insync==0.9.86" in packet_text
    assert "observed_dependency_version=" in packet_text
    assert "command_used=" in packet_text
    assert "diagnostic_command=BEGIN" in packet_text
    assert "worktree_after=CLEAN" in packet_text
    assert "no_rerun_confirmation=true" in packet_text
    assert "vps_runtime_timer_service_not_touched_confirmation=true" in packet_text
    assert "package_capture=BLOCKED" in packet_text
    assert "unit_12_status=UNIT_12_BLOCKED" in packet_text
    assert "stale, recency-caveated, quarantined, missing, malformed" in packet_text
    assert "any warning" in packet_text
    assert "any missing target symbol" in packet_text
    assert "wrong branch or wrong head" in packet_text
    assert "dirty worktree" in packet_text
    assert "missing explicit request window" in packet_text
    assert "dependency mismatch" in packet_text
    assert "account, position, margin, buying power, portfolio, order, balance" in (
        packet_text
    )
    assert "package capture, replay, scoring, candidate generation" in packet_text
    assert "not a rerun-by-impulse" in packet_text
    assert "future Run #2 adjudication/ledger review" in packet_text
    assert "invalidated evidence review" in packet_text
    assert "Run #2 acceptance still does not approve IBKR as primary" in packet_text
    assert "does not complete D11" in packet_text
    assert "does not open Unit 12" in packet_text
    assert "does not authorize runtime" in packet_text
    assert "does not record repeatability Run #2 as completed" in packet_text
    assert "does not record repeatability Run #2 as invalidated" in packet_text
    assert "does not mutate the D11.26 ledger completed or invalidated counts" in (
        packet_text
    )

    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert "| 1 | 2026-06-22 |" in ledger_text
    assert "| 2 | 2026-06-23 |" in ledger_text
    assert "| _none_ | _none_ | _none_ | _none_ | _none_ |" in ledger_text

    assert str(packet_path) in map_text
    assert "D11.27 IBKR Repeatability Run 2 Preflight Packet" in map_text
    assert "not authorization to run today" in map_text
    assert "distinct regular-session trading day after Run #1" in map_text
    assert "`completed_repeatability_runs=2`" in map_text
    assert "`invalidated_repeatability_runs=0`" in map_text
    assert "Run #1 remains recorded for 2026-06-22" in map_text
    assert "Run #3 remains future and pending" in map_text
    assert "Run #3 remains future and pending" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`ORDER_AUTHORITY=NONE`" in map_text
    assert "`EXECUTION_AUTHORITY=NONE`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text
    assert "future authorization to supply the expected source commit" in map_text
    assert "historical packet-creation" in map_text
    assert "no-heredoc operator wrapper" in map_text


def test_d11_28_run_2_adjudication_packet_is_review_prep_only_without_authority() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_repeatability_run_2_adjudication_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    ledger_text = Path(
        "docs/ibkr_market_data_repeatability_ledger_template.md"
    ).read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.28 IBKR Repeatability Run 2 Adjudication Packet" in packet_text
    assert "Control Prep Only" in packet_text
    assert "not the diagnostic run" in packet_text
    assert "not evidence recording" in packet_text
    assert "not authorization to mutate ledger counts" in packet_text
    assert "separately authorized and executed on a distinct U.S." in packet_text
    assert "regular-session trading day after Run #1" in packet_text
    assert "No completed or invalidated repeatability evidence is recorded" in (
        packet_text
    )
    assert "Run #3 remains future and pending" in packet_text
    assert "`completed_repeatability_runs` | `1`" in packet_text
    assert "`invalidated_repeatability_runs` | `0`" in packet_text
    assert "`completed_run_1_only` | `true`" in packet_text
    assert "`run_2_completed` | `false`" in packet_text
    assert "`run_2_invalidated` | `false`" in packet_text
    assert "`run_3_status` | `future_pending`" in packet_text
    assert "`ibkr_provider_status` | `ibkr_market_data_candidate`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`order_authority` | `NONE`" in packet_text
    assert "`execution_authority` | `NONE`" in packet_text
    assert "`vps_runtime` | `PARKED`" in packet_text
    assert "docs/ibkr_market_data_repeatability_run_2_preflight_packet.md" in (
        packet_text
    )
    assert "No reviewer may infer missing evidence from memory" in packet_text
    assert "terminal scrollback" in packet_text
    assert "screenshots" in packet_text
    assert "broker state" in packet_text
    assert "operator confidence" in packet_text
    assert "Acceptance Criteria For Run #2 Ledger-Recording Review" in packet_text
    assert "exact expected source commit from the future Run #2 authorization" in (
        packet_text
    )
    assert "local timestamp UTC is present" in packet_text
    assert "branch is `main`" in packet_text
    assert "HEAD equals the expected source commit" in packet_text
    assert "worktree was clean before and after the run" in packet_text
    assert "`requirements-diagnostics.txt`" in packet_text
    assert "`ib_insync==0.9.86`" in packet_text
    assert "matches the Run #2 source-controlled command" in packet_text
    assert "explicit `requested_start` and `requested_end` are present" in (
        packet_text
    )
    assert "`result_type` is `ibkr_local_read_only_market_data_smoke`" in packet_text
    assert "target symbols all present: AAPL, MSFT, NVDA, TSLA, MSTR" in packet_text
    assert "timeframe is `15Min`" in packet_text
    assert "`provider_key` and `provider_name` are present" in packet_text
    assert "`connection_mode` is `local_read_only_smoke`" in packet_text
    assert "`read_only=true`" in packet_text
    assert "`latest_candle_timestamp` is valid timezone-aware UTC" in packet_text
    assert "`freshness_classification=clean` for every symbol" in packet_text
    assert "`d11_countable=true` for every symbol" in packet_text
    assert "`d11_primary_candidate_status=candidate`" in packet_text
    assert "`d11_primary_eligible=false`" in packet_text
    assert "`failure_reason` is empty for every symbol" in packet_text
    assert "no warnings are present" in packet_text
    assert "`package_capture=false`" in packet_text
    assert "`replay=false`" in packet_text
    assert "`scoring=false`" in packet_text
    assert "`candidate_generation=false`" in packet_text
    assert "`broker_api_authority=false`" in packet_text
    assert "`order_authority=false`" in packet_text
    assert "`execution_authority=false`" in packet_text
    assert "`d11_completion_authority=false`" in packet_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in packet_text
    assert "`authority_boundary` is present" in packet_text
    assert "no account, position, margin, buying power, portfolio, order, balance" in (
        packet_text
    )
    assert "VPS runtime was not touched" in packet_text
    assert "timer and service remained off" in packet_text
    assert "Invalidation Criteria" in packet_text
    assert "stale, recency-caveated, quarantined, missing, malformed" in packet_text
    assert "any warning" in packet_text
    assert "any missing target symbol" in packet_text
    assert "wrong branch or wrong head" in packet_text
    assert "dirty worktree before or after the run" in packet_text
    assert "missing explicit request window" in packet_text
    assert "dependency mismatch" in packet_text
    assert "non-distinct trading day relative to Run #1" in packet_text
    assert "package capture, replay, scoring, candidate generation" in packet_text
    assert "Blocked Review Criteria" in packet_text
    assert "ambiguous, missing, internally contradictory" in packet_text
    assert "outside the Run #2 authorization scope" in packet_text
    assert "ACCEPT_FOR_D11_28_RUN_2_LEDGER_RECORDING_REVIEW" in packet_text
    assert "INVALIDATED_RUN_2_EVIDENCE_REVIEW_REQUIRED" in packet_text
    assert "BLOCKED_FOR_RUN_2_SOURCE_CONTROL_OR_AUTHORITY_DEFECT" in packet_text
    assert "Acceptance still does not approve IBKR as primary" in packet_text
    assert "does not complete D11" in packet_text
    assert "does not open Unit 12" in packet_text
    assert "does not authorize runtime" in packet_text
    assert "Do not rerun by impulse" in packet_text
    assert "does not record repeatability Run #2 as completed" in packet_text
    assert "does not record repeatability Run #2 as invalidated" in packet_text
    assert "does not mutate the D11.26 ledger completed or invalidated counts" in (
        packet_text
    )

    assert "`completed_repeatability_runs` | `3`" in ledger_text
    assert "`invalidated_repeatability_runs` | `0`" in ledger_text
    assert "| 1 | 2026-06-22 |" in ledger_text
    assert "| 2 | 2026-06-23 |" in ledger_text
    assert "| _none_ | _none_ | _none_ | _none_ | _none_ |" in ledger_text

    assert str(packet_path) in map_text
    assert "D11.28 IBKR Repeatability Run 2 Adjudication Packet" in map_text
    assert "not the diagnostic run" in map_text
    assert "not evidence recording" in map_text
    assert "not authorization to mutate ledger counts" in map_text
    assert "ACCEPT_FOR_D11_28_RUN_2_LEDGER_RECORDING_REVIEW" in map_text
    assert "INVALIDATED_RUN_2_EVIDENCE_REVIEW_REQUIRED" in map_text
    assert "BLOCKED_FOR_RUN_2_SOURCE_CONTROL_OR_AUTHORITY_DEFECT" in map_text
    assert "`completed_repeatability_runs=2`" in map_text
    assert "`invalidated_repeatability_runs=0`" in map_text
    assert "Run #1 remains recorded for 2026-06-22" in map_text
    assert "Run #3 remains future and pending" in map_text
    assert "Run #3 remains future and pending" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12_BLOCKED`" in map_text
    assert "`PACKAGE_CAPTURE=BLOCKED`" in map_text
    assert "`ORDER_AUTHORITY=NONE`" in map_text
    assert "`EXECUTION_AUTHORITY=NONE`" in map_text
    assert "`VPS_RUNTIME=PARKED`" in map_text
    assert "Do not rerun by impulse" in map_text


def test_ibkr_read_only_smoke_cli_requires_authorization_flag(capsys) -> None:
    from tools.ops.ibkr_market_data_read_only_smoke import main

    exit_code = main(
        [
            "--symbol",
            "mstr",
            "--timeframe",
            "15Min",
            "--limit",
            "5",
            "--requested-end",
            "2026-06-17T13:45:00Z",
            "--lookback-minutes",
            "120",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"connection_mode": "not_opened"' in captured.out
    assert '"freshness_classification": "unavailable"' in captured.out
    assert '"d11_countable": false' in captured.out
    assert '"d11_primary_eligible": false' in captured.out


def test_ibkr_read_only_smoke_module_boundary_and_authority() -> None:
    import tools.ops.ibkr_market_data_read_only_smoke as smoke

    source = Path(smoke.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "requests",
        "urllib",
        "subprocess",
        "systemctl",
        "import socket",
        "from socket",
        "os.getenv",
        "load_dotenv",
        "keychain",
        "secret",
        "placeOrder",
        "cancelOrder",
        "reqPositions",
        "accountSummary",
        "reqAccount",
        "reqPnL",
        "reqOpenOrders",
    ):
        assert forbidden not in source
    assert "import ib_insync" in source
    assert "no_credentials_read" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_account_query" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_position_query" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_margin_query" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_buying_power_query" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_portfolio_query" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_order_placement" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_order_modification" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_order_cancellation" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_order_routing" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_execution_authority" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_package_capture" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_replay" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_scoring" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_candidate_generation" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_d11_completion" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY
    assert "no_unit_12_opening" in IBKR_READ_ONLY_SMOKE_AUTHORITY_BOUNDARY


def test_metadata_only_modules_still_have_no_ibkr_client_imports() -> None:
    import ibkr_market_data_diagnostic_contract
    import ibkr_read_only_implementation_design

    for module in (
        ibkr_market_data_diagnostic_contract,
        ibkr_read_only_implementation_design,
    ):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "import ibapi" not in source
        assert "from ibapi" not in source
        assert "import ib_insync" not in source
        assert "from ib_insync" not in source
        assert "import socket" not in source
        assert "from socket" not in source
        assert "requests" not in source
        assert "urllib" not in source
