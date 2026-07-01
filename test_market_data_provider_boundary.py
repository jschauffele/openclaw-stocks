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


def test_d11_64_primary_eligibility_blocker_resolution_plan_fails_closed() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_64_primary_eligibility_blocker_resolution_plan.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.64 IBKR Primary Eligibility Blocker Resolution Plan" in packet_text
    assert (
        "`classification` | "
        "`IBKR_D11_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN`" in packet_text
    )
    assert (
        "`source_commit` | `ac78409fa0c81c97f2a357671cbc55fd55988f4b`"
        in packet_text
    )
    assert (
        "`d11_63_decision` | "
        "`BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`" in packet_text
    )
    assert "`criteria_revision_result` | `NOT_APPROVED`" in packet_text
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
        "`d11_64_decision` | "
        "`BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.65_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`"
        in packet_text
    )
    assert "exact blockers before IBKR primary eligibility can be" in packet_text
    assert "separate_vps_read_only_freshness_proof_required_before_primary_eligibility" in (
        packet_text
    )
    assert "`ibkr_market_data_candidate` is not `approved_primary`" in packet_text
    assert "`ibkr_market_data_candidate` remains `d11_primary_eligible=false`" in (
        packet_text
    )
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        packet_text
    )
    assert "LOCAL_MAC historical evidence does not validate VPS production/runtime" in (
        packet_text
    )
    assert "does not establish broker submit readiness" in packet_text
    assert "does not establish live trading readiness" in packet_text
    assert "Historical data availability evidence" in packet_text
    assert "Endpoint locality evidence" in packet_text
    assert "Broker-coupling evidence" in packet_text
    assert "Provider primary-eligibility evidence" in packet_text
    assert "VPS production/runtime eligibility evidence" in packet_text
    assert "Broker submit readiness evidence" in packet_text
    assert "Live trading readiness evidence" in packet_text
    assert "Governance/documentation blockers" in packet_text
    assert "Future runtime, broker, VPS, or market-session evidence blockers" in (
        packet_text
    )
    assert "D11.64 does not perform those future evidence captures" in packet_text
    assert "does not create\ncommands for them" in packet_text
    assert "D11.65_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE" in (
        packet_text
    )
    assert "not runtime activation, broker activation, Unit 12 opening" in packet_text
    assert "D11.64 does not modify production provider-selection behavior" in (
        packet_text
    )
    assert "account_order_execution_authority=false" in packet_text
    assert "keeps closed broker/TWS/API/runtime/network/service/scheduler" in (
        packet_text
    )
    assert "broker submit readiness, live trading readiness, Unit\n12 opening" in (
        packet_text
    )
    assert "Process defect avoided" in packet_text

    assert "### D11.64 IBKR Primary Eligibility Blocker Resolution Plan" in map_text
    assert str(packet_path) in map_text
    assert "`IBKR_D11_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN`" in map_text
    assert "`source_commit=ac78409fa0c81c97f2a357671cbc55fd55988f4b`" in map_text
    assert (
        "`d11_63_decision=BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`"
        in map_text
    )
    assert "`d11_64_decision=BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED`" in (
        map_text
    )
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "`mac_local_historical_diagnostic_evidence=ACCEPTED`" in map_text
    assert "`all_symbols_d11_countable=true`" in map_text
    assert "`all_symbols_freshness_classification=clean`" in map_text
    assert "`endpoint_scope=LOCAL_MAC_ONLY`" in map_text
    assert "historical data availability governance mapping" in map_text
    assert "broker-coupling resolution" in map_text
    assert "broker submit readiness evidence" in map_text
    assert "live trading readiness evidence" in map_text
    assert "Governance blockers include" in map_text
    assert "Future evidence blockers include" in map_text
    assert "does not capture that evidence and does not create\ncommands" in map_text
    assert "`127.0.0.1` is process-context local" in map_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not\nequivalent to VPS" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "`18789` and `18791`\nremain not approved market-data endpoints" in map_text
    assert (
        "`D11.65_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`"
        in map_text
    )
    assert "not runtime activation, broker activation, Unit 12 opening" in map_text
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_65_primary_eligibility_evidence_requirements_prerequisite() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_65_primary_eligibility_evidence_requirements_prerequisite.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.65 IBKR Primary Eligibility Evidence Requirements Prerequisite"
        in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`"
        in packet_text
    )
    assert (
        "`source_commit` | `cee9f5237e2ff220d4230fabd1d905be90e79b9a`"
        in packet_text
    )
    assert (
        "`d11_64_decision` | "
        "`BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED`" in packet_text
    )
    assert (
        "`d11_63_decision` | "
        "`BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`" in packet_text
    )
    assert "`criteria_revision_result` | `NOT_APPROVED`" in packet_text
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
        "`d11_65_decision` | "
        "`EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED`"
        in packet_text
    )
    assert "`evidence_collected` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.66_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`"
        in packet_text
    )
    assert "It defines requirements only" in packet_text
    assert "It does not collect evidence" in packet_text
    assert "Evidence Requirements Table" in packet_text
    assert "Historical data availability evidence" in packet_text
    assert "Already satisfied by prior source-controlled evidence" in packet_text
    assert "Endpoint locality evidence" in packet_text
    assert "Source-controlled documentation/test requirement" in packet_text
    assert "VPS production/runtime reachability evidence" in packet_text
    assert "Future VPS evidence requirement" in packet_text
    assert "Broker-coupling evidence" in packet_text
    assert "Provider primary-eligibility evidence" in packet_text
    assert "`candidate_can_count_for_d11` evidence" in packet_text
    assert "Broker submit readiness evidence" in packet_text
    assert "Explicitly out of scope for D11 primary eligibility" in packet_text
    assert "Live trading readiness evidence" in packet_text
    assert "Unit 12 opening prerequisites" in packet_text
    assert "Blocker-to-Requirement Mapping" in packet_text
    assert "Already-Satisfied Evidence" in packet_text
    assert "Still-Missing Evidence" in packet_text
    assert "Fail-Closed Criteria" in packet_text
    assert "Disqualifiers" in packet_text
    assert "treating historical data availability as provider primary eligibility" in (
        packet_text
    )
    assert "treating LOCAL_MAC `127.0.0.1:7497` as VPS" in packet_text
    assert "treating `18789` or `18791` as approved market-data endpoints" in (
        packet_text
    )
    assert "modifying production provider-selection behavior inside this gate" in (
        packet_text
    )
    assert "collecting new runtime, broker, TWS, VPS" in packet_text
    assert "D11.66_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN" in (
        packet_text
    )
    assert "must not activate runtime, activate broker systems" in packet_text
    assert "must not run broker/TWS/API/runtime/network/service" not in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "runtime_broker_vps_scheduler_systemd_credential_action=false" in (
        packet_text
    )

    assert (
        "### D11.65 IBKR Primary Eligibility Evidence Requirements Prerequisite"
        in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`"
        in map_text
    )
    assert "`source_commit=cee9f5237e2ff220d4230fabd1d905be90e79b9a`" in (
        map_text
    )
    assert "`d11_64_decision=BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED`" in (
        map_text
    )
    assert (
        "`d11_65_decision=EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED`"
        in map_text
    )
    assert "`evidence_collected=false`" in map_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action=false`"
        in map_text
    )
    assert "`production_provider_selection_behavior_changed=false`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "`account_order_execution_authority=false`" in map_text
    assert "historical data availability evidence" in map_text
    assert "endpoint locality\nevidence" in map_text
    assert "VPS production/runtime reachability evidence" in map_text
    assert "broker-coupling\nevidence" in map_text
    assert "`candidate_can_count_for_d11`\nevidence" in map_text
    assert "broker submit readiness evidence" in map_text
    assert "live trading readiness evidence" in map_text
    assert "Unit 12 opening prerequisites" in map_text
    assert "already-satisfied evidence" in map_text
    assert "Still-missing evidence" in map_text or "still-missing evidence" in map_text
    assert "fail-closed disqualifiers" in map_text
    assert (
        "`D11.66_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`"
        in map_text
    )
    assert "must not activate runtime, activate broker systems" in map_text
    assert "create operational commands for broker, TWS" in map_text
    assert "grants no account, order, execution, package capture, replay" in map_text


def test_d11_66_read_only_evidence_authorization_plan_fails_closed() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_66_read_only_evidence_authorization_plan.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.66 IBKR Primary Eligibility Read-Only Evidence Authorization Plan"
        in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`"
        in packet_text
    )
    assert (
        "`source_commit` | `3e66732e4cfbcb454fb72d9036bcb1921c0b24b2`"
        in packet_text
    )
    assert (
        "`d11_65_classification` | "
        "`IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`"
        in packet_text
    )
    assert (
        "`d11_65_decision` | "
        "`EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED`"
        in packet_text
    )
    assert (
        "`d11_66_decision` | "
        "`READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED`"
        in packet_text
    )
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
    assert "`evidence_collected` | `false`" in packet_text
    assert (
        "`actual_read_only_evidence_capture_authorized` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`executable_evidence_capture_commands_created` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.67_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`"
        in packet_text
    )
    assert "defines authorization boundaries only" in packet_text
    assert "does not collect evidence" in packet_text
    assert "authorize actual read-only evidence capture" in packet_text
    assert "create executable evidence-capture commands" in packet_text
    assert "Authorization Plan Table" in packet_text
    assert "Future source-controlled documentation/test adjudication" in packet_text
    assert "Future LOCAL_MAC read-only evidence authorization" in packet_text
    assert "Future VPS read-only evidence authorization" in packet_text
    assert "Future broker/TWS read-only evidence authorization" in packet_text
    assert "Explicitly out of scope for D11 primary eligibility" in packet_text
    assert "D11.65 Requirement to Authorization Boundary Mapping" in packet_text
    assert "Already-Satisfied Evidence" in packet_text
    assert "Still-Missing Evidence" in packet_text
    assert "Future Evidence Categories" in packet_text
    assert "Authorization Preconditions" in packet_text
    assert "Authorization Disqualifiers" in packet_text
    assert "Boundary Separation" in packet_text
    assert "D11.66 does not satisfy these preconditions" in packet_text
    assert "includes executable commands in the authorization-plan gate" in (
        packet_text
    )
    assert "implies evidence collection before a separate preflight design gate" in (
        packet_text
    )
    assert "targets VPS `127.0.0.1:7497` without process-context-local" in (
        packet_text
    )
    assert "treats LOCAL_MAC `127.0.0.1:7497` as equivalent to VPS" in (
        packet_text
    )
    assert "treats `18789` or `18791` as approved market-data endpoints" in (
        packet_text
    )
    assert "permits account, order, execution" in packet_text
    assert "modifies production provider-selection behavior" in packet_text
    assert "read-only evidence authorization: a future source-controlled permission" in (
        packet_text
    )
    assert "evidence collection: not performed and not authorized by D11.66" in (
        packet_text
    )
    assert "evidence adjudication: a later source-controlled review" in packet_text
    assert "provider primary eligibility: remains `NOT_APPROVED`" in packet_text
    assert "runtime deployment eligibility: not established" in packet_text
    assert "broker submit readiness: not established and out of scope" in packet_text
    assert "live trading readiness: not established and out of scope" in packet_text
    assert "Unit 12 opening: not authorized and remains blocked" in packet_text
    assert "D11.67_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN" in (
        packet_text
    )
    assert "must not execute evidence capture" in packet_text
    assert "must not execute evidence capture, activate runtime" in packet_text
    assert "account_order_execution_authority=false" in packet_text
    assert "actual_read_only_evidence_capture_authorized=false" in packet_text
    assert "executable_evidence_capture_commands_created=false" in packet_text

    assert (
        "### D11.66 IBKR Primary Eligibility Read-Only Evidence Authorization Plan"
        in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`"
        in map_text
    )
    assert "`source_commit=3e66732e4cfbcb454fb72d9036bcb1921c0b24b2`" in (
        map_text
    )
    assert (
        "`d11_66_decision=READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED`"
        in map_text
    )
    assert "`evidence_collected=false`" in map_text
    assert "`actual_read_only_evidence_capture_authorized=false`" in map_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action=false`"
        in map_text
    )
    assert "`executable_evidence_capture_commands_created=false`" in map_text
    assert "`production_provider_selection_behavior_changed=false`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "future LOCAL_MAC read-only evidence authorization" in map_text
    assert "future VPS\nread-only evidence authorization" in map_text
    assert "future broker/TWS read-only evidence\nauthorization" in map_text
    assert "explicitly out of scope for D11 primary\neligibility" in map_text
    assert "already-satisfied evidence" in map_text
    assert "still-missing evidence" in map_text
    assert "authorization preconditions" in map_text
    assert "authorization disqualifiers" in map_text
    assert "executable commands in the\nauthorization-plan gate" in map_text
    assert "unsafe VPS localhost\ntargets" in map_text
    assert (
        "`D11.67_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`"
        in map_text
    )
    assert "must\nnot execute evidence capture" in map_text
    assert "actual read-only\nevidence capture" in map_text
    assert "IBKR primary\neligibility approval" in map_text


def test_d11_67_read_only_evidence_preflight_design_fails_closed() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_67_read_only_evidence_preflight_design.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.67 Read-Only Evidence Preflight Design" in packet_text
    assert (
        "`classification` | `IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`"
        in packet_text
    )
    assert (
        "`source_commit` | `fbef77a96eac9e7552ac739250113e328225c579`"
        in packet_text
    )
    assert (
        "`d11_66_classification` | "
        "`IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`"
        in packet_text
    )
    assert (
        "`d11_66_decision` | "
        "`READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED`"
        in packet_text
    )
    assert (
        "`d11_67_decision` | "
        "`READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_RECORDED_FAIL_CLOSED`"
        in packet_text
    )
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
    assert "`evidence_collected` | `false`" in packet_text
    assert "`evidence_collection_authorized` | `false`" in packet_text
    assert (
        "`executable_evidence_capture_commands_created` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.68_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW`"
        in packet_text
    )
    assert "It is design-only" in packet_text
    assert "does not authorize or perform evidence collection" in packet_text
    assert "does\nnot create executable evidence-capture commands" in packet_text
    assert "Read-Only Evidence Preflight Design Table" in packet_text
    assert "LOCAL_MAC read-only evidence preflight design" in packet_text
    assert "VPS read-only evidence preflight design" in packet_text
    assert "Broker/TWS read-only evidence preflight design" in packet_text
    assert "Source-controlled documentation/test adjudication" in packet_text
    assert "Evidence collection" in packet_text
    assert "Evidence adjudication" in packet_text
    assert "Provider primary eligibility" in packet_text
    assert "Runtime deployment eligibility" in packet_text
    assert "Broker submit readiness" in packet_text
    assert "Live trading readiness" in packet_text
    assert "Unit 12 opening" in packet_text
    assert "D11.66 Authorization Boundary to Preflight Design Mapping" in (
        packet_text
    )
    assert "Allowed Design-Only Evidence Classes" in packet_text
    assert "Forbidden Evidence Classes and Forbidden Actions" in packet_text
    assert "Required Preflight Safety Checks for a Later Gate" in packet_text
    assert "Fail-Closed Stop Criteria Before Evidence Capture" in packet_text
    assert "Disqualifiers for Later Read-Only Evidence Capture Authorization" in (
        packet_text
    )
    assert "No listed class is collected, authorized for collection" in packet_text
    assert "executable evidence-capture commands" in packet_text
    assert "D11.67 does not authorize those future checks to be executed" in (
        packet_text
    )
    assert "LOCAL_MAC `127.0.0.1:7497` is treated as VPS" in packet_text
    assert "`18789` or `18791` are treated as approved market-data endpoints" in (
        packet_text
    )
    assert "proposal includes executable commands before a separate authorization" in (
        packet_text
    )
    assert "treats broker-coupled candidate status as resolved" in packet_text
    assert "treats historical data availability as provider primary eligibility" in (
        packet_text
    )
    assert "`127.0.0.1` is process-context local" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not\nequivalent to VPS" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        packet_text
    )
    assert "`d11_primary_eligible=false`" in packet_text
    assert "`d11_primary_candidate_status=candidate`" in packet_text
    assert "`candidate_can_count_for_d11` remains unsatisfied" in packet_text
    assert (
        "D11.68_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW"
        in packet_text
    )
    assert "must not be\nruntime activation, broker activation" in packet_text
    assert "evidence_collected=false" in packet_text
    assert "evidence_collection_authorized=false" in packet_text
    assert "executable_evidence_capture_commands_created=false" in packet_text
    assert "runtime_broker_vps_scheduler_systemd_credential_action=false" in (
        packet_text
    )

    assert "### D11.67 Read-Only Evidence Preflight Design" in map_text
    assert str(packet_path) in map_text
    assert "`IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`" in map_text
    assert "`source_commit=fbef77a96eac9e7552ac739250113e328225c579`" in (
        map_text
    )
    assert (
        "`d11_67_decision=READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_RECORDED_FAIL_CLOSED`"
        in map_text
    )
    assert "`evidence_collected=false`" in map_text
    assert "`evidence_collection_authorized=false`" in map_text
    assert "`executable_evidence_capture_commands_created=false`" in map_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action=false`"
        in map_text
    )
    assert "`production_provider_selection_behavior_changed=false`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "design-only lanes for LOCAL_MAC read-only evidence" in map_text
    assert "evidence collection and evidence adjudication are not performed" in (
        map_text
    )
    assert "allows only design-form evidence classes" in map_text
    assert "forbids account/order/execution" in map_text
    assert "executable\nevidence-capture commands" in map_text
    assert "preflight safety checks required for a later gate" in map_text
    assert "LOCAL_MAC\n`127.0.0.1:7497` is not equivalent to VPS" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        map_text
    )
    assert (
        "`D11.68_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW`"
        in map_text
    )
    assert "must not be\nruntime activation, broker activation" in map_text
    assert "evidence collection,\nexecutable evidence-capture commands" in map_text


def test_d11_68_read_only_evidence_preflight_design_review_forces_blocker() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_68_read_only_evidence_preflight_design_review.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.68 Read-Only Evidence Preflight Design Review" in packet_text
    assert (
        "`classification` | "
        "`IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW`" in packet_text
    )
    assert (
        "`source_commit` | `469fe863578693cf01171198a66a0fcd2204e37f`"
        in packet_text
    )
    assert (
        "`d11_67_classification` | "
        "`IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`" in packet_text
    )
    assert (
        "`d11_67_decision` | "
        "`READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_RECORDED_FAIL_CLOSED`"
        in packet_text
    )
    assert (
        "`d11_68_decision` | "
        "`READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`minimum_future_evidence_capture_target_set` | "
        "`NOT_SELECTED_BLOCKED`" in packet_text
    )
    assert "`concrete_blocker_status` | `PRESENT`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`vps_runtime` | `NOT_TOUCHED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`evidence_collected` | `false`" in packet_text
    assert "`evidence_collection_authorized` | `false`" in packet_text
    assert (
        "`executable_evidence_capture_commands_created` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.69_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION`"
        in packet_text
    )
    assert "Forced Binary Review Outcome" in packet_text
    assert "READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_READY" in packet_text
    assert (
        "READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER"
        in packet_text
    )
    assert "does not create another open-ended planning or design-only gate" in (
        packet_text
    )
    assert "D11.67 Review Table" in packet_text
    assert "LOCAL_MAC read-only evidence preflight design" in packet_text
    assert "VPS read-only evidence preflight design" in packet_text
    assert "Broker/TWS read-only evidence preflight design" in packet_text
    assert "Documentation/test adjudication boundary" in packet_text
    assert "Evidence collection boundary" in packet_text
    assert "Evidence adjudication boundary" in packet_text
    assert "Provider primary eligibility boundary" in packet_text
    assert "Runtime deployment eligibility boundary" in packet_text
    assert "Broker submit readiness boundary" in packet_text
    assert "Live trading readiness boundary" in packet_text
    assert "Unit 12 opening boundary" in packet_text
    assert "Concrete Blocker List" in packet_text
    assert "does not select an exact minimum future evidence-capture target set" in (
        packet_text
    )
    assert "does not select a single source context" in packet_text
    assert "does not define per-target allowed fields and forbidden fields" in (
        packet_text
    )
    assert "does not define a per-target non-executable artifact" in packet_text
    assert "does not select an approved endpoint or process context" in packet_text
    assert "VPS `127.0.0.1:7497` remains unvalidated" in packet_text
    assert "`18789` and `18791` remain not approved market-data endpoints" in (
        packet_text
    )
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        packet_text
    )
    assert "`d11_primary_eligible=false`" in packet_text
    assert "`d11_primary_candidate_status=candidate`" in packet_text
    assert "`candidate_can_count_for_d11` remains unsatisfied" in packet_text
    assert "minimum_future_evidence_capture_target_set=NOT_SELECTED_BLOCKED" in (
        packet_text
    )
    assert "`127.0.0.1` is process-context local" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not\nequivalent to VPS" in packet_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in packet_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in packet_text
    assert "D11.69_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION" in (
        packet_text
    )
    assert "evidence_collected=false" in packet_text
    assert "evidence_collection_authorized=false" in packet_text
    assert "executable_evidence_capture_commands_created=false" in packet_text
    assert "runtime_broker_vps_scheduler_systemd_credential_action=false" in (
        packet_text
    )

    assert "### D11.68 Read-Only Evidence Preflight Design Review" in map_text
    assert str(packet_path) in map_text
    assert "`IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW`" in map_text
    assert "`source_commit=469fe863578693cf01171198a66a0fcd2204e37f`" in (
        map_text
    )
    assert (
        "`d11_68_decision=READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in map_text
    )
    assert "`minimum_future_evidence_capture_target_set=NOT_SELECTED_BLOCKED`" in (
        map_text
    )
    assert "`concrete_blocker_status=PRESENT`" in map_text
    assert "`evidence_collected=false`" in map_text
    assert "`evidence_collection_authorized=false`" in map_text
    assert "`executable_evidence_capture_commands_created=false`" in map_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action=false`"
        in map_text
    )
    assert "`production_provider_selection_behavior_changed=false`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "forces exactly one of the two permitted review outcomes" in map_text
    assert "does not select an exact minimum future\nevidence-capture target set" in (
        map_text
    )
    assert "no exact target set, no selected source\ncontext" in map_text
    assert "`ibkr_market_data_candidate`\nremains `broker_coupled=true`" in map_text
    assert "`candidate_can_count_for_d11`\nremains unsatisfied" in map_text
    assert "LOCAL_MAC\n`127.0.0.1:7497` is not equivalent to VPS" in map_text
    assert "`VPS_LOCALHOST_CONTEXT_MISMATCH`" in map_text
    assert "`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`" in map_text
    assert (
        "`D11.69_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION`"
        in map_text
    )
    assert "must not be runtime activation, broker\nactivation" in map_text
    assert "evidence collection,\nexecutable evidence-capture commands" in map_text


def test_d11_69_read_only_evidence_capture_contract_ready_local_mac_only() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_69_read_only_evidence_capture_blocker_remediation.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.69 Read-Only Evidence Capture Blocker Remediation" in packet_text
    assert (
        "`classification` | "
        "`IBKR_D11_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `9d59af162232bbf0d54dd95d4c55b4dfc475fb57`"
        in packet_text
    )
    assert (
        "`d11_68_decision` | "
        "`READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`d11_69_decision` | "
        "`READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY`" in packet_text
    )
    assert (
        "`selected_future_source_context` | "
        "`LOCAL_MAC_ONLY / DIRECT_MAC_TERMINAL / "
        "IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE / 127.0.0.1:7497`"
        in packet_text
    )
    assert "`future_vps_endpoint_reliance` | `false`" in packet_text
    assert "`future_18789_18791_reliance` | `false`" in packet_text
    assert "`future_bridge_tunnel_reliance` | `false`" in packet_text
    assert "`evidence_collected` | `false`" in packet_text
    assert "`evidence_collection_authorized` | `false`" in packet_text
    assert (
        "`executable_evidence_capture_commands_created` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert "`remaining_capture_contract_blockers` | `NONE`" in packet_text
    assert (
        "`remaining_provider_eligibility_blockers` | "
        "`broker_coupled_candidate_unresolved; "
        "candidate_can_count_for_d11_unsatisfied`" in packet_text
    )
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`D11.70_SOURCE_CONTROLLED_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert "D11.68 Blocker Remediation Table" in packet_text
    assert "| No exact target set | Selects the exact future evidence target set" in (
        packet_text
    )
    assert "| No selected source context | Selects `LOCAL_MAC_ONLY`" in packet_text
    assert "No for capture contract; yes for provider eligibility" in packet_text
    assert "Selected Future Source Context" in packet_text
    assert "| Source context | `LOCAL_MAC_ONLY` |" in packet_text
    assert "| Operator surface | `DIRECT_MAC_TERMINAL` only" in packet_text
    assert "| Process context | LOCAL_MAC process context only |" in packet_text
    assert "| Endpoint candidate | `127.0.0.1:7497` |" in packet_text
    assert "| VPS reliance | Forbidden |" in packet_text
    assert "| `18789`/`18791` reliance | Forbidden |" in packet_text
    assert "| Bridge/tunnel/proxy reliance | Forbidden |" in packet_text
    assert "Exact Future Evidence Target Set" in packet_text
    assert "symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`,\nand `MSTR`" in packet_text
    assert "timeframe `15Min`; lookback `120 minutes`" in packet_text
    assert "`target_1_local_process_endpoint_identity`" in packet_text
    assert "`target_2_read_only_socket_configuration`" in packet_text
    assert "`target_3_api_connection_mode`" in packet_text
    assert "`target_4_historical_bars_availability`" in packet_text
    assert "`target_5_response_metadata_for_adjudication`" in packet_text
    assert "`target_6_negative_authority_evidence`" in packet_text
    assert "Allowed Fields Table" in packet_text
    assert "`endpoint_host`, `endpoint_port`, `endpoint_type_candidate`" in (
        packet_text
    )
    assert "`account_data_requested=false`" in packet_text
    assert "`order_data_requested=false`" in packet_text
    assert "`execution_data_requested=false`" in packet_text
    assert "`submit_cancel_modify_requested=false`" in packet_text
    assert "`historical_market_data_only=true`" in packet_text
    assert "Forbidden Fields Table" in packet_text
    assert "Account IDs, account aliases, account values, balances" in packet_text
    assert "Open orders, order IDs, order status, executions" in packet_text
    assert "Usernames, passwords, tokens, API keys" in packet_text
    assert "VPS `127.0.0.1:7497`, `18789`, `18791`" in packet_text
    assert "Non-Executable Artifact Contract" in packet_text
    assert "does not include shell commands, Python\ncommands" in packet_text
    assert "`artifact_identity`" in packet_text
    assert "`operator_context`" in packet_text
    assert "`source_control_references`" in packet_text
    assert "`target_results`" in packet_text
    assert "`redactions`" in packet_text
    assert "`prohibited_fields_attestation`" in packet_text
    assert "`negative_authority_attestation`" in packet_text
    assert "`locality_attestation`" in packet_text
    assert "`adjudication_summary`" in packet_text
    assert "`LOCAL_MAC_CONTEXT_PASS` or `LOCAL_MAC_CONTEXT_FAIL`" in packet_text
    assert "`FORBIDDEN_FIELDS_ABSENT_PASS` or `FORBIDDEN_FIELDS_ABSENT_FAIL`" in (
        packet_text
    )
    assert "`NEGATIVE_AUTHORITY_PASS` or `NEGATIVE_AUTHORITY_FAIL`" in packet_text
    assert "Any FAIL marker, missing marker" in packet_text
    assert "No D11.68 blocker remains active as a blocker" in packet_text
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        packet_text
    )
    assert "`candidate_can_count_for_d11` remains unsatisfied" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not\nequivalent to VPS" in packet_text
    assert "rejects VPS `127.0.0.1:7497` evidence" in packet_text
    assert "rejects `18789` and `18791`\nas approved market-data endpoints" in (
        packet_text
    )
    assert (
        "D11.70_SOURCE_CONTROLLED_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET"
        in packet_text
    )
    assert "D11.69 itself\ndoes not authorize capture" in packet_text

    assert "### D11.69 Read-Only Evidence Capture Blocker Remediation" in map_text
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION`"
        in map_text
    )
    assert "`source_commit=9d59af162232bbf0d54dd95d4c55b4dfc475fb57`" in (
        map_text
    )
    assert (
        "`d11_69_decision=READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY`"
        in map_text
    )
    assert (
        "`selected_future_source_context=LOCAL_MAC_ONLY_DIRECT_MAC_TERMINAL_127_0_0_1_7497`"
        in map_text
    )
    assert "`future_vps_endpoint_reliance=false`" in map_text
    assert "`future_18789_18791_reliance=false`" in map_text
    assert "`future_bridge_tunnel_reliance=false`" in map_text
    assert "`evidence_collected=false`" in map_text
    assert "`evidence_collection_authorized=false`" in map_text
    assert "`executable_evidence_capture_commands_created=false`" in map_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action=false`"
        in map_text
    )
    assert "`remaining_capture_contract_blockers=NONE`" in map_text
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "first\nfuture evidence context as `LOCAL_MAC_ONLY`" in map_text
    assert "no VPS endpoint reliance, no `18789`/`18791`\nreliance" in map_text
    assert "historical bars\navailability for `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in (
        map_text
    )
    assert "records forbidden fields: account IDs, balances, buying power, margin" in (
        map_text
    )
    assert "non-executable artifact contract" in map_text
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        map_text
    )
    assert "`candidate_can_count_for_d11` remains unsatisfied" in map_text
    assert "LOCAL_MAC\n`127.0.0.1:7497` is not equivalent to VPS" in map_text
    assert "rejects VPS\n`127.0.0.1:7497` evidence" in map_text
    assert "rejects `18789` and `18791` as approved market-data endpoints" in (
        map_text
    )
    assert (
        "`D11.70_SOURCE_CONTROLLED_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in map_text
    )
    assert "D11.69\nitself does not authorize capture" in map_text


