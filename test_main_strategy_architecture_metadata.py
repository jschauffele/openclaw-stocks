from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import main
import reporting
from broker_interface import BrokerAccountState, BrokerOrderResult
from runtime_strategy_metadata_adapter import StrategyArchitectureMetadata
from runtime_strategy_seam import RuntimeStrategySeamResult


class FakeBroker:
    def __init__(self) -> None:
        self.client = object()
        self.submit_calls = 0

    def get_account_buying_power(self) -> BrokerAccountState:
        return BrokerAccountState(broker_name="test", buying_power=100000.0)

    def build_market_order(self, symbol: str, qty: int):
        return SimpleNamespace(symbol=symbol, qty=qty)

    def submit_market_order(self, order) -> BrokerOrderResult:
        self.submit_calls += 1
        return BrokerOrderResult(
            broker_name="test",
            order_id="101",
            order_status="accepted",
            broker_status="accepted",
            is_terminal=False,
        )


def _bars_result():
    timestamp = datetime(2026, 5, 12, tzinfo=timezone.utc)
    closes = (100.0, 100.2, 100.4, 100.8, 101.2)
    return SimpleNamespace(
        candles=[
            SimpleNamespace(
                timestamp=timestamp,
                open=close - 0.1,
                high=close + 0.2,
                low=close - 0.2,
                close=close,
                volume=1000,
            )
            for close in closes
        ],
        symbol="AAPL",
        timeframe="5Min",
        source="alpaca",
        adjustment_type="raw",
        is_adjusted=False,
        warnings=[],
    )


def _action_proposal() -> dict:
    return {
        "should_submit": True,
        "action": "buy",
        "signal": "buy",
        "decision": "buy",
        "reason": "test_submit",
        "previous_close": 100.8,
        "latest_close": 101.2,
        "price_delta": 0.4,
        "percent_change": 0.4,
        "three_close_percent_change": 1.2,
    }


def _runtime_visibility_summary() -> dict:
    return {
        "runtime_visibility_reports": [],
        "runtime_visibility_blocking": False,
        "runtime_visibility_reason": "runtime_visibility_clear",
    }


