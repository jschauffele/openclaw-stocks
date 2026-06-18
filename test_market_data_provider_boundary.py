from __future__ import annotations

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