def test_d11_70_local_mac_read_only_evidence_capture_authorization_packet() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_70_local_mac_read_only_evidence_capture_authorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.70 LOCAL_MAC Read-Only Evidence Capture Authorization Packet" in (
        packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `36342c53ef9ae0fc026c8588511d4a9c8d05f90f`"
        in packet_text
    )
    assert (
        "`d11_69_decision` | `READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY`"
        in packet_text
    )
    assert (
        "`d11_70_decision` | "
        "`LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE`"
        in packet_text
    )
    assert (
        "`authorized_gate_only` | "
        "`D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`"
        in packet_text
    )
    assert "`d11_70_evidence_collected` | `false`" in packet_text
    assert (
        "`d11_70_executable_evidence_capture_commands_created` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert (
        "`remaining_provider_eligibility_blockers` | "
        "`broker_coupled_candidate_unresolved; d11_primary_eligible_false; "
        "d11_primary_candidate_status_candidate; "
        "candidate_can_count_for_d11_unsatisfied`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`"
        in packet_text
    )
    assert "No source-controlled contradiction was found" in packet_text
    assert "| Source context | `LOCAL_MAC_ONLY` |" in packet_text
    assert "| Operator surface | `DIRECT_MAC_TERMINAL` only |" in packet_text
    assert "| Process context | LOCAL_MAC process context only |" in packet_text
    assert "| Endpoint candidate | `127.0.0.1:7497` |" in packet_text
    assert "| Endpoint class | IBKR Paper TWS/Gateway local socket candidate |" in (
        packet_text
    )
    assert "| Evidence scope | Market-data/provider-readiness only |" in packet_text
    assert "| VPS reliance | Forbidden |" in packet_text
    assert "| `18789`/`18791` reliance | Forbidden |" in packet_text
    assert "| Bridge/tunnel/proxy reliance | Forbidden |" in packet_text
    assert "`target_1_local_process_endpoint_identity`" in packet_text
    assert "`target_2_read_only_socket_configuration`" in packet_text
    assert "`target_3_api_connection_mode`" in packet_text
    assert "`target_4_historical_bars_availability`" in packet_text
    assert "`target_5_response_metadata_for_adjudication`" in packet_text
    assert "`target_6_negative_authority_evidence`" in packet_text
    assert "`AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in packet_text
    assert "timeframe `15Min`; lookback/request scope `120 minutes`" in (
        packet_text
    )
    assert "D11.70 authorizes only D11.71 to contain bounded execution" in (
        packet_text
    )
    assert "D11.70\nitself contains no executable evidence-capture commands" in (
        packet_text
    )
    assert "Allowed Fields" in packet_text
    assert "`account_data_requested=false`" in packet_text
    assert "`position_data_requested=false`" in packet_text
    assert "`order_data_requested=false`" in packet_text
    assert "`execution_data_requested=false`" in packet_text
    assert "`submit_cancel_modify_requested=false`" in packet_text
    assert "`historical_market_data_only=true`" in packet_text
    assert "Forbidden Fields" in packet_text
    assert "Account IDs, account aliases, account values, balances" in packet_text
    assert "Open orders, order IDs, order status, executions" in packet_text
    assert "Usernames, passwords, tokens, API keys" in packet_text
    assert "VPS `127.0.0.1:7497`, `18789`, `18791`" in packet_text
    assert "Broker submit readiness, live trading readiness" in packet_text
    assert "Redaction Rules" in packet_text
    assert "A redacted prohibited field still\nforces fail-closed" in packet_text
    assert "Required PASS/FAIL Markers" in packet_text
    assert "`API_CONNECTION_MODE_PASS` or `API_CONNECTION_MODE_FAIL`" in packet_text
    assert "`FORBIDDEN_FIELDS_ABSENT_PASS` or `FORBIDDEN_FIELDS_ABSENT_FAIL`" in (
        packet_text
    )
    assert "`NEGATIVE_AUTHORITY_PASS` or `NEGATIVE_AUTHORITY_FAIL`" in packet_text
    assert "Required Artifact Sections" in packet_text
    assert "`artifact_identity`" in packet_text
    assert "`operator_context`" in packet_text
    assert "`source_control_references`" in packet_text
    assert "`target_results`" in packet_text
    assert "`redactions`" in packet_text
    assert "`prohibited_fields_attestation`" in packet_text
    assert "`negative_authority_attestation`" in packet_text
    assert "`locality_attestation`" in packet_text
    assert "`adjudication_summary`" in packet_text
    assert "Future Capture Fail-Closed Conditions" in packet_text
    assert "the source context is not `LOCAL_MAC_ONLY`" in packet_text
    assert "the operator surface is not `DIRECT_MAC_TERMINAL`" in packet_text
    assert "the endpoint candidate is not `127.0.0.1:7497`" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is treated as VPS" in packet_text
    assert "VPS, `18789`, `18791`, bridge, tunnel, proxy" in packet_text
    assert "account, order, execution, position, balance, portfolio" in packet_text
    assert "Non-Authorized Contexts" in packet_text
    assert "D11.70 rejects treating LOCAL_MAC `127.0.0.1:7497` as VPS" in (
        packet_text
    )
    assert "D11.70 rejects `18789` and `18791` as approved market-data" in (
        packet_text
    )
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        packet_text
    )
    assert "`ibkr_market_data_candidate` remains `d11_primary_eligible=false`" in (
        packet_text
    )
    assert "`d11_primary_candidate_status` remains `candidate`" in packet_text
    assert "`candidate_can_count_for_d11` remains unsatisfied" in packet_text
    assert "Future evidence capture may support later market-data provider-readiness" in (
        packet_text
    )
    assert "but it cannot itself approve IBKR primary eligibility" in packet_text
    assert (
        "D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET"
        in packet_text
    )
    assert "D11.70 itself does not collect evidence" in packet_text

    assert (
        "### D11.70 LOCAL_MAC Read-Only Evidence Capture Authorization Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in map_text
    )
    assert "`source_commit=36342c53ef9ae0fc026c8588511d4a9c8d05f90f`" in (
        map_text
    )
    assert (
        "`d11_70_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE`"
        in map_text
    )
    assert (
        "`D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`"
        in map_text
    )
    assert "`d11_70_evidence_collected=false`" in map_text
    assert (
        "`d11_70_executable_evidence_capture_commands_created=false`"
        in map_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action=false`"
        in map_text
    )
    assert "`ibkr_primary_eligibility=NOT_APPROVED`" in map_text
    assert "`d11_status=D11_INSUFFICIENT`" in map_text
    assert "`unit_12_status=UNIT_12_BLOCKED`" in map_text
    assert "future source context only as `LOCAL_MAC_ONLY`" in map_text
    assert "`DIRECT_MAC_TERMINAL`, LOCAL_MAC process context" in map_text
    assert "endpoint candidate\n`127.0.0.1:7497`" in map_text
    assert "no `18789` or\n`18791` reliance" in map_text
    assert "historical bars availability for `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in (
        map_text
    )
    assert "timeframe `15Min`, lookback/request scope `120 minutes`" in map_text
    assert "records forbidden fields and activities" in map_text
    assert "VPS `127.0.0.1:7497`,\n`18789`, `18791`" in map_text
    assert "requires future capture to fail closed" in map_text
    assert "account/order/execution/position/balance/portfolio" in map_text
    assert "LOCAL_MAC\n`127.0.0.1:7497` is not equivalent to VPS" in map_text
    assert "rejects\n`18789` and `18791` as approved market-data endpoints" in map_text
    assert "`candidate_can_count_for_d11`\nremains unsatisfied" in map_text
    assert "D11.70 itself\ndoes not collect evidence" in map_text
    assert "does not create executable evidence-capture\ncommands" in map_text


def test_d11_71_local_mac_read_only_evidence_capture_execution_packet_ready() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_71_local_mac_read_only_evidence_capture_execution_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.71 LOCAL_MAC Read-Only Evidence Capture Execution Packet" in (
        packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `2f05f254f54f2feb87760820ddc48456e48f0c89`"
        in packet_text
    )
    assert (
        "`d11_70_decision` | "
        "`LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE`"
        in packet_text
    )
    assert (
        "`d11_71_decision` | "
        "`LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY`"
        in packet_text
    )
    assert "`future_execution_source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert (
        "`future_execution_operator_surface` | `DIRECT_MAC_TERMINAL`"
        in packet_text
    )
    assert (
        "`future_execution_endpoint_candidate` | `127.0.0.1:7497`"
        in packet_text
    )
    assert (
        "`future_execution_endpoint_class` | "
        "`IBKR_PAPER_TWS_GATEWAY_LOCAL_SOCKET_CANDIDATE`" in packet_text
    )
    assert (
        "`future_execution_symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR`"
        in packet_text
    )
    assert "`future_execution_timeframe` | `15Min`" in packet_text
    assert "`future_execution_lookback_minutes` | `120`" in packet_text
    assert "`d11_71_evidence_capture_executed` | `false`" in packet_text
    assert (
        "`d11_71_broker_tws_api_network_runtime_action` | `false`"
        in packet_text
    )
    assert "`d11_71_executable_commands_run_by_codex` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert (
        "`remaining_provider_eligibility_blockers` | "
        "`broker_coupled_true; d11_primary_eligible_false; "
        "d11_primary_candidate_status_candidate; "
        "candidate_can_count_for_d11_unsatisfied`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`"
        in packet_text
    )
    assert "Source-Controlled Preconditions for Future Execution" in packet_text
    assert "| Working directory | `/Users/openclawcontrol/Documents/openclaw-stocks` |" in (
        packet_text
    )
    assert "| Python | `.venv-312/bin/python` |" in packet_text
    assert "| Endpoint candidate | `127.0.0.1:7497` only |" in packet_text
    assert "Future Operator Command: Not Run in D11.71" in packet_text
    assert "# FUTURE D11.72 ONLY - DO NOT RUN IN D11.71" in packet_text
    assert "cd /Users/openclawcontrol/Documents/openclaw-stocks" in packet_text
    assert ".venv-312/bin/python -m tools.ops.ibkr_market_data_read_only_smoke" in (
        packet_text
    )
    assert "--symbol AAPL --symbol MSFT --symbol NVDA --symbol TSLA --symbol MSTR" in (
        packet_text
    )
    assert "--timeframe 15Min" in packet_text
    assert "--lookback-minutes 120" in packet_text
    assert "--host 127.0.0.1 --port 7497" in packet_text
    assert "--authorize-local-ibkr-read-only-smoke" in packet_text
    assert "Codex did not run this\ncommand in D11.71" in packet_text
    assert "Expected Artifact Fields" in packet_text
    assert "`source_context=LOCAL_MAC_ONLY`" in packet_text
    assert "`operator_surface=DIRECT_MAC_TERMINAL`" in packet_text
    assert "`endpoint_port=7497`" in packet_text
    assert "`symbols=AAPL,MSFT,NVDA,TSLA,MSTR`" in packet_text
    assert "`timeframe=15Min`" in packet_text
    assert "`lookback_minutes=120`" in packet_text
    assert "`broker_api_authority=false`" in packet_text
    assert "`order_authority=false`" in packet_text
    assert "`execution_authority=false`" in packet_text
    assert "`unit_12_opened=false`" in packet_text
    assert "`port_18789_used=false`" in packet_text
    assert "`port_18791_used=false`" in packet_text
    assert "Required PASS/FAIL Markers" in packet_text
    assert "`DIRECT_MAC_TERMINAL_PASS` or `DIRECT_MAC_TERMINAL_FAIL`" in (
        packet_text
    )
    assert "`ENDPOINT_127_0_0_1_7497_SCOPE_PASS`" in packet_text
    assert "`NO_VPS_18789_18791_BRIDGE_TUNNEL_PROXY_PASS`" in packet_text
    assert "`SYMBOL_SCOPE_PASS` or `SYMBOL_SCOPE_FAIL`" in packet_text
    assert "`TIMEFRAME_15MIN_PASS` or `TIMEFRAME_15MIN_FAIL`" in packet_text
    assert "`LOOKBACK_120_MINUTES_PASS` or `LOOKBACK_120_MINUTES_FAIL`" in (
        packet_text
    )
    assert "`FORBIDDEN_FIELDS_ABSENT_PASS` or `FORBIDDEN_FIELDS_ABSENT_FAIL`" in (
        packet_text
    )
    assert "`NEGATIVE_AUTHORITY_PASS` or `NEGATIVE_AUTHORITY_FAIL`" in packet_text
    assert "Required Redactions" in packet_text
    assert "Redaction never converts a forbidden-field violation" in packet_text
    assert "Forbidden Fields and Forbidden Contexts" in packet_text
    assert "account IDs, account aliases, account values, balances" in packet_text
    assert "open orders, order IDs, order status, executions" in packet_text
    assert "usernames, passwords, tokens, API keys" in packet_text
    assert "VPS, `18789`, `18791`, bridge, tunnel, proxy" in packet_text
    assert "broker submit readiness, live trading readiness" in packet_text
    assert "Future Run Fail-Closed Conditions" in packet_text
    assert "branch is not `main`" in packet_text
    assert "worktree is dirty" in packet_text
    assert "endpoint is not `127.0.0.1:7497`" in packet_text
    assert "source context is not `LOCAL_MAC_ONLY`" in packet_text
    assert "operator surface is not `DIRECT_MAC_TERMINAL`" in packet_text
    assert "TWS/Gateway is not already manually open" in packet_text
    assert "any symbol outside `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in (
        packet_text
    )
    assert "any timeframe other than `15Min`" in packet_text
    assert "lookback/request scope is not `120 minutes`" in packet_text
    assert "Post-Capture Review Requirements for the Next Gate" in packet_text
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        packet_text
    )
    assert "`candidate_can_count_for_d11` remains unsatisfied" in packet_text
    assert "D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN" in (
        packet_text
    )
    assert "d11_71_evidence_capture_executed=false" in packet_text
    assert "d11_71_executable_commands_run_by_codex=false" in packet_text

    assert (
        "### D11.71 LOCAL_MAC Read-Only Evidence Capture Execution Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`"
        in map_text
    )
    assert "`source_commit=2f05f254f54f2feb87760820ddc48456e48f0c89`" in (
        map_text
    )
    assert (
        "`d11_71_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY`"
        in map_text
    )
    assert "future execution source context as `LOCAL_MAC_ONLY`" in map_text
    assert "operator surface as `DIRECT_MAC_TERMINAL`" in map_text
    assert "`127.0.0.1:7497`" in map_text
    assert "symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in map_text
    assert "timeframe `15Min`" in map_text
    assert "lookback/request scope `120 minutes`" in map_text
    assert "`d11_71_evidence_capture_executed=false`" in map_text
    assert "`d11_71_broker_tws_api_network_runtime_action=false`" in map_text
    assert "`d11_71_executable_commands_run_by_codex=false`" in map_text
    assert "marks it\n`FUTURE D11.72 ONLY - DO NOT RUN IN D11.71`" in map_text
    assert ".venv-312/bin/python" in map_text
    assert "targets only `127.0.0.1:7497`" in map_text
    assert "requests only\n`AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in map_text
    assert "no VPS/`18789`/`18791`/bridge/tunnel/proxy" in map_text
    assert "forbids account IDs, account aliases" in map_text
    assert "requires future D11.72 to fail closed" in map_text
    assert "`candidate_can_count_for_d11`\nremains unsatisfied" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY` remains `NOT_APPROVED`" in map_text
    assert "`D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`" in map_text
    assert "evidence\ncapture in D11.71" in map_text
    assert "executable command execution by Codex" in map_text


def test_d11_72_local_mac_read_only_operator_run_record_recency_caveat() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_72_local_mac_read_only_evidence_capture_operator_run_record.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.72 LOCAL_MAC Read-Only Evidence Capture Operator Run Record"
        in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD`"
        in packet_text
    )
    assert (
        "`source_commit` | `7479f708c53067980491c31bb37b41c2bcbf4eea`"
        in packet_text
    )
    assert (
        "`d11_71_decision` | "
        "`LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY`"
        in packet_text
    )
    assert "`d11_72_run_status` | `COMPLETED_BY_OPERATOR`" in packet_text
    assert (
        "`d11_72_evidence_classification` | "
        "`READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`" in packet_text
    )
    assert "`tool_run_by` | `OPERATOR_NOT_CODEX`" in packet_text
    assert "`source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert "`endpoint_candidate` | `127.0.0.1:7497`" in packet_text
    assert "`symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR`" in packet_text
    assert "`timeframe` | `15Min`" in packet_text
    assert "`lookback_minutes` | `120`" in packet_text
    assert (
        "`result_type` | `ibkr_local_read_only_market_data_smoke`"
        in packet_text
    )
    assert "`all_symbols_read_only` | `true`" in packet_text
    assert (
        "`all_symbols_provider_key` | `ibkr_market_data_candidate`"
        in packet_text
    )
    assert (
        "`all_symbols_d11_primary_candidate_status` | `candidate`"
        in packet_text
    )
    assert "`all_symbols_d11_primary_eligible` | `false`" in packet_text
    assert "`all_symbols_d11_countable` | `false`" in packet_text
    assert (
        "`all_symbols_freshness_classification` | `recency_caveated`"
        in packet_text
    )
    assert (
        "`all_symbols_failure_reason` | "
        "`regular_session_closed_latest_candle_valid_for_last_session`"
        in packet_text
    )
    assert "`broker_api_authority` | `false`" in packet_text
    assert "`order_authority` | `false`" in packet_text
    assert "`execution_authority` | `false`" in packet_text
    assert "`package_capture` | `false`" in packet_text
    assert "`replay` | `false`" in packet_text
    assert "`scoring` | `false`" in packet_text
    assert "`candidate_generation` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert "`d11_72_rerun_authorized` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`D11.73_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`"
        in packet_text
    )
    assert "not D11-countable for primary eligibility" in packet_text
    assert "all five\nsymbols returned `d11_countable=false`" in packet_text
    assert (
        "`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`"
        in packet_text
    )

    for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"):
        assert f"| `{symbol}` | `true` | `ibkr_market_data_candidate` |" in (
            packet_text
        )
    assert packet_text.count("`2026-06-26T19:45:00+00:00`") >= 5
    assert packet_text.count("`2026-06-27T01:40:31.383039+00:00`") >= 5
    assert packet_text.count("`2026-06-27T03:40:31.383039+00:00`") >= 5
    assert packet_text.count("`475.52305065`") >= 5
    assert packet_text.count("`recency_caveated`") >= 5
    assert (
        packet_text.count(
            "`regular_session_closed_latest_candle_valid_for_last_session`"
        )
        >= 5
    )
    assert packet_text.count("| `false` | `false` | `candidate` |") == 5

    for marker in (
        "no_account_query",
        "no_position_query",
        "no_margin_query",
        "no_buying_power_query",
        "no_portfolio_query",
        "no_order_placement",
        "no_order_modification",
        "no_order_cancellation",
        "no_order_routing",
        "no_execution_authority",
        "no_package_capture",
        "no_replay",
        "no_scoring",
        "no_candidate_generation",
        "no_unit_12_opening",
        "no_vps_runtime_systemd_timer_mutation",
    ):
        assert f"`{marker}`" in packet_text

    assert "not VPS localhost evidence" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "used no VPS path, no `18789`, no `18791`, no\nbridge" in (
        packet_text
    )
    assert "does not approve `18789` or `18791`" in packet_text
    assert "D11.72 does not authorize a rerun" in packet_text
    assert (
        "Any future fresh\nregular-session rerun would require a new "
        "source-controlled authorization" in packet_text
    )
    assert (
        "D11.73 must be a source-controlled adjudication gate that decides "
        "whether this\nD11.72 capture is sufficient, insufficient due to "
        "the recency caveat, or\nrequires a fresh regular-session rerun "
        "under a new authorization" in packet_text
    )

    assert (
        "### D11.72 LOCAL_MAC Read-Only Evidence Capture Operator Run Record"
        in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD`"
        in map_text
    )
    assert "`source_commit=7479f708c53067980491c31bb37b41c2bcbf4eea`" in (
        map_text
    )
    assert (
        "`d11_72_run_status=COMPLETED_BY_OPERATOR`" in map_text
    )
    assert (
        "`d11_72_evidence_classification=READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`"
        in map_text
    )
    assert "The command was run by the operator, not by Codex" in map_text
    assert "`LOCAL_MAC_ONLY`" in map_text
    assert "`DIRECT_MAC_TERMINAL`" in map_text
    assert "endpoint candidate `127.0.0.1:7497`" in map_text
    assert "symbols `AAPL`, `MSFT`, `NVDA`,\n`TSLA`, `MSTR`" in map_text
    assert "`d11_countable=false`" in map_text
    assert "`freshness_classification=recency_caveated`" in map_text
    assert "`lag_minutes=475.52305065`" in map_text
    assert "not\nD11-countable for primary eligibility" in map_text
    assert "no account query, position query, margin\nquery" in map_text
    assert "no VPS path, no `18789`, no `18791`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11=D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in map_text
    assert "D11.72 does not authorize a rerun" in map_text
    assert "`D11.73_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`" in (
        map_text
    )


def test_d11_73_local_mac_read_only_capture_adjudication_requires_fresh_rerun() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_73_local_mac_read_only_evidence_capture_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.73 LOCAL_MAC Read-Only Evidence Capture Adjudication"
        in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `7f62130f08a03167975f9187c5a0314f95074568`"
        in packet_text
    )
    assert (
        "`d11_72_evidence_classification` | "
        "`READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`" in packet_text
    )
    assert "`d11_72_all_symbols_d11_countable` | `false`" in packet_text
    assert "`d11_72_all_symbols_d11_primary_eligible` | `false`" in (
        packet_text
    )
    assert (
        "`d11_72_all_symbols_freshness_classification` | "
        "`recency_caveated`" in packet_text
    )
    assert (
        "`d11_73_decision` | "
        "`D11_72_EVIDENCE_ADJUDICATED_INSUFFICIENT_REQUIRES_FRESH_REGULAR_SESSION_RERUN`"
        in packet_text
    )
    assert "`d11_73_evidence_collected` | `false`" in packet_text
    assert (
        "`d11_73_executable_evidence_capture_commands_created` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`D11.74_SOURCE_CONTROLLED_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert "operationally useful proof" in packet_text
    assert "outside the\nusable freshness window" in packet_text
    assert "not countable for D11 primary eligibility" in packet_text
    assert "cannot approve IBKR primary eligibility" in packet_text
    assert "cannot mark D11 complete" in packet_text

    for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"):
        assert f"| `{symbol}` | `true` | `ibkr_market_data_candidate` |" in (
            packet_text
        )
    assert packet_text.count("`local_read_only_smoke`") >= 5
    assert packet_text.count("`2026-06-26T19:45:00+00:00`") >= 5
    assert packet_text.count("`2026-06-27T01:40:31.383039+00:00`") >= 5
    assert packet_text.count("`2026-06-27T03:40:31.383039+00:00`") >= 5
    assert packet_text.count("`475.52305065`") >= 5
    assert packet_text.count("`recency_caveated`") >= 5
    assert (
        packet_text.count(
            "`regular_session_closed_latest_candle_valid_for_last_session`"
        )
        >= 5
    )
    assert packet_text.count("| `false` | `false` | `candidate` |") == 5
    assert (
        packet_text.count(
            "`NON_COUNTABLE_REQUIRES_FRESH_REGULAR_SESSION_RERUN`"
        )
        == 5
    )

    for marker in (
        "no_account_query",
        "no_position_query",
        "no_margin_query",
        "no_buying_power_query",
        "no_portfolio_query",
        "no_order_placement",
        "no_order_modification",
        "no_order_cancellation",
        "no_order_routing",
        "no_execution_authority",
        "no_package_capture",
        "no_replay",
        "no_scoring",
        "no_candidate_generation",
        "no_unit_12_opening",
        "no_vps_runtime_systemd_timer_mutation",
    ):
        assert f"`{marker}`" in packet_text

    assert "IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED" in packet_text
    assert "D11=D11_INSUFFICIENT" in packet_text
    assert "UNIT_12=UNIT_12_BLOCKED" in packet_text
    assert "`candidate_can_count_for_d11` remains unsatisfied" in packet_text
    assert "broker submit readiness remains `NOT_APPROVED`" in packet_text
    assert "live trading readiness remains `NOT_APPROVED`" in packet_text
    assert "used no VPS path, no `18789`, no `18791`, no bridge" in (
        packet_text
    )
    assert "LOCAL_MAC `127.0.0.1:7497` remains process-context local" in (
        packet_text
    )
    assert "D11.73 does not create executable broker/TWS/API/runtime commands" in (
        packet_text
    )
    assert "D11.74 must\nbe source-controlled authorization only" in packet_text
    assert "must not itself perform evidence\ncapture" in packet_text
    assert "must not approve IBKR primary eligibility" in packet_text

    assert (
        "### D11.73 LOCAL_MAC Read-Only Evidence Capture Adjudication"
        in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`"
        in map_text
    )
    assert "`source_commit=7f62130f08a03167975f9187c5a0314f95074568`" in (
        map_text
    )
    assert (
        "`d11_73_decision=D11_72_EVIDENCE_ADJUDICATED_INSUFFICIENT_REQUIRES_FRESH_REGULAR_SESSION_RERUN`"
        in map_text
    )
    assert "does not rerun IBKR" in map_text
    assert "not countable for D11 primary eligibility" in map_text
    assert "`d11_countable=false`" in map_text
    assert "`d11_primary_eligible=false`" in map_text
    assert "`freshness_classification=recency_caveated`" in map_text
    assert "`lag_minutes=475.52305065`" in map_text
    assert "outside the usable freshness\nwindow" in map_text
    assert "`candidate_can_count_for_d11`\nremains unsatisfied" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11=D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in map_text
    assert (
        "`D11.74_SOURCE_CONTROLLED_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in map_text
    )


def test_d11_74_fresh_regular_session_capture_authorization_packet() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_74_fresh_regular_session_read_only_evidence_capture_authorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.74 Fresh Regular-Session Read-Only Evidence Capture "
        "Authorization Packet" in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `08bc4cbedd4b465eb6308deadb4a781acc991512`"
        in packet_text
    )
    assert (
        "`d11_73_decision` | "
        "`D11_72_EVIDENCE_ADJUDICATED_INSUFFICIENT_REQUIRES_FRESH_REGULAR_SESSION_RERUN`"
        in packet_text
    )
    assert (
        "`d11_74_decision` | "
        "`FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_OPERATOR_RUN`"
        in packet_text
    )
    assert (
        "`authorized_gate_only` | "
        "`D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`"
        in packet_text
    )
    assert "`d11_74_evidence_collected` | `false`" in packet_text
    assert (
        "`d11_74_executable_evidence_capture_command_run` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert (
        "`remaining_provider_eligibility_blockers` | "
        "`broker_coupled_true; d11_primary_eligible_false; "
        "d11_primary_candidate_status_candidate; "
        "candidate_can_count_for_d11_unsatisfied`" in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`"
        in packet_text
    )

    assert "D11.73 Adjudication Basis" in packet_text
    assert "`READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`" in packet_text
    assert "all five symbols returned `d11_countable=false`" in packet_text
    assert "all five symbols returned `d11_primary_eligible=false`" in (
        packet_text
    )
    assert "all five symbols returned `freshness_classification=recency_caveated`" in (
        packet_text
    )
    assert (
        "`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`"
        in packet_text
    )
    assert "`latest_candle_timestamp=2026-06-26T19:45:00+00:00`" in (
        packet_text
    )
    assert "`requested_start=2026-06-27T01:40:31.383039+00:00`" in (
        packet_text
    )
    assert "`requested_end=2026-06-27T03:40:31.383039+00:00`" in packet_text
    assert "`lag_minutes=475.52305065`" in packet_text
    assert "outside the usable freshness window" in packet_text

    assert "| Source context | `LOCAL_MAC_ONLY` |" in packet_text
    assert "| Operator surface | `DIRECT_MAC_TERMINAL` only |" in packet_text
    assert "| Endpoint candidate | `127.0.0.1:7497` |" in packet_text
    assert "| Timing | Fresh regular-session evidence capture only |" in (
        packet_text
    )
    assert "`AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in packet_text
    assert "timeframe `15Min`" in packet_text
    assert "lookback `120 minutes`" in packet_text
    assert (
        "next operator run may use the D11.71 bounded command/procedure only"
        in packet_text
    )
    assert "D11.74 itself does not create executable commands for Codex to run" in (
        packet_text
    )

    assert "Regular-Session Timing Boundary" in packet_text
    assert (
        "current or\nsufficiently recent `15Min` candle is expected"
        in packet_text
    )
    assert "explicitly rejects after-session reruns" in packet_text
    assert "regular_session_closed_latest_candle_valid_for_last_session" in (
        packet_text
    )
    for required_field in (
        "requested_start",
        "requested_end",
        "latest_candle_timestamp",
        "lag_minutes",
        "freshness_classification",
        "failure_reason",
        "d11_countable",
        "d11_primary_eligible",
    ):
        assert f"`{required_field}`" in packet_text
    assert (
        "fail closed if all symbols remain `d11_countable=false` due to the\n"
        "regular-session-closed recency caveat" in packet_text
    )

    assert "Allowed Fields" in packet_text
    assert "`target_1_local_process_endpoint_identity`" in packet_text
    assert "`target_2_read_only_socket_configuration`" in packet_text
    assert "`target_3_regular_session_historical_bars_availability`" in (
        packet_text
    )
    assert "`target_4_response_metadata_for_adjudication`" in packet_text
    assert "`target_5_negative_authority_evidence`" in packet_text
    assert "`broker_api_authority=false`" in packet_text
    assert "`order_authority=false`" in packet_text
    assert "`execution_authority=false`" in packet_text

    assert "Forbidden Fields" in packet_text
    assert "Account IDs, account aliases, account values, balances" in (
        packet_text
    )
    assert "Open orders, order IDs, order status, executions" in packet_text
    assert "Usernames, passwords, tokens, API keys" in packet_text
    assert "VPS `127.0.0.1:7497`, `18789`, `18791`, bridge" in packet_text
    assert "Service changes, scheduler changes, systemd changes" in packet_text
    assert "Package capture, replay, scoring, candidate generation" in (
        packet_text
    )
    assert "IBKR primary eligibility approval" in packet_text

    assert "Required PASS/FAIL Markers" in packet_text
    assert "`REGULAR_SESSION_TIMING_PASS` or `REGULAR_SESSION_TIMING_FAIL`" in (
        packet_text
    )
    assert (
        "`NO_AFTER_SESSION_STALE_CAPTURE_PASS` or "
        "`NO_AFTER_SESSION_STALE_CAPTURE_FAIL`" in packet_text
    )
    assert "`FORBIDDEN_FIELDS_ABSENT_PASS`" in packet_text
    assert "`NEGATIVE_AUTHORITY_PASS`" in packet_text
    assert "`ADJUDICATION_READY_PASS`" in packet_text

    assert "Required Artifact Sections" in packet_text
    for section in (
        "artifact_identity",
        "operator_context",
        "regular_session_timing",
        "request_scope",
        "target_results",
        "negative_authority_attestation",
        "locality_attestation",
        "adjudication_summary",
    ):
        assert f"`{section}`" in packet_text

    assert "Future Run Fail-Closed Conditions" in packet_text
    assert "source context is not `LOCAL_MAC_ONLY`" in packet_text
    assert "operator surface is not `DIRECT_MAC_TERMINAL`" in packet_text
    assert "endpoint is not `127.0.0.1:7497`" in packet_text
    assert "run timing is not a regular-session window" in packet_text
    assert "all symbols remain `d11_countable=false`" in packet_text
    assert "any symbol outside `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`" in (
        packet_text
    )
    assert "any timeframe other than `15Min`" in packet_text
    assert "lookback/request scope is not `120 minutes`" in packet_text
    assert "account/order/execution/position/balance/portfolio/credential data" in (
        packet_text
    )
    assert "VPS, `18789`, `18791`, bridge, tunnel, proxy" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is treated as VPS" in packet_text

    assert "D11.74 does not authorize VPS evidence" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` is not\nequivalent to VPS" in (
        packet_text
    )
    assert "rejects `18789` and `18791`" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11=D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in packet_text
    assert "`ibkr_market_data_candidate` remains `broker_coupled=true`" in (
        packet_text
    )
    assert "`candidate_can_count_for_d11` remains unsatisfied" in packet_text
    assert "Future evidence capture may support later adjudication but cannot itself\napprove IBKR primary eligibility" in (
        packet_text
    )

    assert (
        "### D11.74 Fresh Regular-Session Read-Only Evidence Capture "
        "Authorization Packet" in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`"
        in map_text
    )
    assert "`source_commit=08bc4cbedd4b465eb6308deadb4a781acc991512`" in (
        map_text
    )
    assert (
        "`d11_74_decision=FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_OPERATOR_RUN`"
        in map_text
    )
    assert "D11.74 authorizes only the next operator-run gate" in map_text
    assert "collects no\nevidence" in map_text
    assert "runs no executable evidence-capture command" in map_text
    assert "fresh regular-session timing" in map_text
    assert "explicitly rejects after-session\nreruns" in map_text
    assert "`REGULAR_SESSION_TIMING_PASS`" in map_text
    assert "`NO_AFTER_SESSION_STALE_CAPTURE_PASS`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11=D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in map_text
    assert (
        "`D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`"
        in map_text
    )