def _contains_strategy_architecture(value) -> bool:
    if isinstance(value, dict):
        if "strategy_architecture" in value:
            return True
        return any(_contains_strategy_architecture(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_strategy_architecture(item) for item in value)
    return False


def _contains_metadata_schema_version(value) -> bool:
    if isinstance(value, dict):
        if "metadata_schema_version" in value:
            return True
        return any(_contains_metadata_schema_version(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_metadata_schema_version(item) for item in value)
    return False


@pytest.fixture
def main_harness(monkeypatch):
    broker = FakeBroker()
    reports = []
    events = []
    observations = []
    market_data_calls = []
    risk_check_calls = []
    action_proposal_calls = []
    call_order = []

    def persist_report(**kwargs):
        call_order.append("persist_report")
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

    def get_historical_bars_call(*args, **kwargs):
        market_data_calls.append((args, kwargs))
        return _bars_result()

    def build_action_proposal_call(*args, **kwargs):
        action_proposal_calls.append((args, kwargs))
        return _action_proposal()

    def risk_check_call(*args, **kwargs):
        risk_check_calls.append((args, kwargs))
        return {"passed": True, "estimated_cost": 100.0}

    monkeypatch.setattr("config.load_config", lambda: None)
    monkeypatch.setattr("config.BASE_DIR", "/tmp/openclaw-test", raising=False)
    monkeypatch.setattr("config.LOG_FILE", "/tmp/openclaw-test.log", raising=False)
    monkeypatch.setattr("config.STATE_FILE", "/tmp/openclaw-state.json", raising=False)
    monkeypatch.setattr(
        "config.RUN_REPORT_FILE", "/tmp/openclaw-report.json", raising=False
    )
    monkeypatch.setattr(
        "config.LEGACY_LAST_ORDER_FILE",
        "/tmp/openclaw-last-order.txt",
        raising=False,
    )
    monkeypatch.setattr("config.OPENCLAW_ENABLED", True, raising=False)
    monkeypatch.setattr("config.OPENCLAW_DRY_RUN", False, raising=False)
    monkeypatch.setattr("config.OPENCLAW_SYMBOL", "AAPL", raising=False)
    monkeypatch.setattr("config.OPENCLAW_QTY", 1, raising=False)
    monkeypatch.setattr("config.OPENCLAW_MAX_POSITION_SIZE", 5, raising=False)
    monkeypatch.setattr(
        "config.OPENCLAW_DUPLICATE_COOLDOWN_SECONDS", 600, raising=False
    )
    monkeypatch.setattr("config.OPENCLAW_BROKER", "alpaca", raising=False)
    monkeypatch.setattr("config.ALPACA_API_KEY", "key", raising=False)
    monkeypatch.setattr("config.ALPACA_SECRET_KEY", "secret", raising=False)
    monkeypatch.setattr(
        "config.ALPACA_BASE_URL", "https://paper-api.alpaca.markets", raising=False
    )
    monkeypatch.setattr("config.ALLOWED_SYMBOLS", ["AAPL"], raising=False)
    monkeypatch.setattr("config.env_str", lambda _name, default: default)
    monkeypatch.setattr("config.env_int", lambda _name, default: default)
    monkeypatch.setattr("main.setup_logging", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("main.create_broker_adapter", lambda *_args, **_kwargs: broker)
    monkeypatch.setattr("main.generate_run_id", lambda: "run-test")
    monkeypatch.setattr("main.initialize_event_logger", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("main.log_event", log_event)
    monkeypatch.setattr("main.validate_config", lambda **_kwargs: True)
    monkeypatch.setattr(
        "main.get_market_session_status",
        lambda _client: {"is_open": True, "reason": "market_open"},
    )
    monkeypatch.setattr("main.AlpacaMarketDataProvider", lambda: object())
    monkeypatch.setattr("main.get_historical_bars", get_historical_bars_call)
    monkeypatch.setattr("main.generate_signal_from_closes", lambda _closes: object())
    monkeypatch.setattr("main.validate_signal_result", lambda _result: object())
    monkeypatch.setattr("main.build_action_proposal", build_action_proposal_call)
    monkeypatch.setattr("main.risk_check", risk_check_call)
    monkeypatch.setattr(
        "main.reconcile_position",
        lambda *_args, **_kwargs: {
            "passed": True,
            "reason": "broker_reconciliation_passed",
            "message": "broker_reconciliation_passed",
            "existing_qty": 0,
            "open_buy_order_qty": 0,
            "projected_qty": 1,
        },
    )
    monkeypatch.setattr(
        "main.build_runtime_visibility_providers",
        lambda _config_module: [],
    )
    monkeypatch.setattr(
        "main.build_runtime_visibility_summary",
        lambda _providers: _runtime_visibility_summary(),
    )
    monkeypatch.setattr(
        "state_manager.duplicate_check",
        lambda *_args, **_kwargs: {
            "is_duplicate": False,
            "reason": "no_matching_state",
            "age_seconds": None,
        },
    )
    monkeypatch.setattr(
        "state_manager.write_order_state", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr("reporting.persist_report", persist_report)
    monkeypatch.setattr(
        "main.append_observation",
        lambda **kwargs: observations.append(kwargs),
    )

    return {
        "broker": broker,
        "reports": reports,
        "events": events,
        "observations": observations,
        "market_data_calls": market_data_calls,
        "risk_check_calls": risk_check_calls,
        "action_proposal_calls": action_proposal_calls,
        "call_order": call_order,
    }


def test_main_success_path_assembles_strategy_architecture_before_persist_report(
    monkeypatch, main_harness
) -> None:
    seam_result = RuntimeStrategySeamResult(
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )
    metadata = StrategyArchitectureMetadata(
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )

    def build_runtime(input_model):
        main_harness["call_order"].append("build_runtime_strategy_metadata")
        assert input_model.closes == (100.0, 100.2, 100.4, 100.8, 101.2)
        return seam_result

    def build_metadata(result):
        main_harness["call_order"].append("build_strategy_architecture_metadata")
        assert result is seam_result
        return metadata

    def build_payload(result_metadata):
        main_harness["call_order"].append(
            "build_orchestration_strategy_architecture_payload"
        )
        assert result_metadata is metadata
        assert result_metadata.metadata_schema_version == "1"
        return {
            "strategy_architecture": {
                "metadata_schema_version": "1",
                "regime_id": "uptrend",
                "selected_strategy_id": "close_momentum_v1",
                "routing_reason": "selected_first_eligible_strategy",
                "eligible_strategy_ids": ("close_momentum_v1",),
                "rejected_strategy_ids": (),
                "source": "runtime_strategy_seam",
            }
        }

    monkeypatch.setattr("main.build_runtime_strategy_metadata", build_runtime)
    monkeypatch.setattr("main.build_strategy_architecture_metadata", build_metadata)
    monkeypatch.setattr(
        "main.build_orchestration_strategy_architecture_payload", build_payload
    )

    main.main()

    report = main_harness["reports"][0]
    assert report["orchestration"]["strategy_architecture"] == {
        "metadata_schema_version": "1",
        "regime_id": "uptrend",
        "selected_strategy_id": "close_momentum_v1",
        "routing_reason": "selected_first_eligible_strategy",
        "eligible_strategy_ids": ("close_momentum_v1",),
        "rejected_strategy_ids": (),
        "source": "runtime_strategy_seam",
    }
    assert main_harness["call_order"] == [
        "build_runtime_strategy_metadata",
        "build_strategy_architecture_metadata",
        "build_orchestration_strategy_architecture_payload",
        "persist_report",
    ]


def test_metadata_assembly_failure_omits_strategy_architecture_and_still_persists_report(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: (_ for _ in ()).throw(ValueError("metadata failed")),
    )

    main.main()

    assert len(main_harness["reports"]) == 1
    report = main_harness["reports"][0]
    assert "strategy_architecture" not in report["orchestration"]
    assert report["result"] == "success"
    assert report["reason"] == "paper_order_submitted"


def test_metadata_assembly_failure_does_not_change_runtime_decision_fields(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: (_ for _ in ()).throw(ValueError("metadata failed")),
    )

    main.main()

    assert main_harness["action_proposal_calls"]
    assert len(main_harness["risk_check_calls"]) == 1
    assert main_harness["broker"].submit_calls == 1
    report = main_harness["reports"][0]
    assert report["result"] == "success"
    assert report["reason"] == "paper_order_submitted"
    assert report["side"] == "buy"


def test_metadata_assembly_does_not_alter_append_observation_behavior(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: RuntimeStrategySeamResult(
            regime_id="uptrend",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        ),
    )

    main.main()

    assert len(main_harness["observations"]) == 1
    assert "strategy_architecture" not in main_harness["observations"][0]
    assert "metadata_schema_version" not in main_harness["observations"][0]


def test_metadata_success_does_not_emit_strategy_architecture_to_jsonl_events(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: RuntimeStrategySeamResult(
            regime_id="uptrend",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        ),
    )

    main.main()

    assert main_harness["events"]
    assert not any(
        _contains_strategy_architecture(event["payload"])
        for event in main_harness["events"]
    )
    assert not any(
        _contains_metadata_schema_version(event["payload"])
        for event in main_harness["events"]
    )


def test_reporting_remains_passthrough_only_and_does_not_import_metadata_builders() -> None:
    orchestration = {
        "runtime_visibility": _runtime_visibility_summary(),
        "strategy_architecture": {
            "metadata_schema_version": "1",
            "regime_id": "uptrend",
            "selected_strategy_id": "close_momentum_v1",
            "routing_reason": "selected_first_eligible_strategy",
            "eligible_strategy_ids": ("close_momentum_v1",),
            "rejected_strategy_ids": (),
            "source": "runtime_strategy_seam",
        },
    }

    report = reporting.build_run_report(
        run_id="run-test",
        mode="paper_submit",
        result="success",
        reason="paper_order_submitted",
        trigger_source="test",
        side="buy",
        symbol="AAPL",
        qty=1,
        openclaw_enabled=True,
        duplicate_cooldown_seconds=600,
        max_position_size=5,
        allowed_symbols=["AAPL"],
        alpaca_base_url="https://paper-api.alpaca.markets",
        orchestration=orchestration,
    )

    assert report["orchestration"] is orchestration
    assert not hasattr(reporting, "build_runtime_strategy_metadata")
    assert not hasattr(reporting, "build_strategy_architecture_metadata")
    assert not hasattr(reporting, "build_orchestration_strategy_architecture_payload")


def test_metadata_chain_is_called_outside_reporting_in_required_order(
    monkeypatch, main_harness
) -> None:
    call_order = []

    def build_runtime(_input_model):
        call_order.append("build_runtime_strategy_metadata")
        return RuntimeStrategySeamResult(
            regime_id="uptrend",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        )

    def build_metadata(seam_result):
        call_order.append("build_strategy_architecture_metadata")
        return StrategyArchitectureMetadata(
            regime_id=seam_result.regime_id,
            selected_strategy_id=seam_result.selected_strategy_id,
            routing_reason=seam_result.routing_reason,
            eligible_strategy_ids=seam_result.eligible_strategy_ids,
            rejected_strategy_ids=seam_result.rejected_strategy_ids,
        )

    def build_payload(_metadata):
        call_order.append("build_orchestration_strategy_architecture_payload")
        return {"strategy_architecture": {"source": "runtime_strategy_seam"}}

    monkeypatch.setattr("main.build_runtime_strategy_metadata", build_runtime)
    monkeypatch.setattr("main.build_strategy_architecture_metadata", build_metadata)
    monkeypatch.setattr(
        "main.build_orchestration_strategy_architecture_payload", build_payload
    )

    main.main()

    assert call_order == [
        "build_runtime_strategy_metadata",
        "build_strategy_architecture_metadata",
        "build_orchestration_strategy_architecture_payload",
    ]
    assert not hasattr(reporting, "build_runtime_strategy_metadata")
    assert not hasattr(reporting, "build_strategy_architecture_metadata")
    assert not hasattr(reporting, "build_orchestration_strategy_architecture_payload")


def test_metadata_assembly_uses_already_fetched_closes_without_fetching_market_data_again(
    monkeypatch, main_harness
) -> None:
    captured_closes = []

    def build_runtime(input_model):
        captured_closes.append(input_model.closes)
        return RuntimeStrategySeamResult(
            regime_id="uptrend",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        )

    monkeypatch.setattr("main.build_runtime_strategy_metadata", build_runtime)

    main.main()

    assert captured_closes == [(100.0, 100.2, 100.4, 100.8, 101.2)]
    assert len(main_harness["market_data_calls"]) == 1