def test_d11_76_fresh_regular_session_operator_run_record_clean_countable() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_76_fresh_regular_session_local_mac_read_only_evidence_capture_operator_run_record.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.76 Fresh Regular-Session LOCAL_MAC Read-Only Evidence Capture "
        "Operator Run Record" in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD`"
        in packet_text
    )
    assert (
        "`source_commit` | `6db5d0b2f1cc47679dd194c846206a0dde36693c`"
        in packet_text
    )
    assert (
        "`d11_75_gate` | "
        "`D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`"
        in packet_text
    )
    assert "`d11_75_run_status` | `COMPLETED_BY_OPERATOR`" in packet_text
    assert (
        "`d11_76_evidence_classification` | "
        "`FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE`"
        in packet_text
    )
    assert (
        "`evidence_record_only_not_provider_approval` | `true`"
        in packet_text
    )
    assert "`tool_run_by` | `OPERATOR_NOT_CODEX`" in packet_text
    assert "`source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert "`endpoint_candidate` | `127.0.0.1:7497`" in packet_text
    assert "`symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR`" in packet_text
    assert "`timeframe` | `15Min`" in packet_text
    assert "`lookback_minutes` | `120`" in packet_text
    assert "`authority` | `READ_ONLY_MARKET_DATA_ONLY`" in packet_text
    assert (
        "`result_type` | `ibkr_local_read_only_market_data_smoke`"
        in packet_text
    )
    assert (
        "`all_symbols_latest_candle_timestamp` | "
        "`2026-06-29T14:00:00+00:00`" in packet_text
    )
    assert (
        "`all_symbols_requested_start` | "
        "`2026-06-29T12:20:17.713714+00:00`" in packet_text
    )
    assert (
        "`all_symbols_requested_end` | "
        "`2026-06-29T14:20:17.713714+00:00`" in packet_text
    )
    assert (
        "`all_symbols_lag_minutes` | `20.295228566666665`" in packet_text
    )
    assert "`all_symbols_freshness_classification` | `clean`" in packet_text
    assert "`all_symbols_failure_reason` | ``" in packet_text
    assert "`all_symbols_d11_countable` | `true`" in packet_text
    assert (
        "`all_symbols_d11_primary_candidate_status` | `candidate`"
        in packet_text
    )
    assert "`all_symbols_d11_primary_eligible` | `false`" in packet_text
    assert "`broker_api_authority` | `false`" in packet_text
    assert "`order_authority` | `false`" in packet_text
    assert "`execution_authority` | `false`" in packet_text
    assert "`package_capture` | `false`" in packet_text
    assert "`replay` | `false`" in packet_text
    assert "`scoring` | `false`" in packet_text
    assert "`candidate_generation` | `false`" in packet_text
    assert "`d11_completion_authority` | `false`" in packet_text
    assert "`ibkr_primary_eligibility` | `NOT_APPROVED`" in packet_text
    assert "`d11_status` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`D11.77_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`"
        in packet_text
    )

    assert "This is an evidence record only, not provider approval" in (
        packet_text
    )
    assert "does not\ndecide whether that evidence is sufficient" in packet_text
    assert "D11.77 is the first permissible gate to adjudicate" in packet_text
    assert (
        "D11.76 itself must\nnot approve IBKR primary eligibility"
        in packet_text
    )
    assert "must not complete D11" in packet_text
    assert "must not open\nUnit 12" in packet_text

    for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"):
        assert f"| `{symbol}` | `true` | `ibkr_market_data_candidate` |" in (
            packet_text
        )
    assert packet_text.count("`2026-06-29T14:00:00+00:00`") >= 5
    assert packet_text.count("`2026-06-29T12:20:17.713714+00:00`") >= 5
    assert packet_text.count("`2026-06-29T14:20:17.713714+00:00`") >= 5
    assert packet_text.count("`20.295228566666665`") >= 5
    assert packet_text.count("`clean`") >= 6
    assert packet_text.count("| `true` | `false` | `candidate` | `15Min` |") == 5

    for marker in (
        "no_account_query",
        "no_position_query",
        "no_portfolio_query",
        "no_balance_query",
        "no_margin_query",
        "no_buying_power_query",
        "no_order_placement",
        "no_order_modification",
        "no_order_cancellation",
        "no_order_routing",
        "no_execution_authority",
        "no_package_capture",
        "no_replay",
        "no_scoring",
        "no_candidate_generation",
        "no_unit_12_opening",
        "no_vps_runtime_systemd_timer_mutation",
    ):
        assert f"`{marker}`" in packet_text

    assert "not VPS localhost evidence" in packet_text
    assert "does not validate VPS `127.0.0.1:7497`" in packet_text
    assert "used no VPS path, no `18789`, no `18791`, no\nbridge" in (
        packet_text
    )
    assert "does not approve `18789` or `18791`" in packet_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in packet_text
    assert "`D11=D11_INSUFFICIENT`" in packet_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in packet_text
    assert "does not approve broker submit readiness" in packet_text
    assert "does not\napprove live trading readiness" in packet_text
    assert "D11.76 does not rerun IBKR" in packet_text
    assert "does not execute evidence capture" in packet_text
    assert "does not run\nbroker/TWS/API/network/runtime commands" in packet_text
    assert "does not access credentials or environment files" in packet_text
    assert "does not\nperform package capture, replay, scoring" in packet_text

    assert (
        "### D11.76 Fresh Regular-Session LOCAL_MAC Read-Only Evidence "
        "Capture Operator Run Record" in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD`"
        in map_text
    )
    assert "`source_commit=6db5d0b2f1cc47679dd194c846206a0dde36693c`" in (
        map_text
    )
    assert "`d11_75_run_status=COMPLETED_BY_OPERATOR`" in map_text
    assert (
        "`d11_76_evidence_classification=FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE`"
        in map_text
    )
    assert "not provider approval" in map_text
    assert "`LOCAL_MAC_ONLY`" in map_text
    assert "`DIRECT_MAC_TERMINAL`" in map_text
    assert "endpoint candidate `127.0.0.1:7497`" in map_text
    assert "`latest_candle_timestamp=2026-06-29T14:00:00+00:00`" in (
        map_text
    )
    assert "`lag_minutes=20.295228566666665`" in map_text
    assert "`freshness_classification=clean`" in map_text
    assert "`d11_countable=true`" in map_text
    assert "`d11_primary_eligible=false`" in map_text
    assert "`d11_primary_candidate_status=candidate`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11=D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in map_text
    assert "no account query, position query, portfolio\nquery" in map_text
    assert "does not rerun IBKR" in map_text
    assert "does not\nexecute evidence capture" in map_text
    assert (
        "`D11.77_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`"
        in map_text
    )


def test_d11_77_fresh_regular_session_adjudication_countable_but_insufficient() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_77_fresh_regular_session_read_only_evidence_capture_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.77 Fresh Regular-Session Read-Only Evidence Capture "
        "Adjudication" in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `1afb04c64275e039d598203dcbcc40b3b2ef9bc2`"
        in packet_text
    )
    assert (
        "`d11_76_evidence_classification` | "
        "`FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE`"
        in packet_text
    )
    assert (
        "`d11_77_decision` | "
        "`D11_75_76_CLEAN_COUNTABLE_EVIDENCE_ADJUDICATED_COUNTABLE_BUT_INSUFFICIENT_TO_APPROVE_PRIMARY_ELIGIBILITY`"
        in packet_text
    )
    assert "`d11_77_evidence_collected` | `false`" in packet_text
    assert (
        "`d11_77_executable_broker_tws_api_network_runtime_command_run` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_behavior_changed` | `false`"
        in packet_text
    )
    assert "`d11_77_commit_performed` | `false`" in packet_text
    assert "`d11_77_push_performed` | `false`" in packet_text
    assert "`d11_75_76_all_symbols_freshness_classification` | `clean`" in (
        packet_text
    )
    assert "`d11_75_76_all_symbols_d11_countable` | `true`" in packet_text
    assert "`d11_75_76_all_symbols_failure_reason` | ``" in packet_text
    assert (
        "`d11_75_76_all_symbols_d11_primary_eligible` | `false`"
        in packet_text
    )
    assert (
        "`d11_75_76_all_symbols_d11_primary_candidate_status` | `candidate`"
        in packet_text
    )
    assert (
        "`ibkr_primary_eligibility_after_d11_77` | `NOT_APPROVED`"
        in packet_text
    )
    assert "`d11_status_after_d11_77` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status_after_d11_77` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`package_capture` | `false`" in packet_text
    assert "`replay` | `false`" in packet_text
    assert "`scoring` | `false`" in packet_text
    assert "`candidate_generation` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`D11.78_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION`"
        in packet_text
    )

    assert "This evidence basis is countability evidence" in packet_text
    assert "It is not, by itself, provider\napproval evidence" in packet_text
    assert "Countability is not the same as provider approval" in packet_text
    assert (
        "the D11.75/D11.76 evidence is clean\nand countable, but the same rows"
        in packet_text
    )
    assert "Clean `d11_countable=true` evidence is not enough" in packet_text

    for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"):
        assert f"| `{symbol}` | `true` | `ibkr_market_data_candidate` |" in (
            packet_text
        )
    assert packet_text.count("`2026-06-29T14:00:00+00:00`") >= 5
    assert packet_text.count("`2026-06-29T12:20:17.713714+00:00`") >= 5
    assert packet_text.count("`2026-06-29T14:20:17.713714+00:00`") >= 5
    assert packet_text.count("`20.295228566666665`") >= 5
    assert packet_text.count("`clean`") >= 6
    assert (
        packet_text.count(
            "| `true` | `false` | `candidate` | `15Min` | "
            "`COUNTABLE_BUT_PRIMARY_ELIGIBILITY_NOT_APPROVED` |"
        )
        == 5
    )

    assert "d11_75_76_clean_countable_evidence=ACCEPTED" in packet_text
    assert "IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED" in packet_text
    assert "D11=D11_INSUFFICIENT" in packet_text
    assert "UNIT_12=UNIT_12_BLOCKED" in packet_text
    assert "D11.77 does not open Unit 12" in packet_text
    assert "does not approve broker\nsubmit readiness" in packet_text
    assert "does not approve live trading readiness" in packet_text

    for blocker in (
        "`d11_primary_candidate_status=candidate`",
        "`d11_primary_eligible=false`",
        "`ibkr_market_data_candidate` remains `broker_coupled=true`",
        "`candidate_can_count_for_d11` remains unsatisfied",
        "`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`",
    ):
        assert blocker in packet_text

    for marker in (
        "no_account_query",
        "no_position_query",
        "no_portfolio_query",
        "no_balance_query",
        "no_margin_query",
        "no_buying_power_query",
        "no_order_placement",
        "no_order_modification",
        "no_order_cancellation",
        "no_order_routing",
        "no_execution_authority",
        "no_package_capture",
        "no_replay",
        "no_scoring",
        "no_candidate_generation",
        "no_unit_12_opening",
        "no_vps_runtime_systemd_timer_mutation",
        "no_vps_endpoint",
        "no_18789",
        "no_18791",
        "no_bridge",
        "no_tunnel",
        "no_proxy",
    ):
        assert f"`{marker}`" in packet_text

    assert "D11.77 collected no evidence" in packet_text
    assert "D11.77 ran no executable broker/TWS/API/network/\nruntime command" in (
        packet_text
    )
    assert "D11.77 performed no commit and no push" in packet_text
    assert "Still-Unapproved Authorities" in packet_text
    assert "IBKR primary eligibility" in packet_text
    assert "D11 completion" in packet_text
    assert "broker submit readiness" in packet_text
    assert "live trading readiness" in packet_text

    assert (
        "### D11.77 Fresh Regular-Session Read-Only Evidence Capture "
        "Adjudication" in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`"
        in map_text
    )
    assert "`source_commit=1afb04c64275e039d598203dcbcc40b3b2ef9bc2`" in (
        map_text
    )
    assert (
        "`D11_75_76_CLEAN_COUNTABLE_EVIDENCE_ADJUDICATED_COUNTABLE_BUT_INSUFFICIENT_TO_APPROVE_PRIMARY_ELIGIBILITY`"
        in map_text
    )
    assert "`freshness_classification=clean`" in map_text
    assert "`d11_countable=true`" in map_text
    assert "`d11_primary_eligible=false`" in map_text
    assert "`d11_primary_candidate_status=candidate`" in map_text
    assert "`broker_coupled=true`" in map_text
    assert "`candidate_can_count_for_d11`" in map_text
    assert "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`" in map_text
    assert "`D11=D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in map_text
    assert "no account query, position\nquery" in map_text
    assert "collected no evidence" in map_text
    assert "performed no\ncommit or push" in map_text
    assert (
        "`D11.78_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION`"
        in map_text
    )


def test_d11_78_primary_eligibility_criteria_remediation_ready_for_final_adjudication() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_78_primary_eligibility_criteria_and_candidate_status_remediation.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "D11.78 Source-Controlled IBKR Primary Eligibility Criteria And "
        "Candidate Status Remediation" in packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `b3ecf93cc49e45787c963930a14a4b7256cc9122`"
        in packet_text
    )
    assert (
        "`d11_77_decision` | "
        "`D11_75_76_CLEAN_COUNTABLE_EVIDENCE_ADJUDICATED_COUNTABLE_BUT_INSUFFICIENT_TO_APPROVE_PRIMARY_ELIGIBILITY`"
        in packet_text
    )
    assert (
        "`d11_77_blocker_basis` | "
        "`d11_primary_candidate_status_candidate; d11_primary_eligible_false; "
        "broker_coupled_true; candidate_can_count_for_d11_unsatisfied; "
        "separate_vps_read_only_freshness_proof_required_before_primary_eligibility_unrevised`"
        in packet_text
    )
    assert (
        "`d11_75_76_evidence_classification` | "
        "`FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE`"
        in packet_text
    )
    assert "`d11_75_76_symbol_scope` | `AAPL,MSFT,NVDA,TSLA,MSTR`" in packet_text
    assert "`d11_75_76_timeframe` | `15Min`" in packet_text
    assert "`d11_75_76_lookback_minutes` | `120`" in packet_text
    assert (
        "`d11_75_76_latest_candle_timestamp_all_symbols` | "
        "`2026-06-29T14:00:00+00:00`" in packet_text
    )
    assert (
        "`d11_75_76_requested_start_all_symbols` | "
        "`2026-06-29T12:20:17.713714+00:00`" in packet_text
    )
    assert (
        "`d11_75_76_requested_end_all_symbols` | "
        "`2026-06-29T14:20:17.713714+00:00`" in packet_text
    )
    assert (
        "`d11_75_76_lag_minutes_all_symbols` | `20.295228566666665`"
        in packet_text
    )
    assert "`d11_75_76_freshness_classification_all_symbols` | `clean`" in (
        packet_text
    )
    assert "`d11_75_76_failure_reason_all_symbols` | ``" in packet_text
    assert "`d11_75_76_d11_countable_all_symbols` | `true`" in packet_text
    assert (
        "`d11_78_decision` | "
        "`IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REMEDIATED_READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION`"
        in packet_text
    )
    assert "`d11_78_evidence_collected` | `false`" in packet_text
    assert (
        "`d11_78_executable_broker_tws_api_network_runtime_command_run` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`d11_78_commit_performed` | `false`" in packet_text
    assert "`d11_78_push_performed` | `false`" in packet_text
    assert (
        "`ibkr_primary_eligibility_through_d11_78` | "
        "`NOT_APPROVED_READY_FOR_FINAL_ADJUDICATION_ONLY`" in packet_text
    )
    assert "`d11_status_through_d11_78` | `D11_INSUFFICIENT`" in packet_text
    assert "`unit_12_status_through_d11_78` | `UNIT_12_BLOCKED`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert "`account_order_execution_authority` | `false`" in packet_text
    assert "`package_capture` | `BLOCKED`" in packet_text
    assert "`replay` | `BLOCKED`" in packet_text
    assert "`scoring` | `BLOCKED`" in packet_text
    assert "`candidate_generation` | `BLOCKED`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`D11.79_FINAL_IBKR_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION`"
        in packet_text
    )

    for blocker in (
        "`d11_primary_candidate_status=candidate`",
        "`d11_primary_eligible=false`",
        "`broker_coupled=true`",
        "`candidate_can_count_for_d11` unsatisfied",
        "`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`",
    ):
        assert blocker in packet_text

    for status in (
        "`REMEDIATED_FOR_FINAL_ADJUDICATION`",
        "`REMEDIATED_FOR_READ_ONLY_MARKET_DATA_QUALIFICATION_ONLY`",
        "`NARROWED_AND_RETIRED_FOR_THIS_LOCAL_MAC_ONLY_PATH`",
    ):
        assert status in packet_text

    assert "artifact row status remains `candidate`" in packet_text
    assert (
        "`READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION`" in packet_text
    )
    assert "D11.78 does not change production provider-selection runtime metadata" in (
        packet_text
    )
    assert "`d11_primary_eligible=false` in the diagnostic artifact is" in (
        packet_text
    )
    assert (
        "candidate_can_count_for_d11=D11_75_76_CLEAN_COUNTABLE_LOCAL_MAC_READ_ONLY_EVIDENCE_SATISFIES_PROVIDER_READINESS_FOR_FINAL_ADJUDICATION"
        in packet_text
    )
    assert "D11.78 narrows and retires" in packet_text
    assert "for this LOCAL_MAC-only read-only market-data provider qualification path" in (
        packet_text
    )
    assert "D11.78 does not approve IBKR primary eligibility" in packet_text
    assert "D11 remains insufficient through D11.78" in packet_text
    assert "Unit 12 remains blocked through D11.78" in packet_text
    assert "D11.78 collected no evidence" in packet_text
    assert "D11.78 ran no executable broker/TWS/API/network/\nruntime command" in (
        packet_text
    )
    assert "D11.78 performed no commit and no push" in packet_text
    assert "No D11.77 criteria blocker remains as a blocker to final adjudication" in (
        packet_text
    )

    for authority in (
        "broker submit readiness `NOT_APPROVED`",
        "live trading readiness `NOT_APPROVED`",
        "account authority none",
        "order authority none",
        "execution authority none",
        "package capture blocked",
        "replay blocked",
        "scoring blocked",
        "candidate generation blocked",
        "strategy behavior changes blocked",
        "risk behavior changes blocked",
        "execution behavior changes blocked",
        "scheduler behavior changes blocked",
        "credential or environment-file changes blocked",
        "production runtime configuration changes blocked",
        "VPS runtime/systemd/timer mutation blocked",
        "Unit 12 not opened by D11.78",
    ):
        assert authority in packet_text

    assert (
        "### D11.78 Source-Controlled IBKR Primary Eligibility Criteria And "
        "Candidate Status Remediation" in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION`"
        in map_text
    )
    assert "`source_commit=b3ecf93cc49e45787c963930a14a4b7256cc9122`" in (
        map_text
    )
    assert (
        "`IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REMEDIATED_READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION`"
        in map_text
    )
    assert "`freshness_classification=clean`" in map_text
    assert "`d11_countable=true`" in map_text
    assert "Artifact row status remains `candidate`" in map_text
    assert "`d11_primary_eligible=false`" in map_text
    assert "`broker_coupled=true`" in map_text
    assert "`candidate_can_count_for_d11` is revised" in map_text
    assert "separate VPS read-only freshness proof criterion is\nnarrowed and retired" in (
        map_text
    )
    assert (
        "`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED_READY_FOR_FINAL_ADJUDICATION_ONLY`"
        in map_text
    )
    assert "`D11=D11_INSUFFICIENT`" in map_text
    assert "`UNIT_12=UNIT_12_BLOCKED`" in map_text
    assert "`broker_submit_readiness=NOT_APPROVED`" in map_text
    assert "`live_trading_readiness=NOT_APPROVED`" in map_text
    assert "collected no evidence" in map_text
    assert "ran no executable broker/TWS/API/network/runtime\ncommand" in map_text
    assert "changed no production provider-selection runtime behavior" in map_text
    assert (
        "`D11.79_FINAL_IBKR_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION`"
        in map_text
    )


def test_d11_79_final_primary_eligibility_and_d11_closure_adjudication() -> None:
    packet_path = Path(
        "docs/ibkr_market_data_d11_79_final_primary_eligibility_and_d11_closure_adjudication.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "D11.79 Final IBKR Primary Eligibility And D11 Closure Adjudication" in (
        packet_text
    )
    assert (
        "`classification` | "
        "`IBKR_D11_FINAL_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`source_commit` | `74c2cad5087214aff9cc7b108900547f250d28cd`"
        in packet_text
    )
    assert (
        "`d11_75_76_evidence_classification` | "
        "`FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE`"
        in packet_text
    )
    assert (
        "`d11_77_decision` | "
        "`D11_75_76_CLEAN_COUNTABLE_EVIDENCE_ADJUDICATED_COUNTABLE_BUT_INSUFFICIENT_TO_APPROVE_PRIMARY_ELIGIBILITY`"
        in packet_text
    )
    assert (
        "`d11_78_decision` | "
        "`IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REMEDIATED_READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION`"
        in packet_text
    )
    assert (
        "`d11_79_decision` | "
        "`IBKR_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_APPROVED_AND_D11_CLOSED`"
        in packet_text
    )
    assert "`d11_79_evidence_collected` | `false`" in packet_text
    assert (
        "`d11_79_executable_broker_tws_api_network_runtime_command_run` | `false`"
        in packet_text
    )
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`d11_79_commit_performed` | `false`" in packet_text
    assert "`d11_79_push_performed` | `false`" in packet_text
    assert (
        "`ibkr_primary_eligibility_after_d11_79` | "
        "`APPROVED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`"
        in packet_text
    )
    assert (
        "`d11_status_after_d11_79` | "
        "`D11_CLOSED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`"
        in packet_text
    )
    assert (
        "`unit_12_status_after_d11_79` | "
        "`UNIT_12_NOT_OPENED_BOUNDARY_REVIEW_REQUIRED`" in packet_text
    )
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert "`account_authority` | `NONE`" in packet_text
    assert "`order_authority` | `NONE`" in packet_text
    assert "`execution_authority` | `NONE`" in packet_text
    assert "`package_capture` | `NOT_AUTHORIZED`" in packet_text
    assert "`replay` | `NOT_AUTHORIZED`" in packet_text
    assert "`scoring` | `NOT_AUTHORIZED`" in packet_text
    assert "`candidate_generation` | `NOT_AUTHORIZED`" in packet_text
    assert (
        "`strategy_risk_execution_changes` | `NOT_AUTHORIZED`"
        in packet_text
    )
    assert "`unit_12_implementation` | `NOT_AUTHORIZED`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_SOURCE_CONTROLLED_REPLAY_PACKAGE_PREREQUISITE_AND_UNIT_12_BOUNDARY_REVIEW`"
        in packet_text
    )

    for symbol in ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR"):
        assert f"| `{symbol}` | `true` | `15Min` | `120` |" in packet_text
    assert packet_text.count("`2026-06-29T14:00:00+00:00`") >= 5
    assert packet_text.count("`2026-06-29T12:20:17.713714+00:00`") >= 5
    assert packet_text.count("`2026-06-29T14:20:17.713714+00:00`") >= 5
    assert packet_text.count("`20.295228566666665`") >= 5
    assert packet_text.count("`clean`") >= 5
    assert packet_text.count("| `20.295228566666665` | `clean` | `` | `true` |") == 5

    for remediation in (
        "Candidate status is a diagnostic artifact status",
        "The false value is a non-self-approval marker",
        "`broker_coupled=true` | Narrowed as compatible only with read-only market-data qualification",
        "`candidate_can_count_for_d11` unsatisfied | Remediated for the D11.75/D11.76 clean countable LOCAL_MAC evidence bundle only",
        "Narrowed and retired for this LOCAL_MAC-only path; no VPS endpoint is approved",
    ):
        assert remediation in packet_text

    assert (
        "IBKR_PRIMARY_ELIGIBILITY=APPROVED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY"
        in packet_text
    )
    assert (
        "D11=D11_CLOSED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY"
        in packet_text
    )
    assert "UNIT_12=UNIT_12_NOT_OPENED_BOUNDARY_REVIEW_REQUIRED" in packet_text
    assert "D11.79 does not implement Unit 12 and does not open Unit 12" in (
        packet_text
    )
    assert "broker_submit_readiness=NOT_APPROVED" in packet_text
    assert "live_trading_readiness=NOT_APPROVED" in packet_text
    assert "account_authority=NONE" in packet_text
    assert "order_authority=NONE" in packet_text
    assert "execution_authority=NONE" in packet_text
    assert "package_capture=NOT_AUTHORIZED" in packet_text
    assert "replay=NOT_AUTHORIZED" in packet_text
    assert "scoring=NOT_AUTHORIZED" in packet_text
    assert "candidate_generation=NOT_AUTHORIZED" in packet_text
    assert "strategy_risk_execution_changes=NOT_AUTHORIZED" in packet_text
    assert "LOCAL_MAC `127.0.0.1:7497` remains a LOCAL_MAC process-context endpoint" in (
        packet_text
    )
    assert "It is\nnot VPS `127.0.0.1:7497`" in packet_text
    assert "approves no VPS endpoint, no `18789`, no `18791`, no bridge" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `NOT_AUTHORIZED` |",
        "| Risk behavior changes | `NOT_AUTHORIZED` |",
        "| Execution behavior changes | `NOT_AUTHORIZED` |",
        "| Scheduler behavior changes | `NOT_AUTHORIZED` |",
        "| Credential or environment-file changes | `NOT_AUTHORIZED` |",
        "| Production runtime configuration changes | `NOT_AUTHORIZED` |",
        "| Production provider-selection runtime behavior changes | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert "D11.79 collected no evidence" in packet_text
    assert "D11.79 ran no executable broker/TWS/API/network/\nruntime command" in (
        packet_text
    )
    assert "D11.79 performed no commit and no push" in packet_text
    assert "No D11 blocker remains after D11.79" in packet_text
    assert "This next gate is a review/authorization prerequisite only" in (
        packet_text
    )
    assert "must not itself\nperform package capture, replay, scoring" in packet_text

    assert (
        "### D11.79 Final IBKR Primary Eligibility And D11 Closure "
        "Adjudication" in map_text
    )
    assert str(packet_path) in map_text
    assert (
        "`IBKR_D11_FINAL_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION`"
        in map_text
    )
    assert "`source_commit=74c2cad5087214aff9cc7b108900547f250d28cd`" in (
        map_text
    )
    assert (
        "`IBKR_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_APPROVED_AND_D11_CLOSED`"
        in map_text
    )
    assert "`freshness_classification=clean`" in map_text
    assert "`d11_countable=true`" in map_text
    assert "`read_only=true`" in map_text
    assert (
        "`IBKR_PRIMARY_ELIGIBILITY=APPROVED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`"
        in map_text
    )
    assert (
        "`D11=D11_CLOSED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`"
        in map_text
    )
    assert "`UNIT_12=UNIT_12_NOT_OPENED_BOUNDARY_REVIEW_REQUIRED`" in map_text
    assert "`broker_submit_readiness=NOT_APPROVED`" in map_text
    assert "`live_trading_readiness=NOT_APPROVED`" in map_text
    assert "`account_authority=NONE`" in map_text
    assert "`order_authority=NONE`" in map_text
    assert "`execution_authority=NONE`" in map_text
    assert "`package_capture=NOT_AUTHORIZED`" in map_text
    assert "`replay=NOT_AUTHORIZED`" in map_text
    assert "`scoring=NOT_AUTHORIZED`" in map_text
    assert "`candidate_generation=NOT_AUTHORIZED`" in map_text
    assert "LOCAL_MAC `127.0.0.1:7497` remains a\nLOCAL_MAC process-context endpoint" in (
        map_text
    )
    assert "approves no VPS endpoint, no `18789`, no `18791`, no bridge" in (
        map_text
    )
    assert "collected no evidence" in map_text
    assert "ran no executable broker/TWS/API/network/runtime\ncommand" in map_text
    assert "implemented no Unit\n12" in map_text
    assert (
        "`POST_D11_SOURCE_CONTROLLED_REPLAY_PACKAGE_PREREQUISITE_AND_UNIT_12_BOUNDARY_REVIEW`"
        in map_text
    )


def test_post_d11_replay_package_prerequisite_and_unit_12_boundary_review() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_prerequisite_and_unit_12_boundary_review.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "Post-D11 Replay Package Prerequisite And Unit 12 Boundary Review" in (
        packet_text
    )
    assert (
        "POST_D11_SOURCE_CONTROLLED_REPLAY_PACKAGE_PREREQUISITE_AND_UNIT_12_BOUNDARY_REVIEW"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_SOURCE_CONTROLLED_REPLAY_PACKAGE_PREREQUISITE_AND_UNIT_12_BOUNDARY_REVIEW`"
        in packet_text
    )
    assert (
        "`source_commit` | `a09ce5e477d568907f32f43732dd5dd2e6741eda`"
        in packet_text
    )
    assert (
        "`d11_79_decision` | "
        "`IBKR_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_APPROVED_AND_D11_CLOSED`"
        in packet_text
    )
    assert (
        "`ibkr_primary_eligibility_after_d11_79` | "
        "`APPROVED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`"
        in packet_text
    )
    assert (
        "`d11_status_after_d11_79` | "
        "`D11_CLOSED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`"
        in packet_text
    )
    assert (
        "`unit_12_status_after_d11_79` | "
        "`UNIT_12_NOT_OPENED_BOUNDARY_REVIEW_REQUIRED`" in packet_text
    )
    assert (
        "`post_d11_decision` | "
        "`POST_D11_REPLAY_PACKAGE_AND_UNIT_12_BOUNDARY_REVIEW_COMPLETED_READY_FOR_SOURCE_CONTROLLED_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert "`package_capture_executed` | `false`" in packet_text
    assert "`replay_executed` | `false`" in packet_text
    assert "`scoring_executed` | `false`" in packet_text
    assert "`candidate_generation_executed` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`unit_12_implemented_or_opened` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert "`account_authority` | `NONE`" in packet_text
    assert "`order_authority` | `NONE`" in packet_text
    assert "`execution_authority` | `NONE`" in packet_text
    assert "`package_capture_execution` | `NOT_AUTHORIZED`" in packet_text
    assert "`replay_execution` | `NOT_AUTHORIZED`" in packet_text
    assert "`scoring_execution` | `NOT_AUTHORIZED`" in packet_text
    assert (
        "`candidate_generation_execution` | `NOT_AUTHORIZED`"
        in packet_text
    )
    assert "`strategy_risk_execution_changes` | `BLOCKED`" in packet_text
    assert (
        "`scheduler_runtime_service_systemd_timer_changes` | `BLOCKED`"
        in packet_text
    )
    assert "`credential_environment_changes` | `BLOCKED`" in packet_text
    assert "`vps_endpoint_approval` | `NOT_APPROVED`" in packet_text
    assert "`bridge_tunnel_proxy_approval` | `NOT_APPROVED`" in packet_text
    assert "`unit_12_implementation` | `NOT_OPENED`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )

    assert "D11 closure unlocks only a governance transition" in packet_text
    assert "It does not convert any other\nGate D, package, replay" in packet_text
    assert "D11 closure does not unlock:" in packet_text
    for denied in (
        "package capture execution",
        "replay execution",
        "scoring execution",
        "candidate generation execution",
        "broker submit readiness",
        "live trading readiness",
        "account authority",
        "order authority",
        "execution authority",
        "VPS endpoint approval",
        "`18789` or `18791` endpoint approval",
        "bridge, tunnel, or proxy approval",
        "Unit 12 opening or implementation",
    ):
        assert denied in packet_text

    for boundary in (
        "| Read-only market-data provider qualification | Approved by D11.79",
        "| Package capture authorization | Not authorized by D11.79 or this gate",
        "| Replay authorization | Not authorized.",
        "| Scoring authorization | Not authorized.",
        "| Candidate generation authorization | Not authorized.",
        "| Unit 12 implementation | Not opened and not implemented.",
        "| Broker submit/live trading authority | Not approved.",
    ):
        assert boundary in packet_text

    assert "PACKAGE_CAPTURE_EXECUTION=NOT_AUTHORIZED" in packet_text
    assert "REPLAY_EXECUTION=NOT_AUTHORIZED" in packet_text
    assert "SCORING_EXECUTION=NOT_AUTHORIZED" in packet_text
    assert "CANDIDATE_GENERATION_EXECUTION=NOT_AUTHORIZED" in packet_text
    assert "UNIT_12_IMPLEMENTATION=NOT_OPENED" in packet_text
    assert "Before any future package capture can be authorized" in packet_text
    assert "eligible `run_id` selection rule from scheduled runtime evidence only" in (
        packet_text
    )
    assert "D13 market-session eligibility requirement" in packet_text
    assert "explicit `order_state.json` exclusion" in packet_text
    assert "Before any future Unit 12 work can be authorized" in packet_text
    assert "completed package evidence exists and is source-control reviewed" in (
        packet_text
    )
    assert "package ledger or equivalent inventory evidence" in packet_text
    assert "broker submit readiness and live trading readiness remain separate gates" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This gate performed no package capture, no replay, no scoring" in (
        packet_text
    )
    assert "broker/TWS/API/network/runtime action" in packet_text
    assert "no IBKR connection" in packet_text
    assert "no\nTWS/Gateway inspection" in packet_text
    assert "no Unit 12 implementation, and no\nUnit 12 opening" in packet_text
    assert "This gate performed no commit and no push" in packet_text
    assert "No concrete blocker prevents drafting the next source-controlled package" in (
        packet_text
    )
    assert (
        "This next gate is still an authorization packet only unless it explicitly\n"
        "authorizes a later operator run" in packet_text
    )

    assert (
        "### Post-D11 Replay Package Prerequisite And Unit 12 Boundary Review"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=a09ce5e477d568907f32f43732dd5dd2e6741eda`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_AND_UNIT_12_BOUNDARY_REVIEW_COMPLETED_READY_FOR_SOURCE_CONTROLLED_AUTHORIZATION_PACKET`"
        in map_text
    )
    assert "D11 closure unlocks only a governance transition" in map_text
    assert "It does not unlock package capture execution" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`replay_execution=NOT_AUTHORIZED`" in map_text
    assert "`scoring_execution=NOT_AUTHORIZED`" in map_text
    assert "`candidate_generation_execution=NOT_AUTHORIZED`" in map_text
    assert "`unit_12_implementation=NOT_OPENED`" in map_text
    assert "eligible `run_id` selection from scheduled runtime\nevidence only" in (
        map_text
    )
    assert "completed and reviewed package evidence" in map_text
    assert "no package capture, no replay, no scoring" in map_text
    assert "no\ncandidate generation" in map_text
    assert "no broker/TWS/API/network/runtime action" in map_text
    assert "no Unit 12\nimplementation" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`" in map_text
    )
    assert "still\nan authorization packet only" in map_text


def test_post_d11_replay_package_capture_authorization_packet() -> None:
    packet_path = Path("docs/post_d11_replay_package_capture_authorization_packet.md")
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert "Post-D11 Replay Package Capture Authorization Packet" in packet_text
    assert "POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET" in packet_text
    assert (
        "`classification` | `POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `cd9768f1ae39f91ef513bf1ab68fe1c737e6bd2f`"
        in packet_text
    )
    assert (
        "`d11_79_decision` | "
        "`IBKR_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_APPROVED_AND_D11_CLOSED`"
        in packet_text
    )
    assert (
        "`post_d11_boundary_decision` | "
        "`POST_D11_REPLAY_PACKAGE_AND_UNIT_12_BOUNDARY_REVIEW_COMPLETED_READY_FOR_SOURCE_CONTROLLED_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`package_capture_authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_OPERATOR_RUN`"
        in packet_text
    )
    assert (
        "`authorized_future_operator_run_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN`" in packet_text
    )
    assert "`authorized_future_source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert (
        "`approved_provider_scope` | "
        "`IBKR_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`"
        in packet_text
    )
    assert "`package_capture_executed_by_this_gate` | `false`" in packet_text
    assert "`replay_executed_by_this_gate` | `false`" in packet_text
    assert "`scoring_executed_by_this_gate` | `false`" in packet_text
    assert (
        "`candidate_generation_executed_by_this_gate` | `false`"
        in packet_text
    )
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`unit_12_implemented_or_opened` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert "`broker_submit_readiness` | `NOT_APPROVED`" in packet_text
    assert "`live_trading_readiness` | `NOT_APPROVED`" in packet_text
    assert "`account_authority` | `NONE`" in packet_text
    assert "`order_authority` | `NONE`" in packet_text
    assert "`execution_authority` | `NONE`" in packet_text
    assert "`replay_execution` | `NOT_AUTHORIZED`" in packet_text
    assert "`scoring_execution` | `NOT_AUTHORIZED`" in packet_text
    assert (
        "`candidate_generation_execution` | `NOT_AUTHORIZED`"
        in packet_text
    )
    assert "`strategy_risk_execution_changes` | `BLOCKED`" in packet_text
    assert (
        "`scheduler_runtime_service_systemd_timer_changes` | `BLOCKED`"
        in packet_text
    )
    assert "`credential_environment_changes` | `BLOCKED`" in packet_text
    assert (
        "`production_runtime_provider_selection_runtime_changes` | `BLOCKED`"
        in packet_text
    )
    assert "`vps_endpoint_approval` | `NOT_APPROVED`" in packet_text
    assert "`endpoint_18789_18791_approval` | `NOT_APPROVED`" in packet_text
    assert "`bridge_tunnel_proxy_approval` | `NOT_APPROVED`" in packet_text
    assert "`unit_12_implementation` | `NOT_OPENED`" in packet_text
    assert (
        "`next_permissible_gate` | `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN`"
        in packet_text
    )

    assert "does not itself\nrun the operator gate" in packet_text
    assert "does\nnot infer package-capture execution authority from D11 closure alone" in (
        packet_text
    )
    assert "The future operator run is `LOCAL_MAC_ONLY`" in packet_text
    assert "no VPS endpoint approval" in packet_text
    assert "no `18789` approval" in packet_text
    assert "no `18791` approval" in packet_text
    assert "no bridge approval" in packet_text
    assert "no tunnel approval" in packet_text
    assert "no proxy approval" in packet_text
    assert "no broker/TWS/API/network traffic" in packet_text

    for requirement in (
        "exactly one `run_id`",
        "aligned JSONL event stream",
        "terminal completion event",
        "aligned `last_run_report.json`",
        "explicit `order_state.json` exclusion",
        "package identity and layout metadata",
        "manifest, hash, integrity, persistence, and finalized immutability evidence",
        "expected source commit",
        "clean worktree before capture",
        "D13 market-session eligibility result",
        "no existing package directory",
        "no mixed `run_id`",
        "no hash mismatch",
        "no path traversal",
        "no overwrite attempt",
        "no future/leaked/post-decision evidence",
        "no broker/order-state binding",
    ):
        assert requirement in packet_text

    for artifact in (
        "| `run_id` | Exactly one selected run identifier. |",
        "| `source_commit` | Commit used for the operator run. |",
        "| `worktree_before` | Must be clean. |",
        "| `worktree_after` | Must be clean or explicitly explained without mutation. |",
        "| `jsonl_path` | `logs/{run_id}.jsonl` or source-controlled LOCAL_MAC equivalent. |",
        "| `last_run_report_alignment` | Must prove report `run_id` equals JSONL `run_id`. |",
        "| `terminal_event` | Terminal completion event must be present. |",
        "| `d13_eligibility` | Must pass or fail closed. |",
        "| `manifest_schema_version` | Required if manifest is emitted. |",
        "| `manifest_canonical_run_id` | Must equal selected `run_id`. |",
        "| `section_provenance` | Required for every package section. |",
        "| `section_redaction_status` | Required for every package section. |",
        "| `package_sha256` | Required package or artifact hash. |",
        "| `integrity_validation_result` | Must pass or fail closed. |",
        "| `finalized_immutable_marker` | Required. |",
        "| `no_overwrite_attestation` | Required. |",
        "| `order_state_handling` | Excluded, absent, or not-applicable only unless later gate authorizes binding. |",
    ):
        assert artifact in packet_text

    assert "PACKAGE_CAPTURE_OPERATOR_RUN_FAILED_CLOSED" in packet_text
    assert "REPLAY_EXECUTION=NOT_AUTHORIZED" in packet_text
    assert "SCORING_EXECUTION=NOT_AUTHORIZED" in packet_text
    assert "CANDIDATE_GENERATION_EXECUTION=NOT_AUTHORIZED" in packet_text
    assert "UNIT_12_IMPLEMENTATION=NOT_OPENED" in packet_text
    assert "broker_submit_readiness=NOT_APPROVED" in packet_text
    assert "live_trading_readiness=NOT_APPROVED" in packet_text
    assert "account_authority=NONE" in packet_text
    assert "order_authority=NONE" in packet_text
    assert "execution_authority=NONE" in packet_text
    assert "vps_endpoint_approval=NOT_APPROVED" in packet_text
    assert "endpoint_18789_18791_approval=NOT_APPROVED" in packet_text
    assert "bridge_tunnel_proxy_approval=NOT_APPROVED" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This authorization packet performed no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "broker/TWS/API/network/runtime action" in packet_text
    assert "no IBKR\nconnection" in packet_text
    assert "no TWS/Gateway inspection" in packet_text
    assert "no Unit 12 implementation, and no\nUnit 12 opening" in packet_text
    assert "This authorization packet performed no commit and no push" in (
        packet_text
    )

    assert "### Post-D11 Replay Package Capture Authorization Packet" in map_text
    assert str(packet_path) in map_text
    assert "`source_commit=cd9768f1ae39f91ef513bf1ab68fe1c737e6bd2f`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_OPERATOR_RUN`"
        in map_text
    )
    assert "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN`" in map_text
    assert "does not execute package capture" in map_text
    assert "The future operator run is authorized only as `LOCAL_MAC_ONLY`" in (
        map_text
    )
    assert "`IBKR_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`" in map_text
    assert "no VPS endpoint, no VPS\n`127.0.0.1:7497`" in map_text
    assert "no `18789`, no `18791`, no bridge, no tunnel, no proxy" in map_text
    assert "one bounded replay package for\nexactly one `run_id`" in map_text
    assert "aligned JSONL event stream" in map_text
    assert "D13 market-session\neligibility" in map_text
    assert "`replay_execution=NOT_AUTHORIZED`" in map_text
    assert "`scoring_execution=NOT_AUTHORIZED`" in map_text
    assert "`candidate_generation_execution=NOT_AUTHORIZED`" in map_text
    assert "`unit_12_implementation=NOT_OPENED`" in map_text
    assert "performed no package capture, no replay, no scoring" in map_text
    assert "no Unit 12\nimplementation" in map_text


def test_post_d11_replay_package_capture_operator_run_preflight_blocker_record() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_operator_run_preflight_blocker_record.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Operator Run Preflight Blocker Record"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_PREFLIGHT_BLOCKER_RECORD`"
        in packet_text
    )
    assert (
        "`source_commit` | `917af7e67e20faf8494afabe425716efd6ae3ae7`"
        in packet_text
    )
    assert (
        "`authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_OPERATOR_RUN`"
        in packet_text
    )
    assert (
        "`authorized_operator_run_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN`" in packet_text
    )
    assert "`authorized_source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert (
        "`operator_run_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKED_PENDING_LOCAL_ARTIFACTS_AND_AUTHORITY_SURFACE_REMEDIATION`"
        in packet_text
    )
    assert "`local_head` | `917af7e67e20faf8494afabe425716efd6ae3ae7`" in (
        packet_text
    )
    assert "`origin_main` | `917af7e67e20faf8494afabe425716efd6ae3ae7`" in (
        packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert "`logs_directory` | `MISSING`" in packet_text
    assert "`run_reports_directory` | `MISSING`" in packet_text
    assert "`replay_packages_directory` | `MISSING`" in packet_text
    assert "`last_run_report_json` | `ABSENT`" in packet_text
    assert "`order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`" in packet_text
    assert "`package_capture_executed` | `false`" in packet_text
    assert "`replay_executed` | `false`" in packet_text
    assert "`scoring_executed` | `false`" in packet_text
    assert "`candidate_generation_executed` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`package_capture_orchestrator_behavior_changed` | `false`" in (
        packet_text
    )
    assert "`unit_12_implemented_or_opened` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN`"
        in packet_text
    )

    for blocker in (
        "No eligible `run_id` can be selected.",
        "No local package target state exists.",
        "Authorization/source-context mismatch.",
        "Current package orchestrator production VPS path is not authorized",
        "`order_state.json` remains absent and excluded.",
    ):
        assert blocker in packet_text

    assert "logs=MISSING" in packet_text
    assert "run_reports=MISSING" in packet_text
    assert "last_run_report.json=ABSENT" in packet_text
    assert "`logs/<run_id>.jsonl` exists" in packet_text
    assert "`run_reports/<run_id>.json` or `last_run_report.json` exists" in (
        packet_text
    )
    assert "capture readiness reproved" in packet_text
    assert "capture --run-id <run_id> --expected-commit <commit> --authorize-vps-package-write" in (
        packet_text
    )
    assert (
        "package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write"
        in packet_text
    )
    assert "does not authorize VPS execution" in packet_text
    assert "No such VPS execution gate is authorized here" in packet_text
    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "must remain absent/excluded/not-bound" in packet_text
    assert "This blocker\nrecord does not authorize order-state binding" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Package-capture/orchestrator production behavior changes | `BLOCKED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This blocker record performed no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no\ncandidate generation" in packet_text
    assert "broker/TWS/API/network/runtime action" in packet_text
    assert "no IBKR\nconnection" in packet_text
    assert "no TWS/Gateway inspection" in packet_text
    assert "no package-capture/orchestrator\nproduction behavior change" in (
        packet_text
    )
    assert "This blocker record performed no commit and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture Operator Run Preflight Blocker Record"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=917af7e67e20faf8494afabe425716efd6ae3ae7`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKED_PENDING_LOCAL_ARTIFACTS_AND_AUTHORITY_SURFACE_REMEDIATION`"
        in map_text
    )
    assert "`logs=MISSING`" in map_text
    assert "`run_reports=MISSING`" in map_text
    assert "`replay_packages=MISSING`" in map_text
    assert "`last_run_report.json=ABSENT`" in map_text
    assert "`order_state.json=ABSENT`" in map_text
    assert "approved `authorized_source_context=LOCAL_MAC_ONLY`" in map_text
    assert "`--execution-mode vps`" in map_text
    assert "did not\nauthorize a VPS execution gate" in map_text
    assert "`replay_execution=NOT_AUTHORIZED`" in map_text
    assert "`scoring_execution=NOT_AUTHORIZED`" in map_text
    assert "`candidate_generation_execution=NOT_AUTHORIZED`" in map_text
    assert "`unit_12_implementation=NOT_OPENED`" in map_text
    assert "performed no package capture" in map_text
    assert "no package-\ncapture/orchestrator production behavior change" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN`"
        in map_text
    )


def test_post_d11_replay_package_capture_operator_run_blocker_remediation_plan() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_operator_run_blocker_remediation_plan.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Operator Run Blocker Remediation Plan"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN`"
        in packet_text
    )
    assert (
        "`source_commit` | `ae9469c9de44f275b25d61f80d88667648434e00`"
        in packet_text
    )
    assert (
        "`prior_blocker_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKED_PENDING_LOCAL_ARTIFACTS_AND_AUTHORITY_SURFACE_REMEDIATION`"
        in packet_text
    )
    assert (
        "`remediation_plan_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN_COMPLETED_READY_FOR_REMEDIATION_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`artifact_remediation_separated_from_authority_surface_remediation` | `true`"
        in packet_text
    )
    assert "`implementation_selected_by_this_gate` | `false`" in packet_text
    assert "`remediation_executed` | `false`" in packet_text
    assert "`package_capture_executed` | `false`" in packet_text
    assert "`replay_executed` | `false`" in packet_text
    assert "`scoring_executed` | `false`" in packet_text
    assert "`candidate_generation_executed` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`package_capture_orchestrator_behavior_changed` | `false`" in (
        packet_text
    )
    assert "`unit_12_implemented_or_opened` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET`"
        in packet_text
    )

    for blocker in (
        "Missing local artifact blocker",
        "Authority-surface mismatch blocker",
        "`order_state` exclusion",
        "`logs=MISSING`",
        "`run_reports=MISSING`",
        "`replay_packages=MISSING`",
        "`last_run_report.json=ABSENT`",
    ):
        assert blocker in packet_text

    assert "Artifact remediation is separate from authority-surface remediation" in (
        packet_text
    )
    assert "Prior market-session/runtime artifact gate" in packet_text
    assert "Deterministic existing-artifact discovery" in packet_text
    assert "Layout-only remediation" in packet_text
    assert "does not authorize directory creation" in packet_text
    assert "source-control\ncriteria and tests first" in packet_text

    assert "Authority-surface remediation is separate from artifact remediation" in (
        packet_text
    )
    assert "capture --run-id <run_id> --expected-commit <commit> --authorize-vps-package-write" in (
        packet_text
    )
    assert (
        "package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write"
        in packet_text
    )
    assert "LOCAL_MAC package-capture command surface" in packet_text
    assert "Bounded VPS execution authorization path" in packet_text
    assert "Legacy-name adjudication path" in packet_text
    assert (
        "`--authorize-vps-package-write` must be treated as authority-bearing"
        in packet_text
    )
    assert "This plan does not authorize VPS execution" in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not authorize order-state binding" in packet_text
    assert "order-state reads" in packet_text
    assert "order-state writes" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production package-capture/orchestrator behavior changes | `NOT_AUTHORIZED_BY_THIS_GATE` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This remediation plan performed no remediation" in packet_text
    assert "no package capture, no replay" in packet_text
    assert "no scoring, no candidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no IBKR connection" in packet_text
    assert "no VPS action" in packet_text
    assert "no\nproduction package-capture/orchestrator behavior change" in (
        packet_text
    )
    assert "This remediation plan performed no commit and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture Operator Run Blocker Remediation Plan"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=ae9469c9de44f275b25d61f80d88667648434e00`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN_COMPLETED_READY_FOR_REMEDIATION_AUTHORIZATION_PACKET`"
        in map_text
    )
    assert "separates artifact remediation from authority-surface remediation" in (
        map_text
    )
    assert "separate prior market-session/runtime artifact gate" in map_text
    assert "already-existing deterministic outputs" in map_text
    assert "does not authorize artifact creation" in map_text
    assert "deferred to a later governed\npackage-capture execution" in map_text
    assert "`--authorize-vps-package-write` is authority-bearing" in map_text
    assert "`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`replay_execution=NOT_AUTHORIZED`" in map_text
    assert "`scoring_execution=NOT_AUTHORIZED`" in map_text
    assert "`candidate_generation_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`production_package_capture_orchestrator_behavior_changes=NOT_AUTHORIZED_BY_THIS_GATE`"
        in map_text
    )
    assert "`unit_12_implementation=NOT_OPENED`" in map_text
    assert "The plan performed no remediation" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_operator_run_blocker_remediation_authorization_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_operator_run_blocker_remediation_authorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Operator Run Blocker Remediation Authorization Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `8faf4258e373a467753377150dfcee764483d1c8`"
        in packet_text
    )
    assert (
        "`remediation_authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET_APPROVED_FOR_SOURCE_CONTROLLED_REMEDIATION_EDIT_GATE`"
        in packet_text
    )
    assert (
        "`authorized_future_edit_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET`"
        in packet_text
    )
    assert (
        "`authorized_remediation_lanes` | "
        "`artifact_path_remediation_and_authority_surface_remediation`"
        in packet_text
    )
    assert (
        "`recommended_next_edit_priority` | "
        "`LOCAL_MAC_COMMAND_SURFACE_RECONCILIATION_PLUS_ARTIFACT_DISCOVERY_LAYOUT_CRITERIA`"
        in packet_text
    )
    assert "`bounded_vps_execution_authorized` | `false`" in packet_text
    assert (
        "`legacy_name_adjudication_authorized_only_by_later_source_controlled_remediation` | `true`"
        in packet_text
    )
    assert "`remediation_performed_by_this_gate` | `false`" in packet_text
    assert "`package_capture_executed` | `false`" in packet_text
    assert "`replay_executed` | `false`" in packet_text
    assert "`scoring_executed` | `false`" in packet_text
    assert "`candidate_generation_executed` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`package_capture_orchestrator_behavior_changed` | `false`" in (
        packet_text
    )
    assert "`unit_12_implemented_or_opened` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET`"
        in packet_text
    )

    assert "Artifact-path remediation" in packet_text
    assert "Authority-surface remediation" in packet_text
    assert "`order_state` exclusion" in packet_text
    assert "approves both lanes for the\nnext edit packet" in packet_text
    assert "LOCAL_MAC command-surface reconciliation plus artifact discovery/layout criteria" in (
        packet_text
    )
    assert "must not execute package capture" in packet_text

    for artifact_fact in (
        "logs=MISSING",
        "run_reports=MISSING",
        "replay_packages=MISSING",
        "last_run_report.json=ABSENT",
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` or `last_run_report.json` exists",
        "`replay_packages/<run_id>` absent",
        "capture readiness reproved",
    ):
        assert artifact_fact in packet_text

    assert "may not\ncreate `logs`, `run_reports`, `replay_packages`" in packet_text
    assert "may not discover artifacts by running runtime commands" in packet_text
    assert "may not\nconvert absent artifacts into an eligible `run_id`" in packet_text

    assert "LOCAL_MAC_ONLY" in packet_text
    assert "--authorize-vps-package-write" in packet_text
    assert "--execution-mode vps" in packet_text
    assert "bounded VPS execution authorization path remains not selected" in (
        packet_text
    )
    assert "bounded VPS execution remains unauthorized" in packet_text
    assert (
        "`--authorize-vps-package-write` remains authority-bearing until a later"
        in packet_text
    )
    assert "Legacy\nname adjudication is allowed only by later source-controlled remediation" in (
        packet_text
    )

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not authorize order-state binding" in packet_text
    assert "order-state reads" in packet_text
    assert "order-state writes" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production package-capture/orchestrator behavior changes | `NOT_AUTHORIZED_BY_THIS_GATE` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This authorization packet performed no remediation" in packet_text
    assert "no package capture" in packet_text
    assert "no\nreplay, no scoring, no candidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime\naction" in packet_text
    assert "no VPS action" in packet_text
    assert "no\nproduction package-capture/orchestrator behavior change" in (
        packet_text
    )
    assert "This authorization packet performed no commit and no push" in (
        packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture Operator Run Blocker Remediation Authorization Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=8faf4258e373a467753377150dfcee764483d1c8`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET_APPROVED_FOR_SOURCE_CONTROLLED_REMEDIATION_EDIT_GATE`"
        in map_text
    )
    assert "`artifact-path remediation` and `authority-surface remediation`" in (
        map_text
    )
    assert "does not authorize remediation execution" in map_text
    assert "does not authorize artifact creation" in map_text
    assert "bounded VPS execution" in map_text
    assert "`logs=MISSING`" in map_text
    assert "`run_reports=MISSING`" in map_text
    assert "`replay_packages=MISSING`" in map_text
    assert "`last_run_report.json=ABSENT`" in map_text
    assert "`--authorize-vps-package-write` remains authority-bearing" in map_text
    assert "Bounded VPS\nexecution remains unauthorized" in map_text
    assert "`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`replay_execution=NOT_AUTHORIZED`" in map_text
    assert "`scoring_execution=NOT_AUTHORIZED`" in map_text
    assert "`candidate_generation_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`production_package_capture_orchestrator_behavior_changes=NOT_AUTHORIZED_BY_THIS_GATE`"
        in map_text
    )
    assert "`unit_12_implementation=NOT_OPENED`" in map_text
    assert "The authorization packet performed no remediation" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_operator_run_blocker_remediation_edit_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_operator_run_blocker_remediation_edit_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Operator Run Blocker Remediation Edit Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `340f26fce661c0a36179d3a7473dafe8a209d086`"
        in packet_text
    )
    assert (
        "`authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET_APPROVED_FOR_SOURCE_CONTROLLED_REMEDIATION_EDIT_GATE`"
        in packet_text
    )
    assert (
        "`remediation_edit_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert "`artifact_path_remediation_criteria_source_controlled` | `true`" in (
        packet_text
    )
    assert "`authority_surface_remediation_implemented` | `false`" in (
        packet_text
    )
    assert "`local_mac_command_surface_reconciled` | `false`" in packet_text
    assert (
        "`concrete_blocker` | "
        "`NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE`"
        in packet_text
    )
    assert "`remediation_execution_performed` | `false`" in packet_text
    assert "`package_capture_executed` | `false`" in packet_text
    assert "`replay_executed` | `false`" in packet_text
    assert "`scoring_executed` | `false`" in packet_text
    assert "`candidate_generation_executed` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert "`vps_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert (
        "`production_package_capture_orchestrator_behavior_changed` | `false`"
        in packet_text
    )
    assert "`unit_12_action` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET`"
        in packet_text
    )

    assert "supports `tmp_path_test` and `vps` execution modes" in packet_text
    assert "No inspected source exposes a\nsafe LOCAL_MAC package-capture execution mode" in (
        packet_text
    )
    assert "without production package-capture/orchestrator behavior\nchanges" in (
        packet_text
    )

    for criterion in (
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` or `last_run_report.json` exists",
        "any available report is aligned to the selected `run_id`",
        "the selected JSONL has a terminal completion event",
        "D13 market-session eligibility is evaluated from already-existing artifacts",
        "`replay_packages/<run_id>` is absent",
        "capture readiness is reproved from already-existing artifacts",
        "no mixed `run_id` evidence appears",
        "no stale report evidence appears",
        "no path traversal appears",
        "no overwrite attempt appears",
        "no future, leaked, or post-decision evidence appears",
        "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND` is preserved",
    ):
        assert criterion in packet_text

    for prohibition in (
        "creation of `logs/`",
        "creation of `run_reports/`",
        "creation of `replay_packages/`",
        "creation of `last_run_report.json`",
        "creation of `order_state.json`",
        "selection of `run_id` from absent artifacts",
        "use of `replay_packages` as proof of runtime artifact availability",
    ):
        assert prohibition in packet_text

    assert "Authority-surface remediation is blocked" in packet_text
    assert "`--authorize-vps-package-write` remains authority-bearing" in (
        packet_text
    )
    assert "Bounded VPS execution remains unauthorized" in packet_text
    assert "does not provide a safe local execution mode to expose" in packet_text
    assert "The current operator `capture` path must not be treated as LOCAL_MAC-safe" in (
        packet_text
    )
    assert "does not add, rename, or execute any operator command" in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or use" in (
        packet_text
    )
    assert "`order_state` must not be used to unblock package\ncapture" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production package-capture/orchestrator behavior changes | `BLOCKED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This edit packet performed no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no\ncandidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no production\npackage-capture/orchestrator behavior change" in (
        packet_text
    )
    assert "Unit 12 action" in packet_text
    assert "This edit packet performed no commit and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture Operator Run Blocker Remediation Edit Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=340f26fce661c0a36179d3a7473dafe8a209d086`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in map_text
    )
    assert "`logs/<run_id>.jsonl` exists" in map_text
    assert "`run_reports/<run_id>.json` or\n`last_run_report.json` exists" in (
        map_text
    )
    assert "no `logs/`, no `run_reports/`, no\n`replay_packages/`" in map_text
    assert (
        "`NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE`"
        in map_text
    )
    assert "`--authorize-vps-package-write` remains authority-bearing" in map_text
    assert "bounded VPS execution remains unauthorized" in map_text
    assert "current `capture` path must\nnot be treated as LOCAL_MAC-safe" in map_text
    assert "`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`replay_execution=NOT_AUTHORIZED`" in map_text
    assert "`scoring_execution=NOT_AUTHORIZED`" in map_text
    assert "`candidate_generation_execution=NOT_AUTHORIZED`" in map_text
    assert "`production_package_capture_orchestrator_behavior_changes=BLOCKED`" in (
        map_text
    )
    assert "`unit_12_implementation=NOT_OPENED`" in map_text
    assert "The edit packet performed no package capture" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_local_mac_command_surface_design_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_local_mac_command_surface_design_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture LOCAL_MAC Command Surface Design Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `e869845e47f3982b7c74b8151665616964d9af97`"
        in packet_text
    )
    assert (
        "`prior_edit_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`concrete_blocker` | "
        "`NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE`"
        in packet_text
    )
    assert (
        "`design_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET_COMPLETED_READY_FOR_IMPLEMENTATION_EDIT_PACKET`"
        in packet_text
    )
    assert "`local_mac_command_surface_design_completed` | `true`" in packet_text
    assert "`production_command_surface_changes_implemented` | `false`" in (
        packet_text
    )
    assert "`package_capture_executed` | `false`" in packet_text
    assert "`replay_executed` | `false`" in packet_text
    assert "`scoring_executed` | `false`" in packet_text
    assert "`candidate_generation_executed` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert "`vps_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert (
        "`production_package_capture_orchestrator_behavior_changed` | `false`"
        in packet_text
    )
    assert "`unit_12_action` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET`"
        in packet_text
    )

    assert "capture-local --run-id <run_id> --expected-commit <commit> --authorize-local-package-write" in (
        packet_text
    )
    assert "no `--authorize-vps-package-write` requirement for LOCAL_MAC package capture" in (
        packet_text
    )
    assert "no delegation through `--execution-mode vps`" in packet_text
    assert "no real `/opt` VPS reads or writes" in packet_text
    assert "LOCAL_MAC package writing and VPS package writing must remain separate" in (
        packet_text
    )
    assert "`--authorize-vps-package-write` remains\nauthority-bearing" in (
        packet_text
    )
    assert "bounded VPS execution remains `NOT_AUTHORIZED`" in packet_text

    for design_option in (
        "Expose existing local execution mode",
        "Add new local execution mode",
        "Bypass VPS orchestration through a local-only package writer path",
        "Block",
    ):
        assert design_option in packet_text

    for criterion in (
        "no artifact creation occurs",
        "no `run_id` is selected from absent artifacts",
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` or `last_run_report.json` exists",
        "the report is aligned to the selected `run_id`",
        "the selected JSONL has a terminal completion event",
        "D13 market-session eligibility is evaluated from already-existing artifacts",
        "`replay_packages/<run_id>` is absent",
        "`replay_packages` is treated as an output target only",
        "expected commit is checked",
        "worktree is checked",
    ):
        assert criterion in packet_text

    for prohibited_creation in (
        "`logs/`",
        "`run_reports/`",
        "`replay_packages/`",
        "`last_run_report.json`",
        "`order_state.json`",
        "any package artifact",
    ):
        assert prohibited_creation in packet_text

    assert "package capture execution remains `NOT_AUTHORIZED`" in packet_text
    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "must not read, write, create, bind, validate, infer,\nor use `order_state`" in (
        packet_text
    )
    assert "must not infer broker-visible state" in packet_text

    for allowed in (
        "operator command surface",
        "local-only package-capture preflight gating",
        "local-only package output path control",
        "local-only tests and docs",
        "local-only command naming or parser wiring",
    ):
        assert allowed in packet_text

    for prohibited in (
        "strategy behavior",
        "risk behavior",
        "execution behavior",
        "broker behavior",
        "provider-selection runtime behavior",
        "scheduler/runtime/service/systemd/timer behavior",
        "credentials or environment files",
        "Unit 12",
        "replay behavior",
        "scoring behavior",
        "candidate-generation behavior",
    ):
        assert prohibited in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production package-capture/orchestrator behavior changes in this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This design packet performed no implementation" in packet_text
    assert "no package capture, no replay" in packet_text
    assert "no scoring, no candidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no\nproduction package-capture/orchestrator behavior change" in (
        packet_text
    )
    assert "Unit 12 action" in packet_text
    assert "This design packet performed no commit and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture LOCAL_MAC Command Surface Design Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=e869845e47f3982b7c74b8151665616964d9af97`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET_COMPLETED_READY_FOR_IMPLEMENTATION_EDIT_PACKET`"
        in map_text
    )
    assert "distinct LOCAL_MAC package-capture command surface" in map_text
    assert "must not\nrequire `--authorize-vps-package-write`" in map_text
    assert "must not delegate through\n`--execution-mode vps`" in map_text
    assert "`--authorize-vps-package-write` as authority-bearing" in map_text
    assert "Bounded VPS execution remains\n`NOT_AUTHORIZED`" in map_text
    assert "Package capture execution remains `NOT_AUTHORIZED`" in map_text
    assert "no artifact creation" in map_text
    assert "no `run_id`\nselection from absent artifacts" in map_text
    assert "`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`" in map_text
    assert "must not change strategy behavior" in map_text
    assert "The design packet performed no implementation" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET`"
        in map_text
    )


def test_gate_d_operator_capture_local_command_surface_is_local_only() -> None:
    from tools.ops import gate_d_market_session_operator as operator

    parser = operator.build_parser()
    parsed = parser.parse_args(
        [
            "capture-local",
            "--run-id",
            "run_1",
            "--expected-commit",
            "abc123",
            "--authorize-local-package-write",
        ]
    )

    assert parsed.command == "capture-local"
    assert parsed.run_id == "run_1"
    assert parsed.expected_commit == "abc123"
    assert parsed.authorize_local_package_write is True
    assert not hasattr(parsed, "authorize_vps_package_write")
    assert parsed.func is operator.capture_local

    try:
        parser.parse_args(
            [
                "capture-local",
                "--run-id",
                "run_1",
                "--expected-commit",
                "abc123",
                "--authorize-vps-package-write",
            ]
        )
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError(
            "capture-local must not accept --authorize-vps-package-write"
        )


def test_gate_d_operator_capture_local_fails_closed_without_artifacts(
    tmp_path: Path, capsys: object
) -> None:
    from tools.ops import gate_d_market_session_operator as operator

    expected_commit = "abc123"
    calls: list[tuple[str, ...]] = []

    def fake_runner(
        argv: tuple[str, ...], timeout: int | None = None
    ) -> operator.CommandResult:
        del timeout
        calls.append(tuple(argv))
        if argv[:4] == ("git", "-C", str(tmp_path), "rev-parse"):
            if argv[4:] == ("--abbrev-ref", "HEAD"):
                return operator.CommandResult(argv=argv, returncode=0, stdout="main\n")
            if argv[4:] == ("HEAD",):
                return operator.CommandResult(
                    argv=argv, returncode=0, stdout=f"{expected_commit}\n"
                )
        if argv[:4] == ("git", "-C", str(tmp_path), "status"):
            return operator.CommandResult(argv=argv, returncode=0, stdout="")
        if argv[:3] == ("timeout", "15", "git"):
            return operator.CommandResult(
                argv=argv,
                returncode=0,
                stdout=f"{expected_commit}\trefs/heads/main\n",
            )
        if argv == ("findmnt", "-no", "OPTIONS", "/"):
            return operator.CommandResult(argv=argv, returncode=0, stdout="rw,local\n")
        if argv == ("systemctl", "is-active", "openclaw.timer"):
            return operator.CommandResult(argv=argv, returncode=0, stdout="active\n")
        if argv == ("systemctl", "is-enabled", "openclaw.timer"):
            return operator.CommandResult(argv=argv, returncode=0, stdout="enabled\n")
        if argv == ("systemctl", "is-active", "openclaw.service"):
            return operator.CommandResult(argv=argv, returncode=3, stdout="inactive\n")
        if argv == ("systemctl", "is-failed", "openclaw.service"):
            return operator.CommandResult(argv=argv, returncode=3, stdout="inactive\n")
        if argv[:3] == ("systemctl", "show", "openclaw.service"):
            return operator.CommandResult(
                argv=argv,
                returncode=0,
                stdout="NRestarts=0\nResult=success\nExecMainStatus=0\n",
            )
        return operator.CommandResult(argv=argv, returncode=127, stderr="unexpected")

    args = SimpleNamespace(
        repo_root=str(tmp_path),
        run_id="run_1",
        expected_commit=expected_commit,
        authorize_local_package_write=True,
    )

    result = operator.capture_local(args, runner=fake_runner)
    output = capsys.readouterr().out

    assert result == 1
    assert "BLOCK jsonl_exists: run_1" in output
    assert "BLOCK run_report_exists: run_1" in output
    assert "PASS package_directory_absent:" in output
    assert "PASS local_package_write_authorized:" in output
    assert "PASS vps_package_write_authority_not_used:" in output
    assert "PASS vps_execution_mode_not_used:" in output
    assert "PASS order_state_excluded_not_bound:" in output
    assert "PACKAGE_CAPTURE_EXECUTED=false" in output
    assert "REPLAY_EXECUTED=false" in output
    assert "SCORING_EXECUTED=false" in output
    assert "CANDIDATE_GENERATION_EXECUTED=false" in output
    assert "VPS_ACTION=false" in output
    assert "ORDER_STATE_BOUND=false" in output
    assert (
        f"FINAL_CLASSIFICATION={operator.LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED}"
        in output
    )
    assert not any("--execution-mode" in part for call in calls for part in call)
    assert not any("package_execution_orchestrator" in part for call in calls for part in call)


def test_post_d11_replay_package_capture_local_mac_command_surface_implementation_edit_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_local_mac_command_surface_implementation_edit_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture LOCAL_MAC Command Surface Implementation Edit Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `69d4a5232bfc4b8a8b3f37ed6210df24d90eaa48`"
        in packet_text
    )
    assert (
        "`design_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET_COMPLETED_READY_FOR_IMPLEMENTATION_EDIT_PACKET`"
        in packet_text
    )
    assert (
        "`implementation_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET_COMPLETED_READY_FOR_OPERATOR_RUN_REAUTHORIZATION_PACKET`"
        in packet_text
    )
    assert "`local_mac_command_surface_added` | `capture-local`" in packet_text
    assert (
        "`local_authorization_flag` | `--authorize-local-package-write`"
        in packet_text
    )
    assert "`vps_authorization_flag_required_for_local_path` | `false`" in (
        packet_text
    )
    assert "`vps_authorization_flag_accepted_as_local_authority` | `false`" in (
        packet_text
    )
    assert "`delegates_through_execution_mode_vps` | `false`" in packet_text
    assert "`package_capture_executed` | `false`" in packet_text
    assert "`replay_executed` | `false`" in packet_text
    assert "`scoring_executed` | `false`" in packet_text
    assert "`candidate_generation_executed` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert "`vps_action` | `false`" in packet_text
    assert (
        "`runtime_broker_vps_scheduler_systemd_credential_action` | `false`"
        in packet_text
    )
    assert (
        "`production_provider_selection_runtime_behavior_changed` | `false`"
        in packet_text
    )
    assert "`strategy_risk_execution_behavior_changed` | `false`" in packet_text
    assert "`broker_behavior_changed` | `false`" in packet_text
    assert "`unit_12_action` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET`"
        in packet_text
    )

    assert "capture-local --run-id <run_id> --expected-commit <commit> --authorize-local-package-write" in (
        packet_text
    )
    assert "does not require `--authorize-vps-package-write`" in packet_text
    assert "does not accept `--authorize-vps-package-write` as LOCAL_MAC authority" in (
        packet_text
    )
    assert "does not delegate through `--execution-mode vps`" in packet_text
    assert "does not call `package_execution_orchestrator.main`" in packet_text
    assert "does not write packages" in packet_text
    assert "does not execute package capture" in packet_text
    assert "existing VPS `capture` path remains isolated and unchanged" in (
        packet_text
    )

    for check in (
        "HEAD equals `--expected-commit`",
        "worktree is clean",
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` or `last_run_report.json` exists",
        "`replay_packages/<run_id>` is absent",
        "capture readiness is reproved from already-existing artifacts",
        "`--authorize-local-package-write` is supplied",
        "VPS package-write authority is not used",
        "`--execution-mode vps` is not used",
        "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND` is preserved",
    ):
        assert check in packet_text

    for no_artifact in (
        "It does not create `logs/`",
        "`run_reports/`",
        "`replay_packages/`",
        "`last_run_report.json`",
        "`order_state.json`",
        "or any package\nartifact",
    ):
        assert no_artifact in packet_text

    assert "LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_READY_REAUTHORIZATION_REQUIRED" in (
        packet_text
    )
    assert "This classification is readiness for a later reauthorization packet only" in (
        packet_text
    )
    assert "LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED" in packet_text
    assert (
        "NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE"
        in packet_text
    )
    assert "remediated at the command-surface level" in packet_text
    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or\nuse `order_state`" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This implementation edit packet performed no package capture" in (
        packet_text
    )
    assert "no replay, no\nscoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no\nVPS action" in packet_text
    assert "Unit 12 action" in packet_text
    assert "This implementation edit packet performed no commit and no push" in (
        packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture LOCAL_MAC Command Surface Implementation Edit Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=69d4a5232bfc4b8a8b3f37ed6210df24d90eaa48`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET_COMPLETED_READY_FOR_OPERATOR_RUN_REAUTHORIZATION_PACKET`"
        in map_text
    )
    assert "`capture-local --run-id <run_id> --expected-commit <commit> --authorize-local-package-write`" in (
        map_text
    )
    assert "does not require or accept\n`--authorize-vps-package-write`" in (
        map_text
    )
    assert "does not delegate\nthrough `--execution-mode vps`" in map_text
    assert "`LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_READY_REAUTHORIZATION_REQUIRED`" in (
        map_text
    )
    assert "`LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`bounded_vps_execution=NOT_AUTHORIZED`" in map_text
    assert "The implementation edit packet performed no package capture" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_operator_run_reauthorization_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_operator_run_reauthorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Operator Run Reauthorization Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `53a836ac91e3d9fd11cf9b9368e1eab6128657e4`"
        in packet_text
    )
    assert (
        "`implementation_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET_COMPLETED_READY_FOR_OPERATOR_RUN_REAUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`reauthorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_LOCAL_MAC_OPERATOR_RUN`"
        in packet_text
    )
    assert (
        "`authorized_future_operator_run_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert "`authorized_future_source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`authorized_operator_run_count` | `1`" in packet_text
    assert "`package_capture_executed_by_this_gate` | `false`" in packet_text
    assert "`replay_executed_by_this_gate` | `false`" in packet_text
    assert "`scoring_executed_by_this_gate` | `false`" in packet_text
    assert "`candidate_generation_executed_by_this_gate` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert "`vps_action` | `false`" in packet_text
    assert "`unit_12_action` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in packet_text
    )

    authorized_command = (
        ".venv-312/bin/python tools/ops/gate_d_market_session_operator.py "
        "capture-local --run-id <run_id> --expected-commit "
        "53a836ac91e3d9fd11cf9b9368e1eab6128657e4 "
        "--authorize-local-package-write"
    )
    assert authorized_command in packet_text
    assert "The operator must not substitute the existing VPS `capture` path" in (
        packet_text
    )
    assert "must not supply `--authorize-vps-package-write`" in packet_text
    assert "must not use\n`--execution-mode vps`" in packet_text
    assert "must not delegate to\n`package_execution_orchestrator.main`" in (
        packet_text
    )
    assert (
        "concrete `run_id` only after preflight proves\nalready-existing eligible LOCAL_MAC artifacts"
        in packet_text
    )

    for criterion in (
        "source context is `LOCAL_MAC_ONLY`",
        "branch is `main`",
        "LOCAL_MAC HEAD equals\n  `53a836ac91e3d9fd11cf9b9368e1eab6128657e4`",
        "LOCAL_MAC `origin/main` equals\n  `53a836ac91e3d9fd11cf9b9368e1eab6128657e4`",
        "worktree is clean",
        "explicit `run_id` is supplied",
        "supplied `run_id` is a safe path segment",
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` exists or `last_run_report.json` alignment\n  exists",
        "available report evidence is aligned to the selected `run_id`",
        "capture readiness is reproved from already-existing artifacts",
        "`replay_packages/<run_id>` is absent before package capture",
        "no mixed `run_id` evidence appears",
        "no stale report evidence appears",
        "no path traversal appears",
        "no overwrite attempt appears",
        "no future, leaked, or post-decision evidence appears",
        "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND` is preserved",
        "no `order_state` read, write, creation, binding, validation, inference, or\n  use occurs",
        "no `--authorize-vps-package-write` appears",
        "no `--execution-mode vps` appears",
        "no `package_execution_orchestrator.main` delegation occurs",
        "no VPS action occurs",
        "no broker/TWS/API/network/runtime/scheduler/systemd/timer/service action\n  occurs",
        "no replay, scoring, candidate generation, or Unit 12 action occurs",
    ):
        assert criterion in packet_text

    for artifact_requirement in (
        "exactly one concrete `run_id`",
        "aligned `logs/<run_id>.jsonl`",
        "aligned `run_reports/<run_id>.json` or aligned `last_run_report.json`",
        "terminal completion evidence",
        "no existing `replay_packages/<run_id>` directory",
        "source commit and `run_id` alignment evidence",
        "does not create `logs/`",
        "`run_reports/`",
        "`replay_packages/`",
        "`last_run_report.json`",
        "`order_state.json`",
        "or any package\nartifact",
        "`replay_packages` remains an output target only",
    ):
        assert artifact_requirement in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "must not read, write, create, bind, validate,\ninfer, or use `order_state`" in (
        packet_text
    )
    assert "must not infer broker-visible order state" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution in this gate | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production broker behavior changes | `BLOCKED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This reauthorization packet is a source-controlled approval packet only" in (
        packet_text
    )
    assert "This reauthorization packet performed no package capture" in packet_text
    assert "no replay, no\nscoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no\nVPS action" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "This reauthorization packet performed no commit and no push" in (
        packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture Operator Run Reauthorization Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=53a836ac91e3d9fd11cf9b9368e1eab6128657e4`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_LOCAL_MAC_OPERATOR_RUN`"
        in map_text
    )
    assert authorized_command in map_text
    assert "performs no\npackage capture" in map_text
    assert "`order_state.json` read" not in packet_text
    assert "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`" in map_text
    assert "no `order_state` read, write,\ncreation, binding, validation, inference, or use is authorized" in map_text
    assert "`package_capture_execution_in_this_gate=NOT_AUTHORIZED`" in map_text
    assert "`bounded_vps_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_operator_run_expected_commit_alignment_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_operator_run_expected_commit_alignment_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Operator Run Expected Commit Alignment Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_EXPECTED_COMMIT_ALIGNMENT_PACKET`"
        in packet_text
    )
    assert (
        "`audit_head` | `72de932896ca33327efe23f17de055ddf5f9162d`"
        in packet_text
    )
    assert (
        "`audit_origin_main` | `72de932896ca33327efe23f17de055ddf5f9162d`"
        in packet_text
    )
    assert "`audit_branch` | `main`" in packet_text
    assert "`audit_worktree` | `clean`" in packet_text
    assert (
        "`historical_reauthorization_source_commit` | "
        "`53a836ac91e3d9fd11cf9b9368e1eab6128657e4`"
        in packet_text
    )
    assert (
        "`implementation_basis_commit` | "
        "`53a836ac91e3d9fd11cf9b9368e1eab6128657e4`"
        in packet_text
    )
    assert (
        "`implementation_packet_source_commit` | "
        "`69d4a5232bfc4b8a8b3f37ed6210df24d90eaa48`"
        in packet_text
    )
    assert (
        "`alignment_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_EXPECTED_COMMIT_ALIGNMENT_PACKET_COMPLETED_READY_FOR_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert "`static_replacement_expected_commit_hardcoded` | `false`" in (
        packet_text
    )
    assert (
        "`active_expected_commit_resolution` | "
        "`current_clean_branch_main_origin_aligned_head_at_bounded_run_preflight`"
        in packet_text
    )
    assert "`package_capture_executed_by_this_gate` | `false`" in packet_text
    assert "`replay_executed_by_this_gate` | `false`" in packet_text
    assert "`scoring_executed_by_this_gate` | `false`" in packet_text
    assert "`candidate_generation_executed_by_this_gate` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert "`vps_action` | `false`" in packet_text
    assert "`production_command_surface_changed` | `false`" in packet_text
    assert "`unit_12_action` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in packet_text
    )

    assert "--expected-commit 53a836ac91e3d9fd11cf9b9368e1eab6128657e4" in (
        packet_text
    )
    assert "The historical reauthorization packet remains a valid" in packet_text
    assert "must not proceed using the stale\nstatic expected commit" in packet_text
    assert (
        "remains the validated LOCAL_MAC\ncommand-surface implementation basis"
        in packet_text
    )
    assert "It is not the active operator-run\nexpected commit" in packet_text
    assert "No static replacement expected commit is hardcoded" in packet_text
    assert (
        "Replacing\n`53a836ac91e3d9fd11cf9b9368e1eab6128657e4` with\n`72de932896ca33327efe23f17de055ddf5f9162d`"
        in packet_text
    )

    command_template = (
        'EXPECTED_COMMIT="$(git rev-parse HEAD)"\n'
        '.venv-312/bin/python tools/ops/gate_d_market_session_operator.py '
        'capture-local --run-id <run_id> --expected-commit "$EXPECTED_COMMIT" '
        "--authorize-local-package-write"
    )
    assert command_template in packet_text

    for locked_field in (
        "branch=main",
        "local_head=<resolved_current_head>",
        "origin_main=<same_resolved_current_head>",
        "status_short=clean",
        "expected_commit=<same_resolved_current_head>",
    ):
        assert locked_field in packet_text

    for criterion in (
        "source context is `LOCAL_MAC_ONLY`",
        "branch is `main`",
        "worktree is clean",
        "LOCAL_MAC HEAD equals `origin/main`",
        "`expected_commit` equals current LOCAL_MAC HEAD and `origin/main` at\n  bounded-run preflight",
        "`branch=main` is printed and locked",
        "`local_head=<resolved_current_head>` is printed and locked",
        "`origin_main=<same_resolved_current_head>` is printed and locked",
        "`status_short=clean` is printed and locked",
        "`expected_commit=<same_resolved_current_head>` is printed and locked",
        "explicit concrete `run_id` is supplied only after preflight proves eligible\n  artifacts",
        "supplied `run_id` is a safe path segment",
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` exists or `last_run_report.json` alignment\n  exists",
        "available report evidence is aligned to the selected `run_id`",
        "capture readiness is reproved from already-existing artifacts",
        "`replay_packages/<run_id>` is absent before package capture",
        "no mixed `run_id` evidence appears",
        "no stale report evidence appears",
        "no path traversal appears",
        "no overwrite attempt appears",
        "no future, leaked, or post-decision evidence appears",
        "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND` is preserved",
        "no `order_state` read, write, creation, binding, validation, inference, or\n  use occurs",
        "no `--authorize-vps-package-write` appears",
        "no `--execution-mode vps` appears",
        "no `package_execution_orchestrator.main` delegation occurs",
        "no VPS action occurs",
        "no broker/TWS/API/network/runtime/scheduler/systemd/timer/service action\n  occurs",
        "no replay, scoring, candidate generation, or Unit 12 action occurs",
    ):
        assert criterion in packet_text

    for artifact_requirement in (
        "exactly one concrete `run_id`",
        "aligned `logs/<run_id>.jsonl`",
        "aligned `run_reports/<run_id>.json` or aligned `last_run_report.json`",
        "terminal completion evidence",
        "no existing `replay_packages/<run_id>` directory",
        "resolved current source commit and `run_id` alignment evidence",
        "does not create `logs/`",
        "`run_reports/`",
        "`replay_packages/`",
        "`last_run_report.json`",
        "`order_state.json`",
        "or any package\nartifact",
        "`replay_packages` remains an output target only",
    ):
        assert artifact_requirement in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "must not read, write, create, bind, validate,\ninfer, or use `order_state`" in (
        packet_text
    )
    assert "must not infer broker-visible order state" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution in this gate | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production command-surface changes | `BLOCKED` |",
        "| Production broker behavior changes | `BLOCKED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This expected-commit alignment packet is the active envelope correction" in (
        packet_text
    )
    assert "This alignment packet performed no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no\ncandidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no\nproduction command-surface change" in packet_text
    assert "Unit 12 action" in packet_text
    assert "This alignment packet performed no commit and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture Operator Run Expected Commit Alignment Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`local_head=72de932896ca33327efe23f17de055ddf5f9162d`" in map_text
    assert "`origin_main=72de932896ca33327efe23f17de055ddf5f9162d`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_EXPECTED_COMMIT_ALIGNMENT_PACKET_COMPLETED_READY_FOR_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in map_text
    )
    assert "static future command binding\n`--expected-commit 53a836ac91e3d9fd11cf9b9368e1eab6128657e4` is superseded" in (
        map_text
    )
    assert "not the active operator-run expected\ncommit" in map_text
    assert command_template in map_text
    assert "No\nstatic replacement expected commit is hardcoded" in map_text
    assert "`package_capture_execution_in_this_gate=NOT_AUTHORIZED`" in map_text
    assert "`production_command_surface_changes=BLOCKED`" in map_text
    assert "`bounded_vps_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_bounded_local_mac_operator_run_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_bounded_local_mac_operator_run_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Bounded LOCAL_MAC Operator Run Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `b06d8a4b96c9237911547cffa6bb31b1d8bf829d`"
        in packet_text
    )
    assert (
        "`origin_main` | `b06d8a4b96c9237911547cffa6bb31b1d8bf829d`"
        in packet_text
    )
    assert (
        "`expected_commit` | `b06d8a4b96c9237911547cffa6bb31b1d8bf829d`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`expected_commit_alignment_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_EXPECTED_COMMIT_ALIGNMENT_PACKET_COMPLETED_READY_FOR_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert (
        "`bounded_operator_run_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`concrete_blocker` | "
        "`NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_FOR_PACKAGE_CAPTURE`"
        in packet_text
    )
    assert "`logs_directory` | `ABSENT`" in packet_text
    assert "`run_reports_directory` | `ABSENT`" in packet_text
    assert "`replay_packages_directory` | `ABSENT`" in packet_text
    assert "`last_run_report_json` | `ABSENT`" in packet_text
    assert "`order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`" in packet_text
    assert "`log_candidates` | `NO_LOGS_DIR`" in packet_text
    assert "`run_report_candidates` | `NO_RUN_REPORTS_DIR`" in packet_text
    assert (
        "`replay_package_existing_targets` | `NO_REPLAY_PACKAGES_DIR`"
        in packet_text
    )
    assert "`last_run_report_status` | `NO_LAST_RUN_REPORT`" in packet_text
    assert (
        "`order_state_status` | `PASS_order_state_absent_excluded_not_bound`"
        in packet_text
    )
    assert "`eligible_run_id` | `NONE`" in packet_text
    assert (
        "`artifact_eligibility_result` | "
        "`FAILED_CLOSED_NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS`"
        in packet_text
    )
    assert "`package_capture_executed_by_this_gate` | `false`" in packet_text
    assert "`replay_executed_by_this_gate` | `false`" in packet_text
    assert "`scoring_executed_by_this_gate` | `false`" in packet_text
    assert "`candidate_generation_executed_by_this_gate` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert "`vps_action` | `false`" in packet_text
    assert "`production_command_surface_changed` | `false`" in packet_text
    assert "`unit_12_action` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET`"
        in packet_text
    )

    for inventory_line in (
        "logs=ABSENT",
        "run_reports=ABSENT",
        "replay_packages=ABSENT",
        "last_run_report.json=ABSENT",
        "order_state.json=ABSENT",
        "LOG CANDIDATES=NO_LOGS_DIR",
        "RUN_REPORT CANDIDATES=NO_RUN_REPORTS_DIR",
        "REPLAY_PACKAGE EXISTING TARGETS=NO_REPLAY_PACKAGES_DIR",
        "LAST_RUN_REPORT STATUS=NO_LAST_RUN_REPORT",
        "ORDER_STATE STATUS=PASS_order_state_absent_excluded_not_bound",
    ):
        assert inventory_line in packet_text

    assert (
        "Because `logs/<run_id>.jsonl` is absent, `run_reports/<run_id>.json` is absent"
        in packet_text
    )
    assert "`last_run_report.json` is absent" in packet_text
    assert "no concrete safe `run_id` can be selected" in packet_text
    assert "the bounded operator run must fail closed" in packet_text
    assert "NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_FOR_PACKAGE_CAPTURE" in (
        packet_text
    )
    assert "The `replay_packages` directory is absent" in packet_text
    assert (
        "That absence is not itself the\nblocking runtime-artifact criterion"
        in packet_text
    )
    assert "`replay_packages` is a package\noutput target" in packet_text

    for missing_criterion in (
        "concrete safe `run_id`",
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` exists or `last_run_report.json` alignment\n  exists",
        "report evidence aligned to selected `run_id`",
        "terminal completion evidence",
        "capture readiness reproved from existing artifacts",
    ):
        assert missing_criterion in packet_text

    for preserved_criterion in (
        "branch `main`",
        "clean worktree",
        "LOCAL_MAC HEAD equals `origin/main`",
        "`expected_commit` equals current LOCAL_MAC HEAD and `origin/main`",
        "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`",
        "no `--authorize-vps-package-write`",
        "no `--execution-mode vps`",
        "no `package_execution_orchestrator.main` delegation",
        "no VPS action",
        "no broker/TWS/API/network/runtime/scheduler/systemd/timer/service action",
        "no replay, scoring, candidate generation, or Unit 12 action",
    ):
        assert preserved_criterion in packet_text

    command_template = (
        'EXPECTED_COMMIT="$(git rev-parse HEAD)"\n'
        '.venv-312/bin/python tools/ops/gate_d_market_session_operator.py '
        'capture-local --run-id <run_id> --expected-commit "$EXPECTED_COMMIT" '
        "--authorize-local-package-write"
    )
    assert command_template in packet_text
    assert "This packet does not run that command because no eligible `run_id` exists" in (
        packet_text
    )

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or use\n`order_state`" in (
        packet_text
    )
    assert "does not infer broker-visible order state" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production command-surface changes | `BLOCKED` |",
        "| Production broker behavior changes | `BLOCKED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This bounded operator-run packet performed no package capture" in (
        packet_text
    )
    assert "no replay, no\nscoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no\nVPS action" in packet_text
    assert "production command-surface change" in packet_text
    assert "Unit 12 action" in packet_text
    assert "This bounded operator-run packet performed no commit and no push" in (
        packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture Bounded LOCAL_MAC Operator Run Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`local_head=b06d8a4b96c9237911547cffa6bb31b1d8bf829d`" in map_text
    assert "`origin_main=b06d8a4b96c9237911547cffa6bb31b1d8bf829d`" in map_text
    assert (
        "`expected_commit=b06d8a4b96c9237911547cffa6bb31b1d8bf829d`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in map_text
    )
    assert "`NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_FOR_PACKAGE_CAPTURE`" in (
        map_text
    )
    assert "`logs/<run_id>.jsonl`" in map_text
    assert "`last_run_report.json`" in map_text
    assert "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`bounded_vps_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_local_mac_runtime_artifact_availability_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_local_mac_runtime_artifact_availability_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture LOCAL_MAC Runtime Artifact Availability Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`"
        in packet_text
    )
    assert (
        "`origin_main` | `b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`"
        in packet_text
    )
    assert (
        "`expected_commit` | `b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`"
        in packet_text
    )
    assert "`head_equals_expected_commit` | `PASS`" in packet_text
    assert "`origin_main_equals_expected_commit` | `PASS`" in packet_text
    assert "`local_head_equals_origin_main` | `PASS`" in packet_text
    assert "`worktree` | `clean`" in packet_text
    assert "`local_mac_python_version` | `Python 3.12.13`" in packet_text
    assert (
        "`prior_bounded_operator_run_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`prior_concrete_blocker` | "
        "`NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_FOR_PACKAGE_CAPTURE`"
        in packet_text
    )
    assert (
        "`artifact_availability_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET_READY_FOR_BOUNDED_LOCAL_MAC_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`current_artifact_availability_result` | "
        "`NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_CURRENTLY_AVAILABLE`"
        in packet_text
    )
    assert "`logs_directory` | `ABSENT`" in packet_text
    assert "`run_reports_directory` | `ABSENT`" in packet_text
    assert "`replay_packages_directory` | `ABSENT`" in packet_text
    assert "`last_run_report_json` | `ABSENT`" in packet_text
    assert "`order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`" in packet_text
    assert "`log_candidates` | `NO_LOGS_DIR`" in packet_text
    assert "`run_report_candidates` | `NO_RUN_REPORTS_DIR`" in packet_text
    assert "`eligible_run_id` | `NONE`" in packet_text
    assert "`runtime_artifact_production_authorized_by_this_gate` | `false`" in (
        packet_text
    )
    assert "`package_capture_executed_by_this_gate` | `false`" in packet_text
    assert "`replay_executed_by_this_gate` | `false`" in packet_text
    assert "`scoring_executed_by_this_gate` | `false`" in packet_text
    assert "`candidate_generation_executed_by_this_gate` | `false`" in packet_text
    assert "`broker_tws_api_network_runtime_action` | `false`" in packet_text
    assert "`vps_action` | `false`" in packet_text
    assert "`production_command_surface_changed` | `false`" in packet_text
    assert "`unit_12_action` | `false`" in packet_text
    assert "`commit_performed` | `false`" in packet_text
    assert "`push_performed` | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`"
        in packet_text
    )

    for inventory_line in (
        "logs=ABSENT",
        "run_reports=ABSENT",
        "replay_packages=ABSENT",
        "last_run_report.json=ABSENT",
        "order_state.json=ABSENT",
        "LOG CANDIDATES=NO_LOGS_DIR",
        "RUN_REPORT CANDIDATES=NO_RUN_REPORTS_DIR",
        "REPLAY_PACKAGE EXISTING TARGETS=NO_REPLAY_PACKAGES_DIR",
        "LAST_RUN_REPORT STATUS=NO_LAST_RUN_REPORT",
        "ORDER_STATE STATUS=PASS_order_state_absent_excluded_not_bound",
    ):
        assert inventory_line in packet_text

    assert "NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_CURRENTLY_AVAILABLE" in (
        packet_text
    )
    assert "No eligible package-capture `run_id` is currently available" in (
        packet_text
    )
    assert "logs directory is absent" in packet_text
    assert "run_reports directory is absent" in packet_text
    assert "last_run_report.json is absent" in packet_text
    assert "there are no log candidates" in packet_text
    assert "there are no run-report candidates" in packet_text
    assert "no eligible `run_id` can be selected" in packet_text
    assert "no selected `run_id` has aligned report evidence" in packet_text
    assert "no selected `run_id` has terminal completion evidence" in packet_text
    assert "`replay_packages` is a package output\ntarget" in packet_text

    assert "runtime_artifact_production=NOT_AUTHORIZED_BY_THIS_GATE" in (
        packet_text
    )
    assert "does not produce runtime artifacts" in packet_text
    assert "does not generate runtime\nartifacts" in packet_text
    assert "does not create `logs/`" in packet_text
    assert "does not create `run_reports/`" in packet_text
    assert "does not\ncreate `replay_packages/`" in packet_text
    assert "does not create `last_run_report.json`" in packet_text
    assert "does not\ncreate `order_state.json`" in packet_text
    assert "does not generate diagnostic or runtime reports" in packet_text
    assert "The next gate is not pre-approved by this packet" in packet_text

    assert "package_capture_execution=NOT_AUTHORIZED" in packet_text
    assert "No package capture may execute" in packet_text

    for criterion in (
        "branch `main`",
        "clean worktree",
        "LOCAL_MAC HEAD equals `origin/main`",
        "`expected_commit` equals current LOCAL_MAC HEAD and `origin/main`",
        "concrete safe `run_id`",
        "`logs/<run_id>.jsonl` exists",
        "`run_reports/<run_id>.json` exists or `last_run_report.json` alignment\n  exists",
        "selected `run_id` is derived only from eligible existing runtime artifacts",
        "selected `run_id` has aligned report evidence",
        "selected `run_id` has terminal completion evidence",
        "`replay_packages/<run_id>` is absent before package capture",
        "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`",
        "no `order_state` read, write, creation, binding, validation, inference, or\n  use",
        "no `--authorize-vps-package-write`",
        "no `--execution-mode vps`",
        "no `package_execution_orchestrator.main` delegation",
        "no VPS action",
        "no broker/TWS/API/network/runtime/scheduler/systemd/timer/service action",
        "no replay, scoring, candidate generation, or Unit 12 action",
    ):
        assert criterion in packet_text

    for restriction in (
        "package capture execution",
        "runtime artifact production",
        "runtime artifact generation",
        "diagnostic or runtime report generation",
        "replay execution",
        "scoring execution",
        "candidate generation execution",
        "Unit 12 implementation",
        "broker submit readiness",
        "live trading readiness",
        "account authority",
        "order authority",
        "execution authority",
        "VPS action",
        "bounded VPS execution",
        "VPS endpoint approval",
        "`18789` or `18791` endpoint approval",
        "bridge, tunnel, or proxy approval",
        "runtime/scheduler/service/systemd/timer mutation",
        "credential or environment-file mutation",
        "production runtime/provider-selection changes",
        "production broker behavior changes",
        "strategy/risk/execution behavior changes",
        "production command-surface changes",
        "package writer/reader/orchestrator changes",
        "`tools/ops/gate_d_market_session_operator.py` changes",
        "`logs/`, `run_reports/`, `replay_packages/`, `last_run_report.json`, or\n  `order_state.json` creation or modification",
    ):
        assert restriction in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or use\n`order_state`" in (
        packet_text
    )
    assert "does not use\n`order_state` to unblock runtime artifact production or package capture" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Runtime artifact production | `NOT_AUTHORIZED_BY_THIS_GATE` |",
        "| Runtime artifact generation | `NOT_AUTHORIZED_BY_THIS_GATE` |",
        "| Diagnostic/runtime report generation | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Strategy behavior changes | `BLOCKED` |",
        "| Risk behavior changes | `BLOCKED` |",
        "| Execution behavior changes | `BLOCKED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime configuration changes | `BLOCKED` |",
        "| Production provider-selection runtime behavior changes | `BLOCKED` |",
        "| Production command-surface changes | `BLOCKED` |",
        "| Production broker behavior changes | `BLOCKED` |",
        "| Package writer/reader/orchestrator changes | `BLOCKED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
    ):
        assert authority in packet_text

    assert "This artifact availability packet performed no package capture" in (
        packet_text
    )
    assert "no runtime\nartifact production" in packet_text
    assert "no runtime artifact generation" in packet_text
    assert "no diagnostic or runtime\nreport generation" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no\nbroker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12\naction" in packet_text
    assert "This artifact availability packet performed no commit and no push" in (
        packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture LOCAL_MAC Runtime Artifact Availability Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET_READY_FOR_BOUNDED_LOCAL_MAC_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`"
        in map_text
    )
    assert "`NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_CURRENTLY_AVAILABLE`" in (
        map_text
    )
    assert "`runtime_artifact_production=NOT_AUTHORIZED_BY_THIS_GATE`" in (
        map_text
    )
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`" in map_text
    assert "`package_writer_reader_orchestrator_changes=BLOCKED`" in map_text
    assert "`bounded_vps_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_local_mac_runtime_artifact_production_authorization_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_local_mac_runtime_artifact_production_authorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture LOCAL_MAC Runtime Artifact Production Authorization Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `d84aa9cdcd21ddfd32f5d39ec1156f76071170ba`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `d84aa9cdcd21ddfd32f5d39ec1156f76071170ba`"
        in packet_text
    )
    assert (
        "`origin_main` | `d84aa9cdcd21ddfd32f5d39ec1156f76071170ba`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_availability_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET_READY_FOR_BOUNDED_LOCAL_MAC_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`artifact_production_authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_LOCAL_MAC_READ_ONLY_ARTIFACT_PRODUCTION_PACKET`"
        in packet_text
    )
    assert (
        "`authorized_future_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET`"
        in packet_text
    )
    assert "`current_logs_directory` | `ABSENT`" in packet_text
    assert "`current_run_reports_directory` | `ABSENT`" in packet_text
    assert "`current_replay_packages_directory` | `ABSENT`" in packet_text
    assert "`current_last_run_report_json` | `ABSENT`" in packet_text
    assert (
        "`current_order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`" in packet_text
    )

    for false_field in (
        "`runtime_artifact_production_performed_by_this_gate` | `false`",
        "`runtime_artifact_generation_performed_by_this_gate` | `false`",
        "`diagnostic_runtime_report_generation_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`scheduler_service_systemd_timer_action` | `false`",
        "`credential_env_mutation` | `false`",
        "`production_command_surface_changed` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed` | `false`",
        "`push_performed` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET`"
        in packet_text
    )

    assert "NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_CURRENTLY_AVAILABLE" in (
        packet_text
    )
    assert "logs=ABSENT" in packet_text
    assert "run_reports=ABSENT" in packet_text
    assert "replay_packages=ABSENT" in packet_text
    assert "last_run_report.json=ABSENT" in packet_text
    assert "order_state.json=ABSENT" in packet_text
    assert "Because no eligible `run_id` or aligned runtime artifacts currently exist" in (
        packet_text
    )
    assert "This packet authorizes only a later source-controlled gate" in (
        packet_text
    )
    assert (
        "POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET"
        in packet_text
    )
    assert "This packet does not pre-approve the later gate's execution" in (
        packet_text
    )

    for not_authorized in (
        "package capture execution",
        "runtime artifact production in this gate",
        "runtime artifact generation in this gate",
        "diagnostic or runtime report generation in this gate",
        "replay execution",
        "scoring execution",
        "candidate generation execution",
        "Unit 12 implementation",
        "broker submit readiness",
        "live trading readiness",
        "account authority",
        "order authority",
        "execution authority",
        "broker/TWS/API/network/runtime action in this gate",
        "VPS action",
        "bounded VPS execution",
        "VPS endpoint approval",
        "`18789` or `18791` endpoint approval",
        "bridge, tunnel, or proxy approval",
        "scheduler/service/systemd/timer action",
        "credential or environment-file mutation",
        "production runtime/provider-selection changes",
        "production broker behavior changes",
        "strategy/risk/execution behavior changes",
        "production command-surface changes",
        "package writer/reader/orchestrator changes",
        "`tools/ops/gate_d_market_session_operator.py` changes",
        "`logs/`, `run_reports/`, `replay_packages/`, `last_run_report.json`, or\n  `order_state.json` creation or modification in this gate",
    ):
        assert not_authorized in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or use\n`order_state`" in (
        packet_text
    )
    assert "does not use\n`order_state` to authorize runtime artifact production or package capture" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Runtime artifact production in this gate | `NOT_PERFORMED` |",
        "| Runtime artifact generation in this gate | `NOT_PERFORMED` |",
        "| Diagnostic/runtime report generation in this gate | `NOT_PERFORMED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| VPS endpoint approval | `NOT_APPROVED` |",
        "| `18789` or `18791` endpoint approval | `NOT_APPROVED` |",
        "| Bridge, tunnel, or proxy approval | `NOT_APPROVED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production runtime/provider-selection changes | `BLOCKED` |",
        "| Production broker behavior changes | `BLOCKED` |",
        "| Strategy/risk/execution behavior changes | `BLOCKED` |",
        "| Production command-surface changes | `BLOCKED` |",
        "| Package writer/reader/orchestrator changes | `BLOCKED` |",
    ):
        assert authority in packet_text

    assert (
        "This runtime artifact production authorization packet performed no package\ncapture"
        in packet_text
    )
    assert "no runtime artifact production" in packet_text
    assert "no runtime artifact generation" in packet_text
    assert "no\ndiagnostic or runtime report generation" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no candidate\ngeneration" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12 action" in packet_text
    assert (
        "This runtime artifact production authorization packet performed no commit and\nno push"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture LOCAL_MAC Runtime Artifact Production Authorization Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=d84aa9cdcd21ddfd32f5d39ec1156f76071170ba`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_LOCAL_MAC_READ_ONLY_ARTIFACT_PRODUCTION_PACKET`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET`"
        in map_text
    )
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`runtime_artifact_production_in_this_gate=NOT_PERFORMED`" in map_text
    assert "`package_writer_reader_orchestrator_changes=BLOCKED`" in map_text
    assert "`bounded_vps_execution=NOT_AUTHORIZED`" in map_text


def test_post_d11_replay_package_capture_bounded_local_mac_read_only_runtime_artifact_production_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_bounded_local_mac_read_only_runtime_artifact_production_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture Bounded LOCAL_MAC Read-Only Runtime Artifact Production Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `a149cdcae1665edd0637897d340393a53133f9dc`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `a149cdcae1665edd0637897d340393a53133f9dc`"
        in packet_text
    )
    assert (
        "`origin_main` | `a149cdcae1665edd0637897d340393a53133f9dc`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_LOCAL_MAC_READ_ONLY_ARTIFACT_PRODUCTION_PACKET`"
        in packet_text
    )
    assert (
        "`bounded_read_only_artifact_production_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET_APPROVED_FOR_ONE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`"
        in packet_text
    )
    assert (
        "`authorized_future_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`"
        in packet_text
    )
    assert "`authorized_operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert "`authorized_future_run_count` | `1`" in packet_text
    assert "`current_logs_directory` | `ABSENT`" in packet_text
    assert "`current_run_reports_directory` | `ABSENT`" in packet_text
    assert "`current_replay_packages_directory` | `ABSENT`" in packet_text
    assert "`current_last_run_report_json` | `ABSENT`" in packet_text
    assert (
        "`current_order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`" in packet_text
    )

    for false_field in (
        "`runtime_artifact_production_performed_by_this_gate` | `false`",
        "`runtime_artifact_generation_performed_by_this_gate` | `false`",
        "`diagnostic_runtime_report_generation_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`scheduler_service_systemd_timer_action` | `false`",
        "`credential_env_mutation` | `false`",
        "`production_behavior_changed` | `false`",
        "`production_command_surface_changed` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed` | `false`",
        "`push_performed` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`"
        in packet_text
    )
    assert "authorizes only the next source-controlled packet/gate" in packet_text
    assert "does not execute that\nrun and does not create artifacts" in packet_text
    assert "logs=ABSENT" in packet_text
    assert "run_reports=ABSENT" in packet_text
    assert "replay_packages=ABSENT" in packet_text
    assert "last_run_report.json=ABSENT" in packet_text
    assert "order_state.json=ABSENT" in packet_text

    for not_authorized in (
        "package capture",
        "runtime artifact production in this gate",
        "runtime artifact generation in this gate",
        "diagnostic or runtime report generation in this gate",
        "replay",
        "scoring",
        "candidate generation",
        "Unit 12",
        "broker submit readiness",
        "live trading readiness",
        "account authority",
        "order authority",
        "execution authority",
        "broker/TWS/API/network/runtime action in this gate",
        "VPS action",
        "scheduler/systemd/timer/service mutation",
        "credential or environment-file mutation",
        "production behavior changes",
        "production command-surface changes",
        "production provider-selection changes",
        "production broker behavior changes",
        "strategy/risk/execution behavior changes",
        "package writer/reader/orchestrator changes",
        "`tools/ops/gate_d_market_session_operator.py` changes",
        "creation of `logs/`, `run_reports/`, `replay_packages/`,\n  `last_run_report.json`, or `order_state.json`",
        "commit",
        "push",
    ):
        assert not_authorized in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or use\n`order_state`" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Runtime artifact production in this gate | `NOT_PERFORMED` |",
        "| Runtime artifact generation in this gate | `NOT_PERFORMED` |",
        "| Diagnostic/runtime report generation in this gate | `NOT_PERFORMED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production behavior changes | `BLOCKED` |",
        "| Production runtime/provider-selection changes | `BLOCKED` |",
        "| Production broker behavior changes | `BLOCKED` |",
        "| Strategy/risk/execution behavior changes | `BLOCKED` |",
        "| Production command-surface changes | `BLOCKED` |",
        "| Package writer/reader/orchestrator changes | `BLOCKED` |",
    ):
        assert authority in packet_text

    assert (
        "This bounded LOCAL_MAC read-only runtime artifact production packet performed\nno artifact production"
        in packet_text
    )
    assert "no package capture" in packet_text
    assert "no runtime artifact generation" in packet_text
    assert "no\ndiagnostic or runtime report generation" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no candidate\ngeneration" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12\naction" in packet_text
    assert (
        "This bounded LOCAL_MAC read-only runtime artifact production packet performed\nno commit and no push"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture Bounded LOCAL_MAC Read-Only Runtime Artifact Production Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=a149cdcae1665edd0637897d340393a53133f9dc`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET_APPROVED_FOR_ONE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`"
        in map_text
    )
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`runtime_artifact_production_in_this_gate=NOT_PERFORMED`" in map_text
    assert "`vps_action=NOT_AUTHORIZED`" in map_text
    assert "`package_writer_reader_orchestrator_changes=BLOCKED`" in map_text


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_run_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_run_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Run Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `99c64e16a992c4ce320fea20263ad600468bb6da`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `99c64e16a992c4ce320fea20263ad600468bb6da`"
        in packet_text
    )
    assert (
        "`origin_main` | `99c64e16a992c4ce320fea20263ad600468bb6da`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET_APPROVED_FOR_ONE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`"
        in packet_text
    )
    assert (
        "`direct_mac_terminal_read_only_run_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET_APPROVED_FOR_ONE_DIRECT_MAC_TERMINAL_READ_ONLY_RUN`"
        in packet_text
    )
    assert (
        "`exact_next_operator_step` | "
        "`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`"
        in packet_text
    )
    assert "`operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert "`authorized_future_run_count` | `1`" in packet_text
    assert "`current_logs_directory` | `ABSENT`" in packet_text
    assert "`current_run_reports_directory` | `ABSENT`" in packet_text
    assert "`current_replay_packages_directory` | `ABSENT`" in packet_text
    assert "`current_last_run_report_json` | `ABSENT`" in packet_text
    assert (
        "`current_order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`" in packet_text
    )

    for false_field in (
        "`runtime_artifact_production_performed_by_this_codex_gate` | `false`",
        "`runtime_artifact_generation_performed_by_this_codex_gate` | `false`",
        "`diagnostic_runtime_report_generation_performed_by_this_codex_gate` | `false`",
        "`package_capture_executed_by_this_codex_gate` | `false`",
        "`replay_executed_by_this_codex_gate` | `false`",
        "`scoring_executed_by_this_codex_gate` | `false`",
        "`candidate_generation_executed_by_this_codex_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`scheduler_service_systemd_timer_action` | `false`",
        "`credential_env_mutation` | `false`",
        "`production_behavior_changed` | `false`",
        "`production_command_surface_changed` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed` | `false`",
        "`push_performed` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_operator_step` | "
        "`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`"
        in packet_text
    )
    assert "defines the exact next operator step as one bounded" in packet_text
    assert "does not execute that\noperator step and does not create artifacts" in (
        packet_text
    )
    assert "logs=ABSENT" in packet_text
    assert "run_reports=ABSENT" in packet_text
    assert "replay_packages=ABSENT" in packet_text
    assert "last_run_report.json=ABSENT" in packet_text
    assert "order_state.json=ABSENT" in packet_text

    for not_authorized in (
        "package capture",
        "runtime artifact production in this Codex gate",
        "runtime artifact generation in this Codex gate",
        "diagnostic or runtime report generation in this Codex gate",
        "replay",
        "scoring",
        "candidate generation",
        "Unit 12",
        "broker submit readiness",
        "live trading readiness",
        "account authority",
        "order authority",
        "execution authority",
        "broker/TWS/API/network/runtime action in this Codex gate",
        "VPS action",
        "scheduler/systemd/timer/service mutation",
        "credential or environment-file mutation",
        "production behavior changes",
        "production command-surface changes",
        "production provider-selection changes",
        "production broker behavior changes",
        "strategy/risk/execution behavior changes",
        "package writer/reader/orchestrator changes",
        "`tools/ops/gate_d_market_session_operator.py` changes",
        "creation of `logs/`, `run_reports/`, `replay_packages/`,\n  `last_run_report.json`, or `order_state.json` in this Codex gate",
        "commit",
        "push",
    ):
        assert not_authorized in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or use\n`order_state`" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Runtime artifact production in this Codex gate | `NOT_PERFORMED` |",
        "| Runtime artifact generation in this Codex gate | `NOT_PERFORMED` |",
        "| Diagnostic/runtime report generation in this Codex gate | `NOT_PERFORMED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| Scheduler/runtime/service/systemd/timer changes | `BLOCKED` |",
        "| Credential or environment-file changes | `BLOCKED` |",
        "| Production behavior changes | `BLOCKED` |",
        "| Production runtime/provider-selection changes | `BLOCKED` |",
        "| Production broker behavior changes | `BLOCKED` |",
        "| Strategy/risk/execution behavior changes | `BLOCKED` |",
        "| Production command-surface changes | `BLOCKED` |",
        "| Package writer/reader/orchestrator changes | `BLOCKED` |",
    ):
        assert authority in packet_text

    assert (
        "This DIRECT_MAC_TERMINAL read-only artifact production run packet performed no\nartifact production"
        in packet_text
    )
    assert "no package capture" in packet_text
    assert "no runtime artifact generation" in packet_text
    assert "no\ndiagnostic or runtime report generation" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no candidate\ngeneration" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12\naction" in packet_text
    assert (
        "This DIRECT_MAC_TERMINAL read-only artifact production run packet performed no\ncommit and no push"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Run Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=99c64e16a992c4ce320fea20263ad600468bb6da`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET_APPROVED_FOR_ONE_DIRECT_MAC_TERMINAL_READ_ONLY_RUN`"
        in map_text
    )
    assert "`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`" in (
        map_text
    )
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`runtime_artifact_production_in_this_codex_gate=NOT_PERFORMED`" in (
        map_text
    )
    assert "`vps_action=NOT_AUTHORIZED`" in map_text
    assert "`package_writer_reader_orchestrator_changes=BLOCKED`" in map_text


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_blocker_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_blocker_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Blocker Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `b6ecbe488918e3b1d92d9de73327db2eea161989`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `b6ecbe488918e3b1d92d9de73327db2eea161989`"
        in packet_text
    )
    assert (
        "`origin_main` | `b6ecbe488918e3b1d92d9de73327db2eea161989`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`"
        in packet_text
    )
    assert (
        "`prior_symbolic_operator_step` | "
        "`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`"
        in packet_text
    )
    assert (
        "`command_surface_blocker_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`concrete_blocker` | "
        "`NO_EXACT_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_DEFINED`"
        in packet_text
    )
    assert (
        "`exact_executable_direct_mac_terminal_artifact_production_command` | `NOT_DEFINED`"
        in packet_text
    )
    assert "`capture_local_references_found` | `true`" in packet_text
    assert (
        "`capture_local_surface_classification` | "
        "`PACKAGE_CAPTURE_RELATED_REQUIRES_EXISTING_RUNTIME_ARTIFACTS`"
        in packet_text
    )
    assert "`eligible_runtime_artifacts_available` | `false`" in packet_text
    assert "`current_logs_directory` | `ABSENT`" in packet_text
    assert "`current_run_reports_directory` | `ABSENT`" in packet_text
    assert "`current_replay_packages_directory` | `ABSENT`" in packet_text
    assert "`current_last_run_report_json` | `ABSENT`" in packet_text
    assert (
        "`current_order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`" in packet_text
    )

    for false_field in (
        "`runtime_artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`unit_12_action` | `false`",
        "`production_code_changed` | `false`",
        "`command_surface_code_changed` | `false`",
        "`commit_performed` | `false`",
        "`push_performed` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET`"
        in packet_text
    )
    assert "approved only the symbolic operator step" in packet_text
    assert "found no exact executable Direct Mac Terminal command" in packet_text
    assert "`capture-local` is package-capture related" in packet_text
    assert "requires eligible existing runtime artifacts" in packet_text
    assert "logs=ABSENT" in packet_text
    assert "run_reports=ABSENT" in packet_text
    assert "replay_packages=ABSENT" in packet_text
    assert "last_run_report.json=ABSENT" in packet_text
    assert "order_state.json=ABSENT" in packet_text
    assert "NO_EXACT_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_DEFINED" in (
        packet_text
    )

    for not_authorized in (
        "artifact production",
        "package capture",
        "replay",
        "scoring",
        "candidate generation",
        "Unit 12",
        "broker submit readiness",
        "live trading readiness",
        "account authority",
        "order authority",
        "execution authority",
        "broker/TWS/API/network/runtime action",
        "VPS action",
        "scheduler/systemd/timer/service mutation",
        "credential or environment-file mutation",
        "production code changes",
        "command-surface code changes",
        "package writer/reader/orchestrator changes",
        "creation of `logs/`, `run_reports/`, `replay_packages/`,\n  `last_run_report.json`, or `order_state.json`",
        "commit",
        "push",
    ):
        assert not_authorized in packet_text

    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in packet_text
    assert "does not read, write, create, bind, validate, infer, or use\n`order_state`" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution | `NOT_AUTHORIZED_BY_THIS_GATE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| Production code changes | `BLOCKED` |",
        "| Command-surface code changes | `BLOCKED` |",
        "| Package writer/reader/orchestrator changes | `BLOCKED` |",
    ):
        assert authority in packet_text

    assert "performed no artifact production" in packet_text
    assert "no package\ncapture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no\nbroker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "performed no commit and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Blocker Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=b6ecbe488918e3b1d92d9de73327db2eea161989`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in map_text
    )
    assert "`NO_EXACT_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_DEFINED`" in (
        map_text
    )
    assert "`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`" in (
        map_text
    )
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert "`runtime_artifact_production_execution=NOT_AUTHORIZED_BY_THIS_GATE`" in (
        map_text
    )
    assert "`command_surface_code_changes=BLOCKED`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_design_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_design_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Design Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `e9a10ff406d46a77417af50800155cb8f057d4b7`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `e9a10ff406d46a77417af50800155cb8f057d4b7`"
        in packet_text
    )
    assert (
        "`origin_main` | `e9a10ff406d46a77417af50800155cb8f057d4b7`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET`"
        in packet_text
    )
    assert (
        "`prior_concrete_blocker` | "
        "`NO_EXACT_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_DEFINED`"
        in packet_text
    )
    assert (
        "`design_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET_READY_FOR_IMPLEMENTATION_GATE`"
        in packet_text
    )
    assert "`exact_proposed_command_name` | `produce-read-only-artifacts`" in (
        packet_text
    )
    assert (
        "`exact_proposed_command_shape` | "
        "`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production`"
        in packet_text
    )
    assert "`required_flag_run_id` | `--run-id <run_id>`" in packet_text
    assert (
        "`required_flag_expected_commit` | `--expected-commit <commit>`"
        in packet_text
    )
    assert (
        "`required_flag_authorization` | "
        "`--authorize-direct-mac-terminal-read-only-artifact-production`"
        in packet_text
    )
    assert "`local_mac_only_boundary` | `REQUIRED`" in packet_text
    assert "`direct_mac_terminal_boundary` | `REQUIRED`" in packet_text
    assert "`clean_worktree_required` | `true`" in packet_text
    assert "`expected_commit_verification_required` | `true`" in packet_text
    assert (
        "`read_only_no_broker_no_order_no_execution_boundary` | `REQUIRED`"
        in packet_text
    )
    assert "`allowed_outputs` | `logs/<run_id>.jsonl; run_reports/<run_id>.json`" in (
        packet_text
    )
    assert "`prohibited_outputs` | `replay_packages/<run_id>" in packet_text

    for false_field in (
        "`implementation_performed_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`unit_12_action` | `false`",
        "`production_code_changed` | `false`",
        "`command_surface_code_changed` | `false`",
        "`commit_performed` | `false`",
        "`push_performed` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET`"
        in packet_text
    )
    assert (
        ".venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production"
        in packet_text
    )
    assert "The future implementation must not treat `capture-local` as this command" in (
        packet_text
    )
    assert "LOCAL_MAC-only and DIRECT_MAC_TERMINAL-only" in packet_text
    assert "must not perform VPS action" in packet_text
    assert "must not require or accept VPS authorization flags" in packet_text
    assert "must not delegate to a VPS execution path" in packet_text
    assert "read-only runtime artifact\nproduction" in packet_text
    assert "logs/<run_id>.jsonl" in packet_text
    assert "run_reports/<run_id>.json" in packet_text
    assert "replay_packages/<run_id>" in packet_text
    assert "`order_state.json`" in packet_text
    assert "Package capture execution | `NOT_AUTHORIZED`" in packet_text

    for evidence_requirement in (
        "the exact command parser entry added or exposed",
        "the exact required flags",
        "parser behavior proving missing required flags fail closed",
        "parser behavior proving package-capture flags are not accepted as authority",
        "source checks proving no package capture path is invoked",
        "tests proving expected commit and clean worktree checks are enforced",
        "tests proving `order_state.json` is not read, written, created, bound",
    ):
        assert evidence_requirement in packet_text

    for fail_closed in (
        "branch is not `main`",
        "LOCAL_MAC HEAD does not equal `origin/main`",
        "`--expected-commit` does not equal LOCAL_MAC HEAD and `origin/main`",
        "the worktree is dirty",
        "`--run-id` is absent or unsafe",
        "`--authorize-direct-mac-terminal-read-only-artifact-production` is absent",
        "a package-capture authorization flag is supplied as a substitute",
    ):
        assert fail_closed in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution | `NOT_AUTHORIZED_BY_THIS_DESIGN_GATE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
        "| Production code changes | `BLOCKED_BY_THIS_GATE` |",
        "| Command-surface code changes | `DESIGNED_ONLY_NOT_IMPLEMENTED` |",
        "| Package writer/reader/orchestrator changes | `BLOCKED` |",
    ):
        assert authority in packet_text

    assert "performed no implementation" in packet_text
    assert "no artifact\nproduction" in packet_text
    assert "no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "performed no commit and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Design Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=e9a10ff406d46a77417af50800155cb8f057d4b7`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET_READY_FOR_IMPLEMENTATION_GATE`"
        in map_text
    )
    assert "produce-read-only-artifacts --run-id <run_id>" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution=NOT_AUTHORIZED_BY_THIS_DESIGN_GATE`"
        in map_text
    )
    assert "`command_surface_code_changes=DESIGNED_ONLY_NOT_IMPLEMENTED`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET`"
        in map_text
    )


def test_gate_d_operator_produce_read_only_artifacts_command_surface_exists() -> None:
    from tools.ops import gate_d_market_session_operator as operator

    parser = operator.build_parser()
    parsed = parser.parse_args(
        [
            "produce-read-only-artifacts",
            "--run-id",
            "run_1",
            "--expected-commit",
            "abc123",
            "--authorize-direct-mac-terminal-read-only-artifact-production",
        ]
    )

    assert parsed.command == "produce-read-only-artifacts"
    assert parsed.run_id == "run_1"
    assert parsed.expected_commit == "abc123"
    assert (
        parsed.authorize_direct_mac_terminal_read_only_artifact_production is True
    )
    assert not hasattr(parsed, "authorize_vps_package_write")
    assert not hasattr(parsed, "authorize_local_package_write")
    assert parsed.func is operator.produce_read_only_artifacts

    try:
        parser.parse_args(
            [
                "produce-read-only-artifacts",
                "--run-id",
                "run_1",
                "--expected-commit",
                "abc123",
            ]
        )
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError(
            "produce-read-only-artifacts must require direct Mac terminal authorization"
        )

    try:
        parser.parse_args(
            [
                "produce-read-only-artifacts",
                "--run-id",
                "run_1",
                "--expected-commit",
                "abc123",
                "--authorize-local-package-write",
            ]
        )
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError(
            "produce-read-only-artifacts must not accept package-capture authority"
        )


def test_gate_d_operator_produce_read_only_artifacts_source_boundaries() -> None:
    source_text = Path("tools/ops/gate_d_market_session_operator.py").read_text(
        encoding="utf-8"
    )

    assert "DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED" in (
        source_text
    )
    assert "DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FAILED_CLOSED" in (
        source_text
    )
    assert "def produce_read_only_artifacts(" in source_text
    assert '"produce-read-only-artifacts"' in source_text
    assert "--authorize-direct-mac-terminal-read-only-artifact-production" in (
        source_text
    )
    assert "head_equals_expected" in source_text
    assert "origin_main_equals_expected" in source_text
    assert "local_head_equals_origin_main" in source_text
    assert "git_status_short_clean" in source_text
    assert "local_mac_only_source_context" in source_text
    assert "direct_mac_terminal_operator_surface" in source_text
    assert "read_only_authority_boundary" in source_text
    assert "broker_submit_readiness_not_approved" in source_text
    assert "account_authority_none" in source_text
    assert "order_authority_none" in source_text
    assert "execution_authority_none" in source_text
    assert "tws_api_network_runtime_action_not_used" in source_text
    assert "vps_action_not_used" in source_text
    assert "scheduler_service_systemd_timer_mutation_not_used" in source_text
    assert "credential_env_mutation_not_used" in source_text
    assert "package_capture_not_executed" in source_text
    assert "replay_not_executed" in source_text
    assert "scoring_not_executed" in source_text
    assert "candidate_generation_not_executed" in source_text
    assert "unit_12_not_opened" in source_text
    assert "log_output_absent_before_write" in source_text
    assert "run_report_output_absent_before_write" in source_text
    assert "last_run_report_output_absent_before_write" in source_text
    assert "replay_package_output_prohibited_and_absent" in source_text
    assert "order_state_absent_excluded_not_bound" in source_text
    assert "RUN_ID=" in source_text
    assert "EXPECTED_COMMIT=" in source_text
    assert "ACTUAL_HEAD=" in source_text
    assert "ORIGIN_MAIN=" in source_text
    assert "WORKTREE_CLEAN=" in source_text
    assert "PRODUCED_ARTIFACT_PATHS=" in source_text
    assert "BROKER_SUBMIT_READINESS=NOT_APPROVED" in source_text
    assert "ACCOUNT_AUTHORITY=NONE" in source_text
    assert "ORDER_AUTHORITY=NONE" in source_text
    assert "EXECUTION_AUTHORITY=NONE" in source_text
    assert "PACKAGE_CAPTURE_EXECUTED=false" in source_text
    assert "REPLAY_EXECUTED=false" in source_text
    assert "SCORING_EXECUTED=false" in source_text
    assert "CANDIDATE_GENERATION_EXECUTED=false" in source_text
    assert "UNIT_12_ACTION=false" in source_text
    assert "logs" in source_text
    assert "run_reports" in source_text
    assert "last_run_report.json" in source_text
    assert "replay_packages" in source_text
    assert "order_state.json" in source_text


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_implementation_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_implementation_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Implementation Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `71b2717d53ec71afc4a3bead1938a704b8be58b1`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `71b2717d53ec71afc4a3bead1938a704b8be58b1`"
        in packet_text
    )
    assert (
        "`origin_main` | `71b2717d53ec71afc4a3bead1938a704b8be58b1`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET_READY_FOR_IMPLEMENTATION_GATE`"
        in packet_text
    )
    assert (
        "`implementation_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET_READY_FOR_LOCAL_DIFF_REVIEW`"
        in packet_text
    )
    assert "`implemented_command_name` | `produce-read-only-artifacts`" in (
        packet_text
    )
    assert (
        "`implemented_command_surface` | "
        "`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production`"
        in packet_text
    )
    assert "`required_flag_run_id` | `--run-id <run_id>`" in packet_text
    assert (
        "`required_flag_expected_commit` | `--expected-commit <commit>`"
        in packet_text
    )
    assert (
        "`required_flag_authorization` | "
        "`--authorize-direct-mac-terminal-read-only-artifact-production`"
        in packet_text
    )
    assert "`authorization_missing_fails_closed` | `true`" in packet_text
    assert "`head_expected_commit_check` | `IMPLEMENTED`" in packet_text
    assert "`local_head_origin_main_alignment_check` | `IMPLEMENTED`" in (
        packet_text
    )
    assert "`clean_worktree_check` | `IMPLEMENTED`" in packet_text
    assert "`local_mac_only_boundary` | `IMPLEMENTED`" in packet_text
    assert (
        "`read_only_no_broker_no_order_no_execution_boundary` | `IMPLEMENTED`"
        in packet_text
    )
    assert (
        "`allowed_later_outputs` | "
        "`logs/<run_id>.jsonl; run_reports/<run_id>.json; last_run_report.json`"
        in packet_text
    )
    assert "`prohibited_outputs` | `replay_packages/" in packet_text

    for false_field in (
        "`artifact_production_run_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed` | `false`",
        "`push_performed` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET`"
        in packet_text
    )
    assert "does not use `capture-local`" in packet_text
    assert "does not delegate to\n`package_execution_orchestrator.main`" in (
        packet_text
    )
    assert "does not use `--execution-mode vps`" in packet_text
    assert "current LOCAL_MAC HEAD equals `--expected-commit`" in packet_text
    assert "local `origin/main` equals `--expected-commit`" in packet_text
    assert "clean worktree before execution" in packet_text
    assert "safe concrete `run_id`" in packet_text
    assert "absent/excluded/not-bound `order_state.json`" in packet_text

    for evidence_field in (
        "`RUN_ID`",
        "`EXPECTED_COMMIT`",
        "`ACTUAL_HEAD`",
        "`ORIGIN_MAIN`",
        "`ORIGIN_MAIN_ALIGNED`",
        "`WORKTREE_CLEAN`",
        "`STATUS_SHORT`",
        "`SOURCE_CONTEXT=LOCAL_MAC_ONLY`",
        "`OPERATOR_SURFACE=DIRECT_MAC_TERMINAL`",
        "`READ_ONLY_AUTHORITY=true`",
        "`BROKER_SUBMIT_READINESS=NOT_APPROVED`",
        "`ACCOUNT_AUTHORITY=NONE`",
        "`ORDER_AUTHORITY=NONE`",
        "`EXECUTION_AUTHORITY=NONE`",
        "`PACKAGE_CAPTURE_EXECUTED=false`",
        "`REPLAY_EXECUTED=false`",
        "`SCORING_EXECUTED=false`",
        "`CANDIDATE_GENERATION_EXECUTED=false`",
        "`UNIT_12_ACTION=false`",
        "`ORDER_STATE_BOUND=false`",
    ):
        assert evidence_field in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert "performed no artifact production" in packet_text
    assert "no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "no\ncommit, and no push" in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Implementation Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=71b2717d53ec71afc4a3bead1938a704b8be58b1`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET_READY_FOR_LOCAL_DIFF_REVIEW`"
        in map_text
    )
    assert "produce-read-only-artifacts --run-id <run_id>" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_implementation_local_review_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_implementation_local_review_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Implementation Local Review Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `19aff6b597e632427f54e9d8f52972b5eae9f546`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `19aff6b597e632427f54e9d8f52972b5eae9f546`"
        in packet_text
    )
    assert (
        "`origin_main` | `19aff6b597e632427f54e9d8f52972b5eae9f546`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET`"
        in packet_text
    )
    assert (
        "`local_review_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET_READY_FOR_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production`"
        in packet_text
    )
    assert "`local_compact_review_allowed_paths_only` | `PASS`" in packet_text
    assert "`local_compact_review_command_surface_present` | `PASS`" in (
        packet_text
    )
    assert "`local_compact_review_authorization_flag_present` | `PASS`" in (
        packet_text
    )
    assert "`local_compact_review_fail_closed_terms_present` | `PASS`" in (
        packet_text
    )
    assert "`local_validation_pytest` | `120 passed`" in packet_text
    assert "`local_validation_git_diff_check` | `PASS`" in packet_text
    assert (
        "`local_commit` | `19aff6b597e632427f54e9d8f52972b5eae9f546`"
        in packet_text
    )
    assert "`local_push_head_origin_aligned` | `PASS`" in packet_text
    assert (
        "`vps_validation_head_matches_expected` | `PASS_head_matches_expected_19aff6b`"
        in packet_text
    )
    assert (
        "`vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned`"
        in packet_text
    )
    assert "`vps_validation_pytest` | `120 passed`" in packet_text

    for false_field in (
        "`produce_read_only_artifacts_run_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert "does not run `produce-read-only-artifacts`" in packet_text
    assert "does not authorize an operator run by itself" in packet_text
    assert "performed no `produce-read-only-artifacts` run" in packet_text
    assert "no\nartifact production" in packet_text
    assert "no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12\naction" in packet_text
    assert "no commit, and no push" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Implementation Local Review Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=19aff6b597e632427f54e9d8f52972b5eae9f546`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET_READY_FOR_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in map_text
    )
    assert "produce-read-only-artifacts --run-id <run_id>" in map_text
    assert "`PASS_head_matches_expected_19aff6b`" in map_text
    assert "`PASS_head_origin_main_aligned`" in map_text
    assert "`produce_read_only_artifacts_run_by_this_gate=false`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_authorization_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_authorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Authorization Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`"
        in packet_text
    )
    assert (
        "`origin_main` | `dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`operator_run_authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET_APPROVED_FOR_ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_OPERATOR_RUN`"
        in packet_text
    )
    assert "`authorized_future_attempt_count` | `1`" in packet_text
    assert "`authorized_source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`authorized_operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert (
        "`authorized_run_id` | `post_d11_direct_mac_read_only_artifacts_001`"
        in packet_text
    )
    assert (
        "`authorized_expected_commit` | `dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`"
        in packet_text
    )
    exact_command = (
        ".venv-312/bin/python tools/ops/gate_d_market_session_operator.py "
        "produce-read-only-artifacts --run-id "
        "post_d11_direct_mac_read_only_artifacts_001 --expected-commit "
        "dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2 "
        "--authorize-direct-mac-terminal-read-only-artifact-production"
    )
    assert exact_command in packet_text
    assert "`expected_commit_must_equal_local_head` | `true`" in packet_text
    assert "`expected_commit_must_equal_origin_main` | `true`" in packet_text
    assert "`clean_worktree_required_before_operator_run` | `true`" in (
        packet_text
    )
    assert (
        "`allowed_later_output_log` | "
        "`logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`"
        in packet_text
    )
    assert (
        "`allowed_later_output_run_report` | "
        "`run_reports/post_d11_direct_mac_read_only_artifacts_001.json`"
        in packet_text
    )
    assert "`allowed_later_output_last_run_report` | `last_run_report.json`" in (
        packet_text
    )
    assert "`prohibited_outputs` | `replay_packages/" in packet_text
    assert "`vps_validation_head_matches_expected` | `PASS_head_matches_expected_dcdf6e9`" in (
        packet_text
    )
    assert "`vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned`" in (
        packet_text
    )
    assert "`vps_validation_pytest` | `121 tests passed`" in packet_text

    for false_field in (
        "`produce_read_only_artifacts_run_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert "exactly one later operator attempt" in packet_text
    assert "LOCAL_MAC only" in packet_text
    assert "DIRECT_MAC_TERMINAL only" in packet_text
    assert "expected commit equals LOCAL_MAC HEAD" in packet_text
    assert "expected commit equals `origin/main`" in packet_text
    assert "clean worktree before the operator run" in packet_text
    assert "no TWS/API/network runtime action" in packet_text
    assert "no VPS runtime action" in packet_text
    assert "no package capture" in packet_text
    assert "no replay" in packet_text
    assert "no scoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no Unit 12" in packet_text
    assert "This authorization packet did not create those outputs" in packet_text
    assert "performed no `produce-read-only-artifacts` run" in packet_text
    assert "no\nartifact production" in packet_text
    assert "no commit, and no push" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Authorization Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET_APPROVED_FOR_ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_OPERATOR_RUN`"
        in map_text
    )
    assert "post_d11_direct_mac_read_only_artifacts_001" in map_text
    assert exact_command in map_text
    assert "`PASS_head_matches_expected_dcdf6e9`" in map_text
    assert "`PASS_head_origin_main_aligned`" in map_text
    assert "`121 tests passed`" in map_text
    assert "`produce_read_only_artifacts_run_by_this_gate=false`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_expected_commit_adjudication_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_expected_commit_adjudication_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Expected-Commit Adjudication Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`"
        in packet_text
    )
    assert (
        "`origin_main` | `44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET_APPROVED_FOR_ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_OPERATOR_RUN`"
        in packet_text
    )
    assert (
        "`prior_authorized_expected_commit` | `dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`"
        in packet_text
    )
    assert (
        "`current_source_of_truth_head` | `44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`"
        in packet_text
    )
    assert (
        "`expected_commit_adjudication_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET_BLOCKED_PENDING_CORRECTED_OPERATOR_RUN_AUTHORIZATION`"
        in packet_text
    )
    assert (
        "`concrete_blocker` | "
        "`AUTHORIZED_EXPECTED_COMMIT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD`"
        in packet_text
    )
    assert "`operator_run_must_not_proceed` | `true`" in packet_text
    assert "`produce_read_only_artifacts_fail_closed_expected` | `true`" in (
        packet_text
    )
    assert (
        "`vps_validation_head_matches_expected` | `PASS_head_matches_expected_44a39de`"
        in packet_text
    )
    assert (
        "`vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned`"
        in packet_text
    )
    assert "`vps_validation_pytest` | `122 tests passed`" in packet_text

    for false_field in (
        "`produce_read_only_artifacts_run_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET`"
        in packet_text
    )
    assert "does not match" in packet_text
    assert "must\nnot proceed" in packet_text
    assert "would fail closed if run with the stale expected commit" in packet_text
    assert "performed no\n`produce-read-only-artifacts` run" in packet_text
    assert "no artifact production" in packet_text
    assert "no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no broker/TWS/API/network/" in packet_text
    assert "runtime action" in packet_text
    assert "no VPS action" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "no commit, and no push" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Expected-Commit Adjudication Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET_BLOCKED_PENDING_CORRECTED_OPERATOR_RUN_AUTHORIZATION`"
        in map_text
    )
    assert "`AUTHORIZED_EXPECTED_COMMIT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD`" in (
        map_text
    )
    assert "`dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`" in map_text
    assert "`44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`" in map_text
    assert "`PASS_head_matches_expected_44a39de`" in map_text
    assert "`PASS_head_origin_main_aligned`" in map_text
    assert "`122 tests passed`" in map_text
    assert "`produce_read_only_artifacts_run_by_this_gate=false`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_authorization_correction_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_authorization_correction_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Authorization Correction Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `6894dcfd62bbfc25a1627e8f7c27089d28fba5a6`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `6894dcfd62bbfc25a1627e8f7c27089d28fba5a6`"
        in packet_text
    )
    assert (
        "`origin_main` | `6894dcfd62bbfc25a1627e8f7c27089d28fba5a6`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET_BLOCKED_PENDING_CORRECTED_OPERATOR_RUN_AUTHORIZATION`"
        in packet_text
    )
    assert (
        "`prior_concrete_blocker` | "
        "`AUTHORIZED_EXPECTED_COMMIT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD`"
        in packet_text
    )
    assert (
        "`authorization_correction_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET_READY_FOR_FINAL_OPERATOR_COMMAND_RESOLUTION`"
        in packet_text
    )
    assert "`authorized_future_attempt_count` | `1`" in packet_text
    assert "`authorized_source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`authorized_operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert (
        "`authorized_run_id` | `post_d11_direct_mac_read_only_artifacts_001`"
        in packet_text
    )
    assert (
        "`corrected_expected_commit_binding` | "
        "`FINAL_VALIDATED_SOURCE_OF_TRUTH_HEAD_AFTER_THIS_CORRECTION_PACKET`"
        in packet_text
    )
    assert "`pre_correction_commit_not_final_expected_commit` | `true`" in (
        packet_text
    )
    corrected_shape = (
        ".venv-312/bin/python tools/ops/gate_d_market_session_operator.py "
        "produce-read-only-artifacts --run-id "
        "post_d11_direct_mac_read_only_artifacts_001 --expected-commit "
        "<FINAL_VALIDATED_SOURCE_OF_TRUTH_HEAD_AFTER_THIS_CORRECTION_PACKET> "
        "--authorize-direct-mac-terminal-read-only-artifact-production"
    )
    assert corrected_shape in packet_text
    assert "`expected_commit_must_equal_local_head_at_operator_run` | `true`" in (
        packet_text
    )
    assert "`expected_commit_must_equal_origin_main_at_operator_run` | `true`" in (
        packet_text
    )
    assert "`clean_worktree_required_before_operator_run` | `true`" in (
        packet_text
    )
    assert (
        "`vps_validation_head_matches_expected` | `PASS_head_matches_expected_6894dcf`"
        in packet_text
    )
    assert (
        "`vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned`"
        in packet_text
    )
    assert "`vps_validation_pytest` | `123 tests passed`" in packet_text

    for false_field in (
        "`produce_read_only_artifacts_run_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET`"
        in packet_text
    )
    assert "does not hardcode the current pre-correction commit" in packet_text
    assert "FINAL_VALIDATED_SOURCE_OF_TRUTH_HEAD_AFTER_THIS_CORRECTION_PACKET" in (
        packet_text
    )
    assert "must be resolved only after this correction packet is committed" in (
        packet_text
    )
    assert "exactly one attempt" in packet_text
    assert "LOCAL_MAC only" in packet_text
    assert "DIRECT_MAC_TERMINAL only" in packet_text
    assert "no TWS/API/network runtime action" in packet_text
    assert "no VPS runtime action" in packet_text
    assert "no package capture" in packet_text
    assert "no replay" in packet_text
    assert "no scoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no Unit 12" in packet_text
    assert "performed no `produce-read-only-artifacts` run" in packet_text
    assert "no\nartifact production" in packet_text
    assert "no commit, and no push" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Authorization Correction Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=6894dcfd62bbfc25a1627e8f7c27089d28fba5a6`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET_READY_FOR_FINAL_OPERATOR_COMMAND_RESOLUTION`"
        in map_text
    )
    assert "`FINAL_VALIDATED_SOURCE_OF_TRUTH_HEAD_AFTER_THIS_CORRECTION_PACKET`" in (
        map_text
    )
    assert corrected_shape in map_text
    assert "`PASS_head_matches_expected_6894dcf`" in map_text
    assert "`PASS_head_origin_main_aligned`" in map_text
    assert "`123 tests passed`" in map_text
    assert "`produce_read_only_artifacts_run_by_this_gate=false`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_final_operator_command_resolution_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_final_operator_command_resolution_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Final Operator Command Resolution Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `83815993c160282f26fe4a3bc9fad92386f8fe50`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `83815993c160282f26fe4a3bc9fad92386f8fe50`"
        in packet_text
    )
    assert (
        "`origin_main` | `83815993c160282f26fe4a3bc9fad92386f8fe50`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET_READY_FOR_FINAL_OPERATOR_COMMAND_RESOLUTION`"
        in packet_text
    )
    assert (
        "`final_command_resolution_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_OPERATOR_RUN`"
        in packet_text
    )
    assert "`authorized_future_attempt_count` | `1`" in packet_text
    assert "`authorized_source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`authorized_operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert (
        "`authorized_run_id` | `post_d11_direct_mac_read_only_artifacts_001`"
        in packet_text
    )
    assert (
        '`expected_commit_resolution` | `EXPECTED_COMMIT="$(git rev-parse HEAD)"'
        in packet_text
    )
    assert "`static_expected_commit_hardcoded_for_operator_run` | `false`" in (
        packet_text
    )
    assert "`expected_commit_must_equal_local_head_at_operator_run` | `true`" in (
        packet_text
    )
    assert "`expected_commit_must_equal_origin_main_at_operator_run` | `true`" in (
        packet_text
    )
    assert "`clean_worktree_required_before_operator_run` | `true`" in (
        packet_text
    )
    assert (
        '`final_resolved_command_shape` | `.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production`'
        in packet_text
    )
    assert (
        "`vps_validation_head_matches_expected` | `PASS_head_matches_expected_8381599`"
        in packet_text
    )
    assert (
        "`vps_validation_head_origin_main_aligned` | `PASS_head_origin_main_aligned`"
        in packet_text
    )
    assert "`vps_validation_pytest` | `124 tests passed`" in packet_text

    for required_line in (
        "git fetch origin main",
        'test "$(git rev-parse --abbrev-ref HEAD)" = "main"',
        'test -z "$(git status --short)"',
        'test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"',
        'EXPECTED_COMMIT="$(git rev-parse HEAD)"',
        'test "$EXPECTED_COMMIT" = "$(git rev-parse origin/main)"',
        '.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production',
    ):
        assert required_line in packet_text

    for false_field in (
        "`produce_read_only_artifacts_run_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert "hardcode `83815993c160282f26fe4a3bc9fad92386f8fe50`" in packet_text
    assert "Expected commit equals LOCAL_MAC HEAD" not in packet_text
    assert "expected commit equals LOCAL_MAC HEAD" in packet_text
    assert "expected commit equals `origin/main`" in packet_text
    assert "worktree is clean before the operator run" in packet_text
    assert "no TWS/API/network runtime action" in packet_text
    assert "no VPS runtime action" in packet_text
    assert "no package capture" in packet_text
    assert "no replay" in packet_text
    assert "no scoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no Unit 12" in packet_text
    assert "performed no `produce-read-only-artifacts`\nrun" in packet_text
    assert "no artifact production" in packet_text
    assert "no commit, and no push" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Final Operator Command Resolution Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=83815993c160282f26fe4a3bc9fad92386f8fe50`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_OPERATOR_RUN`"
        in map_text
    )
    assert 'EXPECTED_COMMIT="$(git rev-parse HEAD)"' in map_text
    assert '--expected-commit "$EXPECTED_COMMIT"' in map_text
    assert "`PASS_head_matches_expected_8381599`" in map_text
    assert "`PASS_head_origin_main_aligned`" in map_text
    assert "`124 tests passed`" in map_text
    assert "`produce_read_only_artifacts_run_by_this_gate=false`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `9de2ae86961fce1602895d0caa96063ed7dc2f27`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `9de2ae86961fce1602895d0caa96063ed7dc2f27`"
        in packet_text
    )
    assert (
        "`origin_main` | `9de2ae86961fce1602895d0caa96063ed7dc2f27`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FINAL_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_OPERATOR_RUN`"
        in packet_text
    )
    assert (
        "`operator_run_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET_FAILED_BEFORE_ARTIFACT_PRODUCTION_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`concrete_blocker` | "
        "`DIRECT_SCRIPT_INVOCATION_DOES_NOT_RESOLVE_REPO_ROOT_TOOLS_PACKAGE_IMPORT`"
        in packet_text
    )
    assert (
        "`attempted_run_id` | `post_d11_direct_mac_read_only_artifacts_001`"
        in packet_text
    )
    assert (
        "`runtime_resolved_expected_commit` | `9de2ae86961fce1602895d0caa96063ed7dc2f27`"
        in packet_text
    )
    assert (
        'produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT"'
        in packet_text
    )
    assert "`observed_exception_type` | `ModuleNotFoundError`" in packet_text
    assert "`observed_exception_message` | `No module named 'tools'`" in (
        packet_text
    )
    assert "`failed_before_artifact_production` | `true`" in packet_text
    assert "`rerun_authorized_by_this_packet` | `false`" in packet_text
    assert "`production_code_changed_by_this_packet` | `false`" in packet_text
    assert "`command_invocation_changed_by_this_packet` | `false`" in packet_text
    assert (
        "`log_artifact_status` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl=ABSENT`"
        in packet_text
    )
    assert (
        "`run_report_artifact_status` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json=ABSENT`"
        in packet_text
    )
    assert "`last_run_report_status` | `last_run_report.json=ABSENT`" in (
        packet_text
    )
    assert "`replay_packages_status` | `replay_packages=ABSENT`" in packet_text
    assert "`order_state_status` | `order_state.json=ABSENT`" in packet_text

    for false_field in (
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET`"
        in packet_text
    )
    assert "failed before\nartifact production" in packet_text
    assert "No module named 'tools'" in packet_text
    assert "does not authorize a rerun" in packet_text
    assert "does not correct the\ninvocation context" in packet_text
    assert "`logs/post_d11_direct_mac_read_only_artifacts_001.jsonl` | `ABSENT`" in (
        packet_text
    )
    assert (
        "`run_reports/post_d11_direct_mac_read_only_artifacts_001.json` | `ABSENT`"
        in packet_text
    )
    assert "`last_run_report.json` | `ABSENT`" in packet_text
    assert "`replay_packages` | `ABSENT`" in packet_text
    assert "`order_state.json` | `ABSENT`" in packet_text
    assert "performed no rerun" in packet_text
    assert "no `produce-read-only-artifacts`\nrun" in packet_text
    assert "no artifact production" in packet_text
    assert "no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "no production code change" in packet_text
    assert "no command invocation change" in packet_text
    assert "no\ncommit, and no push" in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=9de2ae86961fce1602895d0caa96063ed7dc2f27`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET_FAILED_BEFORE_ARTIFACT_PRODUCTION_WITH_CONCRETE_BLOCKER`"
        in map_text
    )
    assert "`DIRECT_SCRIPT_INVOCATION_DOES_NOT_RESOLVE_REPO_ROOT_TOOLS_PACKAGE_IMPORT`" in (
        map_text
    )
    assert "`ModuleNotFoundError: No module named 'tools'`" in map_text
    assert "post_d11_direct_mac_read_only_artifacts_001" in map_text
    assert "`9de2ae86961fce1602895d0caa96063ed7dc2f27`" in map_text
    assert "`produce_read_only_artifacts_rerun_by_this_gate=false`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_invocation_context_correction_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_invocation_context_correction_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Invocation Context Correction Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `47968d8ad0bcc785f1cebb0653696883db2f4885`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `47968d8ad0bcc785f1cebb0653696883db2f4885`"
        in packet_text
    )
    assert (
        "`origin_main` | `47968d8ad0bcc785f1cebb0653696883db2f4885`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET_FAILED_BEFORE_ARTIFACT_PRODUCTION_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`prior_concrete_blocker` | "
        "`DIRECT_SCRIPT_INVOCATION_DOES_NOT_RESOLVE_REPO_ROOT_TOOLS_PACKAGE_IMPORT`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_47968d8`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`126 tests passed`" in packet_text
    assert (
        "`invocation_context_correction_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET_READY_FOR_CORRECTED_OPERATOR_COMMAND_RESOLUTION`"
        in packet_text
    )
    assert (
        ".venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts"
        in packet_text
    )
    assert (
        ".venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts"
        in packet_text
    )
    assert "--run-id post_d11_direct_mac_read_only_artifacts_001" in packet_text
    assert '--expected-commit "$EXPECTED_COMMIT"' in packet_text
    assert (
        "--authorize-direct-mac-terminal-read-only-artifact-production"
        in packet_text
    )
    assert 'EXPECTED_COMMIT="$(git rev-parse HEAD)"' in packet_text

    for command_line in (
        "git fetch origin main",
        'test "$(git rev-parse --abbrev-ref HEAD)" = "main"',
        'test -z "$(git status --short)"',
        'test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"',
        'EXPECTED_COMMIT="$(git rev-parse HEAD)"',
        'test "$EXPECTED_COMMIT" = "$(git rev-parse origin/main)"',
        '.venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production',
    ):
        assert command_line in packet_text

    for false_field in (
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`command_surface_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert "no\n`produce-read-only-artifacts` run" in packet_text
    assert "no artifact production" in packet_text
    assert "no package capture" in packet_text
    assert "no replay, no scoring" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "no production code change" in packet_text
    assert "no\ncommand-surface code change" in packet_text
    assert "no commit, and no push" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Invocation Context Correction Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=47968d8ad0bcc785f1cebb0653696883db2f4885`" in (
        map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET_READY_FOR_CORRECTED_OPERATOR_COMMAND_RESOLUTION`"
        in map_text
    )
    assert "`DIRECT_SCRIPT_INVOCATION_DOES_NOT_RESOLVE_REPO_ROOT_TOOLS_PACKAGE_IMPORT`" in (
        map_text
    )
    assert (
        ".venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts"
        in map_text
    )
    assert 'EXPECTED_COMMIT="$(git rev-parse HEAD)"' in map_text
    assert "`PASS_head_matches_expected_47968d8`" in map_text
    assert "`126 tests passed`" in map_text
    assert "`produce_read_only_artifacts_rerun_by_this_gate=false`" in map_text
    assert "`package_capture_execution=NOT_AUTHORIZED`" in map_text
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_corrected_operator_command_resolution_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_corrected_operator_command_resolution_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Corrected Operator Command Resolution Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `b431a5389ee991e52806e8dd982eba9666f10581`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `b431a5389ee991e52806e8dd982eba9666f10581`"
        in packet_text
    )
    assert (
        "`origin_main` | `b431a5389ee991e52806e8dd982eba9666f10581`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_INVOCATION_CONTEXT_CORRECTION_PACKET_READY_FOR_CORRECTED_OPERATOR_COMMAND_RESOLUTION`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_b431a53`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`127 tests passed`" in packet_text
    assert (
        "`prior_failed_invocation_shape` | "
        "`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts"
        in packet_text
    )
    assert "`prior_failure` | `ModuleNotFoundError: No module named 'tools'`" in (
        packet_text
    )
    assert (
        "`corrected_invocation_shape` | "
        "`.venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts"
        in packet_text
    )
    assert (
        "`authorized_run_id` | `post_d11_direct_mac_read_only_artifacts_001`"
        in packet_text
    )
    assert (
        "`expected_commit_resolution` | `EXPECTED_COMMIT=\"$(git rev-parse HEAD)\"`"
        in packet_text
    )
    assert (
        "`expected_commit_terminal_evidence` | `echo \"EXPECTED_COMMIT=$EXPECTED_COMMIT\"`"
        in packet_text
    )
    assert (
        "`corrected_operator_command_resolution_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_CORRECTED_OPERATOR_RUN`"
        in packet_text
    )

    for command_line in (
        "git fetch origin main",
        'test "$(git rev-parse --abbrev-ref HEAD)" = "main"',
        'test -z "$(git status --short)"',
        'test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"',
        'EXPECTED_COMMIT="$(git rev-parse HEAD)"',
        'test "$EXPECTED_COMMIT" = "$(git rev-parse origin/main)"',
        'echo "EXPECTED_COMMIT=$EXPECTED_COMMIT"',
        '.venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit "$EXPECTED_COMMIT" --authorize-direct-mac-terminal-read-only-artifact-production',
    ):
        assert command_line in packet_text

    for false_field in (
        "`produce_read_only_artifacts_run_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action` | `false`",
        "`scheduler_service_systemd_timer_mutation` | `false`",
        "`credential_env_mutation` | `false`",
        "`strategy_risk_execution_behavior_change` | `false`",
        "`provider_selection_or_broker_behavior_change` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Runtime artifact production execution in this gate | `NOT_PERFORMED` |",
        "| Package capture execution in this gate | `NOT_AUTHORIZED` |",
        "| Package capture beyond later single corrected read-only operator run | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this gate | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert "no `produce-read-only-artifacts` run in this gate" in packet_text
    assert "no artifact production in this gate" in packet_text
    assert "no package capture execution in this gate" in packet_text
    assert "no replay" in packet_text
    assert "no scoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "no broker/TWS/API/network/runtime action" in packet_text
    assert "no VPS runtime action" in packet_text
    assert "no production code change" in packet_text
    assert "no\ncommit, and no push" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Corrected Operator Command Resolution Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=b431a5389ee991e52806e8dd982eba9666f10581`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_b431a53`" in map_text
    assert "`127 tests passed`" in map_text
    assert "`ModuleNotFoundError: No module named 'tools'`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_CORRECTED_OPERATOR_RUN`"
        in map_text
    )
    assert 'echo "EXPECTED_COMMIT=$EXPECTED_COMMIT"' in map_text
    assert (
        ".venv-312/bin/python -m tools.ops.gate_d_market_session_operator produce-read-only-artifacts"
        in map_text
    )
    assert "`produce_read_only_artifacts_run_by_this_gate=false`" in map_text
    assert (
        "`package_capture_execution=NOT_AUTHORIZED_BEYOND_LATER_SINGLE_CORRECTED_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN`"
        in map_text
    )
    assert (
        "`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`"
        in map_text
    )
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_corrected_operator_run_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_corrected_operator_run_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Corrected Operator Run Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert (
        "`origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_COMMAND_RESOLUTION_PACKET_READY_FOR_ONE_BOUNDED_CORRECTED_OPERATOR_RUN`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_ac75080`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`128 tests passed`" in packet_text
    assert (
        "`corrected_operator_run_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET_COMPLETED_READ_ONLY_ARTIFACT_PRODUCTION`"
        in packet_text
    )
    assert "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`" in (
        packet_text
    )
    assert (
        "`expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert (
        "`actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert (
        "`origin_main_observed` | `ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert "`source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert "`read_only_authority` | `true`" in packet_text
    assert (
        "`operator_run_final_classification` | "
        "`DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED`"
        in packet_text
    )

    for false_field in (
        "`tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`package_capture_executed` | `false`",
        "`replay_executed` | `false`",
        "`scoring_executed` | `false`",
        "`candidate_generation_executed` | `false`",
        "`unit_12_action` | `false`",
        "`order_state_bound` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_production_performed_by_this_packet` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`scheduler_service_systemd_timer_mutation` | `false`",
        "`credential_env_mutation` | `false`",
        "`strategy_risk_execution_behavior_change` | `false`",
        "`provider_selection_or_broker_behavior_change` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert (
        "`log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`"
        in packet_text
    )
    assert (
        "`log_artifact_sha256` | "
        "`7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`"
        in packet_text
    )
    assert (
        "`run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json`"
        in packet_text
    )
    assert (
        "`run_report_artifact_sha256` | "
        "`fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`"
        in packet_text
    )
    assert "`last_run_report_path` | `last_run_report.json`" in packet_text
    assert (
        "`last_run_report_sha256` | "
        "`fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`"
        in packet_text
    )
    assert (
        "`post_run_log_artifact_inventory` | `PRESENT_logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`"
        in packet_text
    )
    assert (
        "`post_run_run_report_inventory` | `PRESENT_run_reports/post_d11_direct_mac_read_only_artifacts_001.json`"
        in packet_text
    )
    assert (
        "`post_run_last_run_report_inventory` | `PRESENT_last_run_report.json`"
        in packet_text
    )
    assert "`post_run_replay_packages_inventory` | `ABSENT_replay_packages`" in (
        packet_text
    )
    assert "`post_run_order_state_inventory` | `ABSENT_order_state.json`" in (
        packet_text
    )

    for authority in (
        "| Broker submit readiness | `NOT_APPROVED` |",
        "| Live trading readiness | `NOT_APPROVED` |",
        "| Account authority | `NONE` |",
        "| Order authority | `NONE` |",
        "| Execution authority | `NONE` |",
        "| Package capture execution | `NOT_AUTHORIZED` |",
        "| Replay execution | `NOT_AUTHORIZED` |",
        "| Scoring execution | `NOT_AUTHORIZED` |",
        "| Candidate generation execution | `NOT_AUTHORIZED` |",
        "| Unit 12 implementation | `NOT_OPENED` |",
        "| VPS action by this packet | `NOT_AUTHORIZED` |",
        "| Bounded VPS execution | `NOT_AUTHORIZED` |",
    ):
        assert authority in packet_text

    assert "no rerun by this packet" in packet_text
    assert "no package capture" in packet_text
    assert "no replay" in packet_text
    assert "no scoring" in packet_text
    assert "no candidate generation" in packet_text
    assert "no Unit 12 action" in packet_text
    assert "no production code change" in packet_text
    assert "no commit,\nand no push" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Corrected Operator Run Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=ac75080419e910c39f1a2683641a603f8a8999a1`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_ac75080`" in map_text
    assert "`128 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET_COMPLETED_READ_ONLY_ARTIFACT_PRODUCTION`"
        in map_text
    )
    assert "`EXPECTED_COMMIT=ac75080419e910c39f1a2683641a603f8a8999a1`" in (
        map_text
    )
    assert (
        "`sha256=7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`"
        in map_text
    )
    assert (
        "`sha256=fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`"
        in map_text
    )
    assert "`ABSENT_replay_packages`" in map_text
    assert "`ABSENT_order_state.json`" in map_text
    assert "`package_capture_executed=false`" in map_text
    assert "`order_state_bound=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_artifact_adjudication_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_artifact_adjudication_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Artifact Adjudication Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `f65222c59a244f8a784565295f699001a0027ded`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `f65222c59a244f8a784565295f699001a0027ded`"
        in packet_text
    )
    assert (
        "`origin_main` | `f65222c59a244f8a784565295f699001a0027ded`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_CORRECTED_OPERATOR_RUN_PACKET_COMPLETED_READ_ONLY_ARTIFACT_PRODUCTION`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_f65222c`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`129 tests passed`" in packet_text
    assert (
        "`artifact_adjudication_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`concrete_blocker` | "
        "`PRODUCED_ARTIFACT_COMMIT_ALIGNMENT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD`"
        in packet_text
    )
    assert (
        "`required_alignment_commit` | `f65222c59a244f8a784565295f699001a0027ded`"
        in packet_text
    )
    for observed_commit_field in (
        "`observed_artifact_expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`observed_artifact_actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`observed_artifact_origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
    ):
        assert observed_commit_field in packet_text
    assert (
        "`commit_alignment_result` | "
        "`FAIL_REQUIRED_f65222c59a244f8a784565295f699001a0027ded_OBSERVED_ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert "`run_id_alignment` | `PASS_post_d11_direct_mac_read_only_artifacts_001`" in (
        packet_text
    )
    assert (
        "`final_classification_alignment` | "
        "`PASS_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED`"
        in packet_text
    )

    for hash_field in (
        "`observed_log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`observed_run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`observed_last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`log_artifact_hash_result` | `PASS`",
        "`run_report_artifact_hash_result` | `PASS`",
        "`last_run_report_hash_result` | `PASS`",
    ):
        assert hash_field in packet_text
    assert "`last_run_report_byte_identical_to_run_report` | `true`" in packet_text
    assert "`last_run_report_hash_identical_to_run_report` | `true`" in packet_text
    assert "`replay_packages_absence_result` | `PASS_ABSENT_replay_packages`" in (
        packet_text
    )
    assert "`order_state_absence_result` | `PASS_ABSENT_order_state.json`" in (
        packet_text
    )

    for false_field in (
        "`tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`package_capture_executed` | `false`",
        "`replay_executed` | `false`",
        "`scoring_executed` | `false`",
        "`candidate_generation_executed` | `false`",
        "`unit_12_action` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_files_modified_by_this_gate` | `false`",
        "`artifact_git_add_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`scheduler_service_systemd_timer_mutation` | `false`",
        "`credential_env_mutation` | `false`",
        "`strategy_risk_execution_behavior_change` | `false`",
        "`provider_selection_or_broker_behavior_change` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert "`expected_commit` | `f65222c59a244f8a784565295f699001a0027ded` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `FAIL` |" in (
        packet_text
    )
    assert "`actual_head` | `f65222c59a244f8a784565295f699001a0027ded` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `FAIL` |" in (
        packet_text
    )
    assert "`origin_main` | `f65222c59a244f8a784565295f699001a0027ded` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `FAIL` |" in (
        packet_text
    )
    assert "The passing clean adjudication decision is not used" in packet_text
    assert "byte-identical and hash-identical" in packet_text
    assert "did not add produced artifacts to git" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Artifact Adjudication Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=f65222c59a244f8a784565295f699001a0027ded`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_f65222c`" in map_text
    assert "`129 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in map_text
    )
    assert (
        "`PRODUCED_ARTIFACT_COMMIT_ALIGNMENT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD`"
        in map_text
    )
    assert "`observed_artifact_expected_commit=ac75080419e910c39f1a2683641a603f8a8999a1`" in (
        map_text
    )
    assert (
        "`sha256=7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`"
        in map_text
    )
    assert (
        "`sha256=fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`"
        in map_text
    )
    assert "`PASS_ABSENT_replay_packages`" in map_text
    assert "`PASS_ABSENT_order_state.json`" in map_text
    assert "`artifact_git_add_performed_by_this_gate=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_artifact_alignment_remediation_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_artifact_alignment_remediation_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Artifact Alignment Remediation Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b`"
        in packet_text
    )
    assert (
        "`origin_main` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ADJUDICATION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`prior_concrete_blocker` | "
        "`PRODUCED_ARTIFACT_COMMIT_ALIGNMENT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_8191b9f`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`130 tests passed`" in packet_text
    assert (
        "`artifact_alignment_remediation_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET_READY_FOR_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_RETRY`"
        in packet_text
    )
    assert (
        "`remediated_alignment_rule` | "
        "`ARTIFACT_BYTES_ALIGN_TO_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_NOT_LATER_DOCUMENTATION_COMMITS`"
        in packet_text
    )
    for runtime_anchor in (
        "`artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`artifact_expected_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`artifact_actual_head_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`artifact_origin_main_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
    ):
        assert runtime_anchor in packet_text
    assert (
        "`corrected_operator_run_packet_commit` | `f65222c59a244f8a784565295f699001a0027ded`"
        in packet_text
    )
    assert (
        "`blocked_adjudication_packet_commit` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b`"
        in packet_text
    )
    assert (
        "`documentation_lineage_commits_are_artifact_runtime_anchors` | `false`"
        in packet_text
    )
    assert "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`" in (
        packet_text
    )
    assert (
        "`run_id_rule` | `MUST_MATCH_post_d11_direct_mac_read_only_artifacts_001`"
        in packet_text
    )
    assert (
        "`last_run_report_alignment_rule` | "
        "`MUST_BE_BYTE_IDENTICAL_AND_HASH_IDENTICAL_TO_RUN_REPORT`"
        in packet_text
    )
    assert "`replay_packages_rule` | `MUST_REMAIN_ABSENT`" in packet_text
    assert "`order_state_json_rule` | `MUST_REMAIN_ABSENT`" in packet_text
    assert (
        "`artifact_git_add_rule` | `MUST_NOT_ADD_PRODUCED_ARTIFACTS_TO_GIT`"
        in packet_text
    )
    for sha_field in (
        "`log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
    ):
        assert sha_field in packet_text

    for false_field in (
        "`tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`package_capture_executed` | `false`",
        "`replay_executed` | `false`",
        "`scoring_executed` | `false`",
        "`candidate_generation_executed` | `false`",
        "`unit_12_action` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_files_modified_by_this_gate` | `false`",
        "`artifact_git_add_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`scheduler_service_systemd_timer_mutation` | `false`",
        "`credential_env_mutation` | `false`",
        "`strategy_risk_execution_behavior_change` | `false`",
        "`provider_selection_or_broker_behavior_change` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert "infinite\ndocumentation-commit loop" in packet_text
    assert "later documentation/adjudication\nsource-control commits" in packet_text
    assert "documentation lineage commits. They are not artifact runtime\nanchors" in (
        packet_text
    )
    assert "no produced artifact git-add" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Artifact Alignment Remediation Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=8191b9f7af769f734d77dc0a564ca74ae3b6286b`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_8191b9f`" in map_text
    assert "`130 tests passed`" in map_text
    assert (
        "`ARTIFACT_BYTES_ALIGN_TO_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_NOT_LATER_DOCUMENTATION_COMMITS`"
        in map_text
    )
    assert "`ac75080419e910c39f1a2683641a603f8a8999a1`" in map_text
    assert "`f65222c59a244f8a784565295f699001a0027ded`" in map_text
    assert "`8191b9f7af769f734d77dc0a564ca74ae3b6286b`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET_READY_FOR_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_RETRY`"
        in map_text
    )
    assert "`artifact_git_add_performed_by_this_gate=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_runtime_commit_aligned_artifact_adjudication_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_runtime_commit_aligned_artifact_adjudication_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Runtime-Commit-Aligned Artifact Adjudication Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `bf1ab29063e38b222946dff93cc7ea4c0b044409`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `bf1ab29063e38b222946dff93cc7ea4c0b044409`"
        in packet_text
    )
    assert (
        "`origin_main` | `bf1ab29063e38b222946dff93cc7ea4c0b044409`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_ARTIFACT_ALIGNMENT_REMEDIATION_PACKET_READY_FOR_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_RETRY`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_bf1ab29`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`131 tests passed`" in packet_text
    assert (
        "`runtime_commit_aligned_artifact_adjudication_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET_ARTIFACTS_ADJUDICATED_CLEAN`"
        in packet_text
    )
    assert "`corrected_alignment_rule_applied` | `true`" in packet_text
    assert (
        "`alignment_rule` | "
        "`ARTIFACT_BYTES_ALIGN_TO_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_NOT_LATER_DOCUMENTATION_COMMITS`"
        in packet_text
    )
    for runtime_field in (
        "`artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`artifact_expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`artifact_actual_head` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`artifact_origin_main` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`artifact_runtime_commit_internal_alignment` | `PASS`",
    ):
        assert runtime_field in packet_text
    for lineage_field in (
        "`documentation_lineage_commit_after_operator_run_packet` | `f65222c59a244f8a784565295f699001a0027ded`",
        "`documentation_lineage_commit_blocked_adjudication_packet` | `8191b9f7af769f734d77dc0a564ca74ae3b6286b`",
        "`documentation_lineage_commit_alignment_remediation_packet` | `bf1ab29063e38b222946dff93cc7ea4c0b044409`",
        "`documentation_lineage_commits_are_artifact_runtime_anchors` | `false`",
    ):
        assert lineage_field in packet_text
    assert "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`" in (
        packet_text
    )
    assert "`run_id_alignment` | `PASS_post_d11_direct_mac_read_only_artifacts_001`" in (
        packet_text
    )

    for hash_field in (
        "`observed_log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`observed_run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`observed_last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`log_artifact_hash_result` | `PASS`",
        "`run_report_artifact_hash_result` | `PASS`",
        "`last_run_report_hash_result` | `PASS`",
    ):
        assert hash_field in packet_text
    assert "`last_run_report_byte_identical_to_run_report` | `true`" in packet_text
    assert "`last_run_report_hash_identical_to_run_report` | `true`" in packet_text
    assert "`replay_packages_absence_result` | `PASS_ABSENT_replay_packages`" in (
        packet_text
    )
    assert "`order_state_absence_result` | `PASS_ABSENT_order_state.json`" in (
        packet_text
    )
    assert "`produced_artifacts_added_to_git` | `false`" in packet_text
    assert "`package_capture_has_been_run` | `false`" in packet_text

    for false_field in (
        "`tws_api_network_runtime_action` | `false`",
        "`vps_action` | `false`",
        "`package_capture_executed` | `false`",
        "`replay_executed` | `false`",
        "`scoring_executed` | `false`",
        "`candidate_generation_executed` | `false`",
        "`unit_12_action` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_files_modified_by_this_gate` | `false`",
        "`artifact_git_add_performed_by_this_gate` | `false`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`scheduler_service_systemd_timer_mutation` | `false`",
        "`credential_env_mutation` | `false`",
        "`strategy_risk_execution_behavior_change` | `false`",
        "`provider_selection_or_broker_behavior_change` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert "Artifact byte evidence must align to the artifact-production runtime commit" in (
        packet_text
    )
    assert "must not be required\nto align to later documentation/adjudication commits" in (
        packet_text
    )
    assert "| Artifact `expected_commit` | `ac75080419e910c39f1a2683641a603f8a8999a1` | `PASS` |" in (
        packet_text
    )
    assert "byte-identical and hash-identical" in packet_text
    assert "`replay_packages` | `PASS_ABSENT_replay_packages`" in packet_text
    assert "`order_state.json` | `PASS_ABSENT_order_state.json`" in packet_text
    assert "Produced artifacts added to git | `false`" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Runtime-Commit-Aligned Artifact Adjudication Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=bf1ab29063e38b222946dff93cc7ea4c0b044409`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_bf1ab29`" in map_text
    assert "`131 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET_ARTIFACTS_ADJUDICATED_CLEAN`"
        in map_text
    )
    assert (
        "`ARTIFACT_BYTES_ALIGN_TO_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_NOT_LATER_DOCUMENTATION_COMMITS`"
        in map_text
    )
    assert "`ac75080419e910c39f1a2683641a603f8a8999a1`" in map_text
    assert "`f65222c59a244f8a784565295f699001a0027ded`" in map_text
    assert "`8191b9f7af769f734d77dc0a564ca74ae3b6286b`" in map_text
    assert "`bf1ab29063e38b222946dff93cc7ea4c0b044409`" in map_text
    assert "`PASS_ABSENT_replay_packages`" in map_text
    assert "`PASS_ABSENT_order_state.json`" in map_text
    assert "`produced_artifacts_added_to_git=false`" in map_text
    assert "`package_capture_has_been_run=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_authorization_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_authorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Authorization Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `7829aa5c5d4aee36f70218724b774238a56ac4ef`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `7829aa5c5d4aee36f70218724b774238a56ac4ef`"
        in packet_text
    )
    assert (
        "`origin_main` | `7829aa5c5d4aee36f70218724b774238a56ac4ef`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUNTIME_COMMIT_ALIGNED_ARTIFACT_ADJUDICATION_PACKET_ARTIFACTS_ADJUDICATED_CLEAN`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_7829aa5`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`132 tests passed`" in packet_text
    assert (
        "`package_capture_authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET_READY_FOR_PACKAGE_CAPTURE_COMMAND_RESOLUTION`"
        in packet_text
    )
    assert "`authorization_scope` | `PACKAGE_CAPTURE_COMMAND_RESOLUTION_ONLY`" in (
        packet_text
    )
    assert "`package_capture_execution_authorized_by_this_packet` | `false`" in (
        packet_text
    )
    assert "`package_capture_command_resolution_authorized_by_this_packet` | `true`" in (
        packet_text
    )
    for false_authorization in (
        "`replay_authorized` | `false`",
        "`scoring_authorized` | `false`",
        "`candidate_generation_authorized` | `false`",
        "`unit_12_authorized` | `false`",
        "`broker_runtime_account_order_execution_authority_authorized` | `false`",
        "`vps_runtime_action_authorized` | `false`",
        "`artifact_modification_authorized` | `false`",
        "`produced_artifact_git_add_authorized` | `false`",
    ):
        assert false_authorization in packet_text

    assert "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`" in (
        packet_text
    )
    assert (
        "`artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`"
        in packet_text
    )
    assert (
        "`command_resolution_authorization_source_commit` | `7829aa5c5d4aee36f70218724b774238a56ac4ef`"
        in packet_text
    )
    for artifact_anchor in (
        "`log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`",
        "`log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json`",
        "`run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_path` | `last_run_report.json`",
        "`last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_identity` | `BYTE_IDENTICAL_AND_HASH_IDENTICAL_TO_RUN_REPORT`",
    ):
        assert artifact_anchor in packet_text

    assert "`replay_packages_current_state` | `ABSENT`" in packet_text
    assert "`order_state_json_current_state` | `ABSENT`" in packet_text
    assert (
        "`future_package_output_boundary` | "
        "`BOUNDED_REPLAY_PACKAGE_UNDER_REPLAY_PACKAGES_FOR_ADJUDICATED_RUN_ID_ONLY`"
        in packet_text
    )
    assert (
        "`future_package_capture_broker_state_boundary` | "
        "`READ_ONLY_WITH_RESPECT_TO_BROKER_ACCOUNT_ORDER_EXECUTION_STATE`"
        in packet_text
    )
    assert (
        "`future_order_state_boundary` | "
        "`MUST_NOT_READ_WRITE_REQUIRE_OR_BIND_ORDER_STATE_JSON_UNLESS_LATER_PACKET_EXPLICITLY_AUTHORIZES`"
        in packet_text
    )
    assert (
        "`future_source_artifact_mutation_boundary` | `MUST_NOT_MUTATE_SOURCE_ARTIFACTS`"
        in packet_text
    )
    assert (
        "`future_artifact_git_add_boundary` | "
        "`MUST_NOT_ADD_LOGS_RUN_REPORTS_LAST_RUN_REPORT_REPLAY_PACKAGES_OR_ORDER_STATE_TO_GIT`"
        in packet_text
    )

    for false_field in (
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_packages_created_by_this_gate` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_files_modified_by_this_gate` | `false`",
        "`artifact_git_add_performed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`scheduler_service_systemd_timer_mutation` | `false`",
        "`credential_env_mutation` | `false`",
        "`strategy_risk_execution_behavior_change` | `false`",
        "`provider_selection_or_broker_behavior_change` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    for authority in (
        "`broker_submit_readiness` | `NOT_APPROVED`",
        "`live_trading_readiness` | `NOT_APPROVED`",
        "`account_authority` | `NONE`",
        "`order_authority` | `NONE`",
        "`execution_authority` | `NONE`",
    ):
        assert authority in packet_text

    assert "authorizes only the next package-capture command-resolution packet" in (
        packet_text
    )
    assert "does not authorize package-capture execution" in packet_text
    assert "created\nno `replay_packages`" in packet_text
    assert "added no artifacts to git" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Authorization Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=7829aa5c5d4aee36f70218724b774238a56ac4ef`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_7829aa5`" in map_text
    assert "`132 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET_READY_FOR_PACKAGE_CAPTURE_COMMAND_RESOLUTION`"
        in map_text
    )
    assert "`package_capture_execution_authorized_by_this_packet=false`" in (
        map_text
    )
    assert "`package_capture_command_resolution_authorized_by_this_packet=true`" in (
        map_text
    )
    assert "`post_d11_direct_mac_read_only_artifacts_001`" in map_text
    assert "`ac75080419e910c39f1a2683641a603f8a8999a1`" in map_text
    assert "`7829aa5c5d4aee36f70218724b774238a56ac4ef`" in map_text
    assert (
        "`MUST_NOT_READ_WRITE_REQUIRE_OR_BIND_ORDER_STATE_JSON_UNLESS_LATER_PACKET_EXPLICITLY_AUTHORIZES`"
        in map_text
    )
    assert "`replay_packages_created_by_this_gate=false`" in map_text
    assert "`artifact_git_add_performed_by_this_gate=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_command_resolution_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_command_resolution_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Resolution Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert (
        "`local_head` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b`"
        in packet_text
    )
    assert (
        "`origin_main` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b`"
        in packet_text
    )
    assert "`worktree` | `clean`" in packet_text
    assert (
        "`prior_packet` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET_READY_FOR_PACKAGE_CAPTURE_COMMAND_RESOLUTION`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_a910514`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`133 tests passed`" in packet_text
    assert (
        "`package_capture_command_resolution_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in packet_text
    )
    assert (
        "`concrete_blocker` | "
        "`NO_SUPPORTED_LOCAL_MAC_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE`"
        in packet_text
    )
    assert "`supported_package_capture_command_resolved` | `false`" in packet_text
    assert "`resolved_future_operator_command` | `NONE_BLOCKED`" in packet_text

    for anchor in (
        "`authorization_source_commit` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b`",
        "`artifact_adjudication_source_commit` | `7829aa5c5d4aee36f70218724b774238a56ac4ef`",
        "`artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`",
        "`log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`",
        "`log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json`",
        "`run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_path` | `last_run_report.json`",
        "`last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_identity` | `BYTE_IDENTICAL_AND_HASH_IDENTICAL_TO_RUN_REPORT`",
    ):
        assert anchor in packet_text

    assert "`replay_packages_current_state` | `ABSENT`" in packet_text
    assert "`order_state_json_current_state` | `ABSENT`" in packet_text
    assert (
        "`expected_future_package_output_path` | "
        "`replay_packages/post_d11_direct_mac_read_only_artifacts_001`"
        in packet_text
    )
    assert (
        "`capture_local_resolution_result` | "
        "`UNSUPPORTED_FOR_PACKAGE_CAPTURE_EXECUTION_PREFLIGHT_ONLY_DOES_NOT_WRITE_REPLAY_PACKAGE`"
        in packet_text
    )
    assert (
        "`legacy_capture_resolution_result` | "
        "`UNSUPPORTED_FOR_LOCAL_MAC_ONLY_DELEGATES_TO_EXECUTION_MODE_VPS_AND_VPS_PACKAGE_WRITE_AUTHORITY`"
        in packet_text
    )
    assert (
        "`package_execution_orchestrator_resolution_result` | "
        "`UNSUPPORTED_FOR_LOCAL_MAC_ONLY_VPS_EXECUTION_REQUIRES_SEPARATE_BOUNDED_VPS_EXECUTION_GATE`"
        in packet_text
    )

    for false_field in (
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_packages_created_by_this_gate` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_files_modified_by_this_gate` | `false`",
        "`artifact_git_add_performed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`scheduler_service_systemd_timer_mutation` | `false`",
        "`credential_env_mutation` | `false`",
        "`strategy_risk_execution_behavior_change` | `false`",
        "`provider_selection_or_broker_behavior_change` | `false`",
        "`production_code_changed_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert "No supported command was resolved for this exact boundary" in packet_text
    assert "LOCAL_MAC preflight surface only; does not write a replay package" in (
        packet_text
    )
    assert "Delegates to `package_execution_orchestrator.main` with `--execution-mode vps`" in (
        packet_text
    )
    assert "VPS execution requires separate bounded VPS execution authorization" in (
        packet_text
    )
    assert "replay_packages/post_d11_direct_mac_read_only_artifacts_001" in (
        packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Resolution Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=a910514f693c2ffbcbe8b6ed499811c37904ec4b`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_a910514`" in map_text
    assert "`133 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`"
        in map_text
    )
    assert "`NO_SUPPORTED_LOCAL_MAC_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE`" in (
        map_text
    )
    assert "capture-local" in map_text
    assert "--execution-mode vps" in map_text
    assert "`supported_package_capture_command_resolved=false`" in map_text
    assert "`replay_packages_created_by_this_gate=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_command_surface_remediation_packet() -> None:
    from tools.ops import gate_d_market_session_operator as operator

    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_command_surface_remediation_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")
    operator_source = Path("tools/ops/gate_d_market_session_operator.py").read_text(
        encoding="utf-8"
    )
    local_surface_source = operator_source.split(
        "def _direct_mac_terminal_read_only_package_checks", 1
    )[1].split("\ndef produce_read_only_artifacts", 1)[0]

    parser = operator.build_parser()
    args = parser.parse_args(
        [
            "capture-local-read-only-package",
            "--run-id",
            "post_d11_direct_mac_read_only_artifacts_001",
            "--expected-commit",
            "42a72f0814b49c31500031e83e1c737cdee8c8a3",
            "--artifact-runtime-commit",
            "ac75080419e910c39f1a2683641a603f8a8999a1",
            "--expected-log-sha256",
            "7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea",
            "--expected-run-report-sha256",
            "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09",
            "--expected-last-run-report-sha256",
            "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09",
            "--authorize-direct-mac-terminal-read-only-package-capture",
        ]
    )
    assert args.func is operator.capture_local_read_only_package
    assert args.authorize_direct_mac_terminal_read_only_package_capture is True
    assert not hasattr(args, "authorize_vps_package_write")

    try:
        parser.parse_args(
            [
                "capture-local-read-only-package",
                "--run-id",
                "post_d11_direct_mac_read_only_artifacts_001",
                "--expected-commit",
                "42a72f0814b49c31500031e83e1c737cdee8c8a3",
                "--artifact-runtime-commit",
                "ac75080419e910c39f1a2683641a603f8a8999a1",
                "--expected-log-sha256",
                "7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea",
                "--expected-run-report-sha256",
                "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09",
                "--expected-last-run-report-sha256",
                "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09",
                "--authorize-direct-mac-terminal-read-only-package-capture",
                "--authorize-vps-package-write",
            ]
        )
        raise AssertionError("--authorize-vps-package-write was accepted")
    except SystemExit as exc:
        assert exc.code != 0

    assert "capture-local-read-only-package" in operator_source
    assert "--authorize-direct-mac-terminal-read-only-package-capture" in (
        operator_source
    )
    assert "package_dir = repo / \"replay_packages\" / args.run_id" in (
        local_surface_source
    )
    assert "manifest_path = package_dir / \"manifest.json\"" in local_surface_source
    assert "package_execution_orchestrator.main" not in local_surface_source
    assert "--execution-mode" not in local_surface_source
    assert "authorize_vps_package_write" not in local_surface_source
    assert "order_state_path.read" not in local_surface_source
    assert "order_state_path.write" not in local_surface_source
    assert "order_state_json=ABSENT_EXCLUDED_NOT_BOUND" in local_surface_source

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Surface Remediation Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `42a72f0814b49c31500031e83e1c737cdee8c8a3`"
        in packet_text
    )
    assert "`PASS_head_matches_expected_42a72f0`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`134 tests passed`" in packet_text
    assert (
        "`remediation_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET_READY_FOR_COMMAND_RESOLUTION_RETRY`"
        in packet_text
    )
    assert (
        "`prior_concrete_blocker` | "
        "`NO_SUPPORTED_LOCAL_MAC_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE`"
        in packet_text
    )
    assert "`remediated_command_surface` | `capture-local-read-only-package`" in (
        packet_text
    )
    assert (
        "`local_authorization_flag` | "
        "`--authorize-direct-mac-terminal-read-only-package-capture`"
        in packet_text
    )
    assert "`vps_authorization_flag_accepted` | `false`" in packet_text
    assert "`execution_mode_vps_used` | `false`" in packet_text
    assert "`package_execution_orchestrator_main_delegation` | `false`" in (
        packet_text
    )
    assert "`supported_package_capture_command_resolved` | `true`" in packet_text

    for anchor in (
        "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`",
        "`artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`future_expected_package_output_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001`",
        "`replay_packages_current_state` | `ABSENT`",
        "`order_state_json_current_state` | `ABSENT`",
    ):
        assert anchor in packet_text

    for false_field in (
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_packages_created_by_this_gate` | `false`",
        "`artifact_git_add` | `PROHIBITED`",
        "`order_state_read_write_require_bind` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert "does not require" in packet_text
    assert "accept, or reinterpret `--authorize-vps-package-write`" in packet_text
    assert "`replay_packages` remains absent" in packet_text
    assert "`order_state.json` remains absent" in packet_text
    assert "previously produced artifacts were not modified and were not added to git" in (
        packet_text
    )
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Surface Remediation Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=42a72f0814b49c31500031e83e1c737cdee8c8a3`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_42a72f0`" in map_text
    assert "`134 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET_READY_FOR_COMMAND_RESOLUTION_RETRY`"
        in map_text
    )
    assert "`NO_SUPPORTED_LOCAL_MAC_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE`" in (
        map_text
    )
    assert "`capture-local-read-only-package`" in map_text
    assert "`--authorize-direct-mac-terminal-read-only-package-capture`" in map_text
    assert "`supported_package_capture_command_resolved=true`" in map_text
    assert "`replay_packages_created_by_this_gate=false`" in map_text
    assert "`artifact_git_add_performed_by_this_gate=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_command_resolution_retry_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_command_resolution_retry_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")
    operator_source = Path("tools/ops/gate_d_market_session_operator.py").read_text(
        encoding="utf-8"
    )
    local_surface_source = operator_source.split(
        "def _direct_mac_terminal_read_only_package_checks", 1
    )[1].split("\ndef produce_read_only_artifacts", 1)[0]

    command_shape = (
        ".venv-312/bin/python -m tools.ops.gate_d_market_session_operator "
        "capture-local-read-only-package --run-id "
        "post_d11_direct_mac_read_only_artifacts_001 --expected-commit "
        '"$EXPECTED_COMMIT" --artifact-runtime-commit '
        "ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 "
        "7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea "
        "--expected-run-report-sha256 "
        "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 "
        "--expected-last-run-report-sha256 "
        "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 "
        "--authorize-direct-mac-terminal-read-only-package-capture"
    )

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Resolution Retry Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `f2034397f862b5a44bad53d8dc36896e20d175d3`"
        in packet_text
    )
    assert (
        "`local_head` | `f2034397f862b5a44bad53d8dc36896e20d175d3`"
        in packet_text
    )
    assert (
        "`origin_main` | `f2034397f862b5a44bad53d8dc36896e20d175d3`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert "`worktree` | `clean`" in packet_text
    assert "`PASS_head_matches_expected_f203439`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`135 tests passed`" in packet_text
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_SURFACE_REMEDIATION_PACKET_READY_FOR_COMMAND_RESOLUTION_RETRY`"
        in packet_text
    )
    assert (
        "`command_resolution_retry_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION`"
        in packet_text
    )
    assert command_shape in packet_text
    assert "`resolved_command_surface` | `capture-local-read-only-package`" in (
        packet_text
    )
    assert (
        "`local_authorization_flag` | "
        "`--authorize-direct-mac-terminal-read-only-package-capture`"
        in packet_text
    )
    assert "`supported_package_capture_command_resolved` | `true`" in packet_text
    assert (
        "`package_capture_execution_authorized_by_this_packet` | `false`"
        in packet_text
    )

    resolved_command_value = packet_text.split(
        "`resolved_future_operator_command` | `", 1
    )[1].split("` |", 1)[0]
    assert "--execution-mode vps" not in resolved_command_value
    assert "--authorize-vps-package-write" not in resolved_command_value
    assert "package_execution_orchestrator" not in resolved_command_value
    assert "package_execution_orchestrator.main" not in local_surface_source
    assert "--execution-mode" not in local_surface_source
    assert "authorize_vps_package_write" not in local_surface_source

    for anchor in (
        "`prior_blocker_commit` | `42a72f0814b49c31500031e83e1c737cdee8c8a3`",
        "`authorization_packet_commit` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b`",
        "`artifact_adjudication_commit` | `7829aa5c5d4aee36f70218724b774238a56ac4ef`",
        "`artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`",
        "`log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`",
        "`log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json`",
        "`run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_path` | `last_run_report.json`",
        "`last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`expected_future_package_output_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001`",
        "`replay_packages_current_state` | `ABSENT`",
        "`order_state_json_current_state` | `ABSENT`",
    ):
        assert anchor in packet_text

    for false_field in (
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_package_created_by_this_gate` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_files_modified_by_this_gate` | `false`",
        "`artifact_git_add_performed_by_this_gate` | `false`",
        "`replay_executed_by_this_gate` | `false`",
        "`scoring_executed_by_this_gate` | `false`",
        "`candidate_generation_executed_by_this_gate` | `false`",
        "`unit_12_action_by_this_gate` | `false`",
        "`broker_tws_api_network_runtime_action_by_this_gate` | `false`",
        "`vps_action_by_this_gate` | `false`",
        "`broker_submit_readiness` | `NOT_APPROVED`",
        "`live_trading_readiness` | `NOT_APPROVED`",
        "`account_authority` | `NONE`",
        "`order_authority` | `NONE`",
        "`execution_authority` | `NONE`",
        "`order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert false_field in packet_text

    assert "`replay_packages` remains absent" in packet_text
    assert "`order_state.json` remains absent" in packet_text
    assert "does not execute it" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Command Resolution Retry Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=f2034397f862b5a44bad53d8dc36896e20d175d3`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_f203439`" in map_text
    assert "`135 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION`"
        in map_text
    )
    assert "`capture-local-read-only-package`" in map_text
    assert "`--authorize-direct-mac-terminal-read-only-package-capture`" in map_text
    assert "`supported_package_capture_command_resolved=true`" in map_text
    assert "`package_capture_execution_authorized_by_this_packet=false`" in (
        map_text
    )
    assert "`replay_package_created_by_this_gate=false`" in map_text
    assert "`artifact_git_add_performed_by_this_gate=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in map_text
    )


def test_post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_operator_run_authorization_packet() -> None:
    packet_path = Path(
        "docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_package_capture_operator_run_authorization_packet.md"
    )
    packet_text = packet_path.read_text(encoding="utf-8")
    map_text = Path(
        "docs/replay_evaluation_implementation_prerequisite_map.md"
    ).read_text(encoding="utf-8")

    command_shape = (
        ".venv-312/bin/python -m tools.ops.gate_d_market_session_operator "
        "capture-local-read-only-package --run-id "
        "post_d11_direct_mac_read_only_artifacts_001 --expected-commit "
        '"$EXPECTED_COMMIT" --artifact-runtime-commit '
        "ac75080419e910c39f1a2683641a603f8a8999a1 --expected-log-sha256 "
        "7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea "
        "--expected-run-report-sha256 "
        "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 "
        "--expected-last-run-report-sha256 "
        "fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09 "
        "--authorize-direct-mac-terminal-read-only-package-capture"
    )

    assert (
        "Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Operator Run Authorization Packet"
        in packet_text
    )
    assert (
        "`classification` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET`"
        in packet_text
    )
    assert (
        "`source_commit` | `db269ead5d981777f2e45397109e0c5a1259e6c4`"
        in packet_text
    )
    assert (
        "`local_head` | `db269ead5d981777f2e45397109e0c5a1259e6c4`"
        in packet_text
    )
    assert (
        "`origin_main` | `db269ead5d981777f2e45397109e0c5a1259e6c4`"
        in packet_text
    )
    assert "`branch` | `main`" in packet_text
    assert "`worktree` | `clean`" in packet_text
    assert "`PASS_head_matches_expected_db269ea`" in packet_text
    assert "`PASS_head_origin_main_aligned`" in packet_text
    assert "`136 tests passed`" in packet_text
    assert (
        "`prior_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMMAND_RESOLUTION_RETRY_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION`"
        in packet_text
    )
    assert (
        "`operator_run_authorization_decision` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN`"
        in packet_text
    )
    assert command_shape in packet_text
    assert (
        "`authorized_future_operator_command` | `" + command_shape + "`"
        in packet_text
    )
    assert "`authorized_attempt_count` | `1`" in packet_text
    assert "`source_context` | `LOCAL_MAC_ONLY`" in packet_text
    assert "`operator_surface` | `DIRECT_MAC_TERMINAL`" in packet_text
    assert (
        "`expected_commit_for_future_operator_run` | "
        "`db269ead5d981777f2e45397109e0c5a1259e6c4_UNLESS_SUPERSEDED_BY_LATER_PACKET`"
        in packet_text
    )

    for lineage in (
        "`artifact_adjudication_commit` | `7829aa5c5d4aee36f70218724b774238a56ac4ef`",
        "`package_capture_authorization_commit` | `a910514f693c2ffbcbe8b6ed499811c37904ec4b`",
        "`command_surface_blocker_commit` | `42a72f0814b49c31500031e83e1c737cdee8c8a3`",
        "`command_surface_remediation_commit` | `f2034397f862b5a44bad53d8dc36896e20d175d3`",
        "`command_resolution_retry_commit` | `db269ead5d981777f2e45397109e0c5a1259e6c4`",
    ):
        assert lineage in packet_text

    for anchor in (
        "`run_id` | `post_d11_direct_mac_read_only_artifacts_001`",
        "`artifact_runtime_commit_anchor` | `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`log_artifact_path` | `logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`",
        "`log_artifact_sha256` | `7e7ec6303d0defc2e2ff1234823eb6679e2ae44620d5e74f9935aa00c4f87eea`",
        "`run_report_artifact_path` | `run_reports/post_d11_direct_mac_read_only_artifacts_001.json`",
        "`run_report_artifact_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_path` | `last_run_report.json`",
        "`last_run_report_sha256` | `fe3066a526851a81d59802064c0a9cb76c641ad5595de7d27b4c1ce3adb80b09`",
        "`last_run_report_identity` | `BYTE_IDENTICAL_AND_HASH_IDENTICAL_TO_RUN_REPORT`",
        "`expected_future_package_output_path` | `replay_packages/post_d11_direct_mac_read_only_artifacts_001`",
        "`replay_packages_current_state` | `ABSENT`",
        "`order_state_json_current_state` | `ABSENT`",
    ):
        assert anchor in packet_text

    for boundary in (
        "HEAD, origin/main, and expected commit align",
        "Worktree is clean before execution",
        "artifact runtime commit anchor matches `ac75080419e910c39f1a2683641a603f8a8999a1`",
        "`replay_packages/post_d11_direct_mac_read_only_artifacts_001` is absent before execution",
        "`order_state.json` is absent and is not read, written, required, or bound",
        "does not use `--execution-mode vps`",
        "does not use `--authorize-vps-package-write`",
        "does not call `package_execution_orchestrator.main`",
        "does not touch broker/account/order/execution state",
        "does not modify source artifacts",
        "does not add `logs`, `run_reports`, `last_run_report.json`, `replay_packages`, or `order_state.json` to git",
    ):
        assert boundary in packet_text

    for field in (
        "`package_capture_operator_run_authorized` | `ONE_FUTURE_BOUNDED_LOCAL_MAC_ATTEMPT_ONLY`",
        "`package_capture_executed_by_this_gate` | `false`",
        "`replay_package_created_by_this_gate` | `false`",
        "`produce_read_only_artifacts_rerun_by_this_gate` | `false`",
        "`artifact_files_modified_by_this_gate` | `false`",
        "`artifact_git_add_performed_by_this_gate` | `false`",
        "`replay_authorized` | `false`",
        "`scoring_authorized` | `false`",
        "`candidate_generation_authorized` | `false`",
        "`unit_12_authorized` | `false`",
        "`broker_tws_api_network_runtime_action_authorized` | `false`",
        "`vps_runtime_action_authorized` | `false`",
        "`broker_submit_readiness` | `NOT_APPROVED`",
        "`live_trading_readiness` | `NOT_APPROVED`",
        "`account_authority` | `NONE`",
        "`order_authority` | `NONE`",
        "`execution_authority` | `NONE`",
        "`order_state_json` | `ABSENT_EXCLUDED_NOT_BOUND`",
        "`commit_performed_by_this_gate` | `false`",
        "`push_performed_by_this_gate` | `false`",
    ):
        assert field in packet_text

    assert "No package capture was executed by this packet" in packet_text
    assert "No replay package was created by\nthis packet" in packet_text
    assert "`replay_packages` remains absent" in packet_text
    assert "`order_state.json` remains\nabsent" in packet_text
    assert (
        "`next_permissible_gate` | "
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET`"
        in packet_text
    )

    assert (
        "### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Package Capture Operator Run Authorization Packet"
        in map_text
    )
    assert str(packet_path) in map_text
    assert "`source_commit=db269ead5d981777f2e45397109e0c5a1259e6c4`" in (
        map_text
    )
    assert "`PASS_head_matches_expected_db269ea`" in map_text
    assert "`136 tests passed`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_AUTHORIZATION_PACKET_READY_FOR_PACKAGE_CAPTURE_OPERATOR_RUN`"
        in map_text
    )
    assert "`package_capture_operator_run_authorized=ONE_FUTURE_BOUNDED_LOCAL_MAC_ATTEMPT_ONLY`" in (
        map_text
    )
    assert "`package_capture_executed_by_this_gate=false`" in map_text
    assert "`replay_package_created_by_this_gate=false`" in map_text
    assert "`artifact_git_add_performed_by_this_gate=false`" in map_text
    assert (
        "`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_OPERATOR_RUN_PACKET`"
        in map_text
    )


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
