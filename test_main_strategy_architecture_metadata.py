from __future__ import annotations

import sys
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import main
import reporting
from broker_interface import BrokerAccountState, BrokerOrderResult
from decision_engine import build_action_proposal
from regime_classifier import RegimeClassificationInput, classify_regime
from runtime_strategy_metadata_adapter import StrategyArchitectureMetadata
from runtime_strategy_seam import RuntimeStrategySeamResult
from strategy_evaluator import StrategyEvaluationInput, evaluate_selected_strategy_signal
from strategy_library import get_strategy_definition
from strategy_router import StrategyRoutingInput, route_strategy


FORBIDDEN_MODULES_TO_UNLOAD_AFTER_MAIN_TESTS = (
    "main",
    "config",
    "broker_factory",
    "risk_engine",
    "execution_engine",
    "execution_use_case",
    "reporting",
    "observation_logger",
    "state_manager",
    "market_data",
    "strategy_engine",
    "signal_validator",
)


def teardown_module(_module) -> None:
    for module_name in FORBIDDEN_MODULES_TO_UNLOAD_AFTER_MAIN_TESTS:
        sys.modules.pop(module_name, None)
    for module_name in tuple(sys.modules):
        if module_name.startswith("ibkr_"):
            sys.modules.pop(module_name, None)


class FakeBroker:
    def __init__(self) -> None:
        self.client = object()
        self.buying_power_calls = 0
        self.build_order_calls = 0
        self.submit_calls = 0

    def get_account_buying_power(self) -> BrokerAccountState:
        self.buying_power_calls += 1
        return BrokerAccountState(broker_name="test", buying_power=100000.0)

    def build_market_order(self, symbol: str, qty: int):
        self.build_order_calls += 1
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


def _hold_action_proposal() -> dict:
    action_proposal = _action_proposal()
    action_proposal.update(
        {
            "should_submit": False,
            "action": "hold",
            "decision": "hold",
            "reason": "test_hold",
        }
    )
    return action_proposal


def _sell_action_proposal() -> dict:
    action_proposal = _action_proposal()
    action_proposal.update(
        {
            "should_submit": False,
            "action": "sell",
            "signal": "sell",
            "decision": "sell",
            "reason": "test_sell",
        }
    )
    return action_proposal


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


def _strategy_events(events: list[dict], stage: str) -> list[dict]:
    return [
        event
        for event in events
        if event["event_type"] == "strategy" and event["stage"] == stage
    ]


def _assert_flat_routing_fields(
    payload: dict,
    *,
    regime_id: str,
    selected_strategy_id: str | None,
    routing_reason: str,
    eligible_strategy_ids: tuple[str, ...],
    rejected_strategy_ids: tuple[str, ...],
) -> None:
    assert payload["regime_id"] == regime_id
    assert payload["selected_strategy_id"] == selected_strategy_id
    assert payload["routing_reason"] == routing_reason
    assert payload["eligible_strategy_ids"] == eligible_strategy_ids
    assert payload["rejected_strategy_ids"] == rejected_strategy_ids
    assert "strategy_architecture" not in payload


def _assert_no_flat_routing_fields(payload: dict) -> None:
    for field_name in (
        "regime_id",
        "selected_strategy_id",
        "routing_reason",
        "eligible_strategy_ids",
        "rejected_strategy_ids",
    ):
        assert field_name not in payload


@pytest.fixture
def main_harness(monkeypatch):
    broker = FakeBroker()
    reports = []
    events = []
    observations = []
    market_data_calls = []
    duplicate_check_calls = []
    risk_check_calls = []
    reconcile_position_calls = []
    signal_generation_calls = []
    strategy_evaluator_calls = []
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

    def generate_signal_from_closes_call(*args, **kwargs):
        signal_generation_calls.append((args, kwargs))
        return object()

    def evaluate_selected_strategy_signal_call(input_model):
        call_order.append("evaluate_selected_strategy_signal")
        strategy_evaluator_calls.append(input_model)
        return SimpleNamespace(signal_result=object())

    def risk_check_call(*args, **kwargs):
        risk_check_calls.append((args, kwargs))
        return {"passed": True, "estimated_cost": 100.0}

    def duplicate_check_call(*args, **kwargs):
        duplicate_check_calls.append((args, kwargs))
        return {
            "is_duplicate": False,
            "reason": "no_matching_state",
            "age_seconds": None,
        }

    def reconcile_position_call(*args, **kwargs):
        reconcile_position_calls.append((args, kwargs))
        return {
            "passed": True,
            "reason": "broker_reconciliation_passed",
            "message": "broker_reconciliation_passed",
            "existing_qty": 0,
            "open_buy_order_qty": 0,
            "projected_qty": 1,
        }

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
    monkeypatch.setattr(
        "main.generate_signal_from_closes",
        generate_signal_from_closes_call,
    )
    monkeypatch.setattr(
        "main.evaluate_selected_strategy_signal",
        evaluate_selected_strategy_signal_call,
    )
    monkeypatch.setattr("main.validate_signal_result", lambda _result: object())
    monkeypatch.setattr("main.build_action_proposal", build_action_proposal_call)
    monkeypatch.setattr("main.risk_check", risk_check_call)
    monkeypatch.setattr(
        "main.reconcile_position",
        reconcile_position_call,
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
        duplicate_check_call,
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
        "duplicate_check_calls": duplicate_check_calls,
        "risk_check_calls": risk_check_calls,
        "reconcile_position_calls": reconcile_position_calls,
        "signal_generation_calls": signal_generation_calls,
        "strategy_evaluator_calls": strategy_evaluator_calls,
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
        "evaluate_selected_strategy_signal",
        "persist_report",
    ]
    assert main_harness["strategy_evaluator_calls"][0].closes == (
        100.0,
        100.2,
        100.4,
        100.8,
        101.2,
    )
    assert (
        main_harness["strategy_evaluator_calls"][0].selected_strategy_id
        == "close_momentum_v1"
    )
    assert main_harness["signal_generation_calls"] == []
    assert len(main_harness["duplicate_check_calls"]) == 1
    assert len(main_harness["risk_check_calls"]) == 1
    assert len(main_harness["reconcile_position_calls"]) == 1
    assert main_harness["broker"].buying_power_calls == 1
    assert main_harness["broker"].build_order_calls == 1
    assert main_harness["broker"].submit_calls == 1
    strategy_evaluated_events = _strategy_events(
        main_harness["events"],
        "strategy_evaluated",
    )
    assert len(strategy_evaluated_events) == 1
    assert strategy_evaluated_events[0]["payload"]["action"] == "buy"
    assert strategy_evaluated_events[0]["payload"]["decision"] == "buy"
    assert strategy_evaluated_events[0]["payload"]["reason"] == "test_submit"
    _assert_flat_routing_fields(
        strategy_evaluated_events[0]["payload"],
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )
    assert len(main_harness["observations"]) == 1
    observation = main_harness["observations"][0]
    assert observation["action_proposal"]["action"] == "buy"
    assert observation["action_proposal"]["decision"] == "buy"
    _assert_flat_routing_fields(
        observation,
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )


def test_sideways_buy_signal_is_blocked_by_strategy_routing_without_submission(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no_eligible_strategy_for_regime",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        ),
    )

    main.main()

    assert len(main_harness["risk_check_calls"]) == 0
    assert len(main_harness["duplicate_check_calls"]) == 0
    assert len(main_harness["reconcile_position_calls"]) == 0
    assert main_harness["broker"].buying_power_calls == 0
    assert main_harness["broker"].build_order_calls == 0
    assert main_harness["broker"].submit_calls == 0
    report = main_harness["reports"][0]
    assert report["result"] == "blocked"
    assert report["reason"] == "strategy_routing_no_selected_strategy"
    assert report["orchestration"]["strategy_architecture"] == {
        "metadata_schema_version": "1",
        "regime_id": "sideways",
        "selected_strategy_id": None,
        "routing_reason": "no_eligible_strategy_for_regime",
        "eligible_strategy_ids": (),
        "rejected_strategy_ids": ("close_momentum_v1",),
        "source": "runtime_strategy_seam",
    }
    assert "Strategy action=hold" in report["notes"]
    assert (
        "Strategy reason=strategy_routing_no_selected_strategy"
        in report["notes"]
    )
    strategy_evaluated_events = _strategy_events(
        main_harness["events"],
        "strategy_evaluated",
    )
    assert len(strategy_evaluated_events) == 1
    assert strategy_evaluated_events[0]["payload"]["action"] == "hold"
    assert strategy_evaluated_events[0]["payload"]["decision"] == "hold"
    assert (
        strategy_evaluated_events[0]["payload"]["reason"]
        == "strategy_routing_no_selected_strategy"
    )
    _assert_flat_routing_fields(
        strategy_evaluated_events[0]["payload"],
        regime_id="sideways",
        selected_strategy_id=None,
        routing_reason="no_eligible_strategy_for_regime",
        eligible_strategy_ids=(),
        rejected_strategy_ids=("close_momentum_v1",),
    )
    assert not any(
        event["payload"]["action"] == "buy"
        and event["payload"]["decision"] == "buy"
        for event in strategy_evaluated_events
    )
    assert len(main_harness["observations"]) == 1
    observation = main_harness["observations"][0]
    assert observation["action_proposal"]["action"] == "hold"
    assert observation["action_proposal"]["decision"] == "hold"
    assert (
        observation["action_proposal"]["reason"]
        == "strategy_routing_no_selected_strategy"
    )
    _assert_flat_routing_fields(
        observation,
        regime_id="sideways",
        selected_strategy_id=None,
        routing_reason="no_eligible_strategy_for_regime",
        eligible_strategy_ids=(),
        rejected_strategy_ids=("close_momentum_v1",),
    )


def test_sideways_buy_signal_emits_deterministic_routing_block_reason(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no_eligible_strategy_for_regime",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        ),
    )

    main.main()

    action_events = _strategy_events(main_harness["events"], "action_proposal")
    assert len(action_events) == 1
    assert action_events[0]["status"] == "blocked"
    assert action_events[0]["payload"]["action"] == "hold"
    assert action_events[0]["payload"]["decision"] == "hold"
    assert (
        action_events[0]["payload"]["reason"]
        == "strategy_routing_no_selected_strategy"
    )
    _assert_flat_routing_fields(
        action_events[0]["payload"],
        regime_id="sideways",
        selected_strategy_id=None,
        routing_reason="no_eligible_strategy_for_regime",
        eligible_strategy_ids=(),
        rejected_strategy_ids=("close_momentum_v1",),
    )


def test_no_selected_strategy_sell_signal_normalizes_to_hold_without_submission(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_action_proposal",
        lambda *args, **kwargs: _sell_action_proposal(),
    )
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no_eligible_strategy_for_regime",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        ),
    )

    main.main()

    assert len(main_harness["duplicate_check_calls"]) == 0
    assert len(main_harness["risk_check_calls"]) == 0
    assert len(main_harness["reconcile_position_calls"]) == 0
    assert main_harness["broker"].buying_power_calls == 0
    assert main_harness["broker"].build_order_calls == 0
    assert main_harness["broker"].submit_calls == 0
    report = main_harness["reports"][0]
    assert report["result"] == "blocked"
    assert report["reason"] == "strategy_routing_no_selected_strategy"
    assert report["side"] == "sell"
    assert report["orchestration"]["strategy_architecture"] == {
        "metadata_schema_version": "1",
        "regime_id": "sideways",
        "selected_strategy_id": None,
        "routing_reason": "no_eligible_strategy_for_regime",
        "eligible_strategy_ids": (),
        "rejected_strategy_ids": ("close_momentum_v1",),
        "source": "runtime_strategy_seam",
    }
    assert "Strategy action=hold" in report["notes"]
    assert (
        "Strategy reason=strategy_routing_no_selected_strategy"
        in report["notes"]
    )

    strategy_evaluated_events = _strategy_events(
        main_harness["events"],
        "strategy_evaluated",
    )
    assert len(strategy_evaluated_events) == 1
    assert strategy_evaluated_events[0]["payload"]["signal"] == "sell"
    assert strategy_evaluated_events[0]["payload"]["action"] == "hold"
    assert strategy_evaluated_events[0]["payload"]["decision"] == "hold"
    assert (
        strategy_evaluated_events[0]["payload"]["reason"]
        == "strategy_routing_no_selected_strategy"
    )
    assert not any(
        event["payload"]["action"] == "sell"
        and event["payload"]["decision"] == "sell"
        for event in strategy_evaluated_events
    )
    assert len(main_harness["observations"]) == 1
    observation = main_harness["observations"][0]
    assert observation["action_proposal"]["signal"] == "sell"
    assert observation["action_proposal"]["action"] == "hold"
    assert observation["action_proposal"]["decision"] == "hold"
    assert (
        observation["action_proposal"]["reason"]
        == "strategy_routing_no_selected_strategy"
    )
    _assert_flat_routing_fields(
        observation,
        regime_id="sideways",
        selected_strategy_id=None,
        routing_reason="no_eligible_strategy_for_regime",
        eligible_strategy_ids=(),
        rejected_strategy_ids=("close_momentum_v1",),
    )


def test_existing_non_submit_proposal_remains_non_submit_after_strategy_routing(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_action_proposal",
        lambda *args, **kwargs: _hold_action_proposal(),
    )
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no_eligible_strategy_for_regime",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        ),
    )

    main.main()

    assert len(main_harness["risk_check_calls"]) == 0
    assert len(main_harness["duplicate_check_calls"]) == 0
    assert len(main_harness["reconcile_position_calls"]) == 0
    assert main_harness["broker"].buying_power_calls == 0
    assert main_harness["broker"].build_order_calls == 0
    assert main_harness["broker"].submit_calls == 0
    report = main_harness["reports"][0]
    assert report["result"] == "blocked"
    assert report["reason"] == "strategy_hold"
    assert "Strategy action=hold" in report["notes"]
    assert "Strategy reason=test_hold" in report["notes"]


def test_selected_close_momentum_hold_remains_non_submit(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_action_proposal",
        lambda *args, **kwargs: _hold_action_proposal(),
    )
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

    assert len(main_harness["duplicate_check_calls"]) == 0
    assert len(main_harness["risk_check_calls"]) == 0
    assert len(main_harness["reconcile_position_calls"]) == 0
    assert main_harness["broker"].buying_power_calls == 0
    assert main_harness["broker"].build_order_calls == 0
    assert main_harness["broker"].submit_calls == 0
    report = main_harness["reports"][0]
    assert report["result"] == "blocked"
    assert report["reason"] == "strategy_hold"
    assert "Strategy action=hold" in report["notes"]
    assert "Strategy reason=test_hold" in report["notes"]
    assert report["orchestration"]["strategy_architecture"] == {
        "metadata_schema_version": "1",
        "regime_id": "uptrend",
        "selected_strategy_id": "close_momentum_v1",
        "routing_reason": "selected_first_eligible_strategy",
        "eligible_strategy_ids": ("close_momentum_v1",),
        "rejected_strategy_ids": (),
        "source": "runtime_strategy_seam",
    }


def test_selected_close_momentum_sell_normalizes_to_hold_without_submission(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_action_proposal",
        lambda *args, **kwargs: _sell_action_proposal(),
    )
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

    assert len(main_harness["duplicate_check_calls"]) == 0
    assert len(main_harness["risk_check_calls"]) == 0
    assert len(main_harness["reconcile_position_calls"]) == 0
    assert main_harness["broker"].buying_power_calls == 0
    assert main_harness["broker"].build_order_calls == 0
    assert main_harness["broker"].submit_calls == 0
    report = main_harness["reports"][0]
    assert report["result"] == "blocked"
    assert report["reason"] == "strategy_routing_action_not_allowed"
    assert report["orchestration"]["strategy_architecture"] == {
        "metadata_schema_version": "1",
        "regime_id": "uptrend",
        "selected_strategy_id": "close_momentum_v1",
        "routing_reason": "selected_first_eligible_strategy",
        "eligible_strategy_ids": ("close_momentum_v1",),
        "rejected_strategy_ids": (),
        "source": "runtime_strategy_seam",
    }
    assert "Strategy action=hold" in report["notes"]
    assert "Strategy reason=strategy_routing_action_not_allowed" in report["notes"]

    strategy_evaluated_events = _strategy_events(
        main_harness["events"],
        "strategy_evaluated",
    )
    assert len(strategy_evaluated_events) == 1
    assert strategy_evaluated_events[0]["payload"]["signal"] == "sell"
    assert strategy_evaluated_events[0]["payload"]["action"] == "hold"
    assert strategy_evaluated_events[0]["payload"]["decision"] == "hold"
    assert (
        strategy_evaluated_events[0]["payload"]["reason"]
        == "strategy_routing_action_not_allowed"
    )
    _assert_flat_routing_fields(
        strategy_evaluated_events[0]["payload"],
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )
    assert not any(
        event["payload"]["action"] == "sell"
        and event["payload"]["decision"] == "sell"
        for event in strategy_evaluated_events
    )
    assert len(main_harness["observations"]) == 1
    observation = main_harness["observations"][0]
    assert observation["action_proposal"]["signal"] == "sell"
    assert observation["action_proposal"]["action"] == "hold"
    assert observation["action_proposal"]["decision"] == "hold"
    assert (
        observation["action_proposal"]["reason"]
        == "strategy_routing_action_not_allowed"
    )
    _assert_flat_routing_fields(
        observation,
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )


def test_report_only_candidate_buy_proposal_is_forced_to_hold_no_submit() -> None:
    action_proposal = _action_proposal()
    result = main.apply_strategy_routing_submit_gate(
        action_proposal,
        RuntimeStrategySeamResult(
            regime_id="uptrend",
            selected_strategy_id="equity_momentum_continuation_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("equity_momentum_continuation_v1",),
            rejected_strategy_ids=("close_momentum_v1",),
        ),
    )

    assert result["should_submit"] is False
    assert result["action"] == "hold"
    assert result["decision"] == "hold"
    assert result["reason"] == "strategy_report_only_candidate_no_submit"
    assert action_proposal["should_submit"] is True
    assert action_proposal["action"] == "buy"


def test_close_momentum_buy_proposal_is_not_changed_by_report_only_gate() -> None:
    action_proposal = _action_proposal()

    result = main.apply_strategy_routing_submit_gate(
        action_proposal,
        RuntimeStrategySeamResult(
            regime_id="uptrend",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        ),
    )

    assert result is action_proposal
    assert result["should_submit"] is True
    assert result["action"] == "buy"
    assert result["decision"] == "buy"
    assert result["reason"] == "test_submit"


def test_no_selected_strategy_behavior_remains_no_submit_hold() -> None:
    result = main.apply_strategy_routing_submit_gate(
        _action_proposal(),
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no_eligible_strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(
                "close_momentum_v1",
                "equity_momentum_continuation_v1",
            ),
        ),
    )

    assert result["should_submit"] is False
    assert result["action"] == "hold"
    assert result["decision"] == "hold"
    assert result["reason"] == "strategy_routing_no_selected_strategy"


def test_action_not_allowed_behavior_remains_no_submit_hold() -> None:
    result = main.apply_strategy_routing_submit_gate(
        _sell_action_proposal(),
        RuntimeStrategySeamResult(
            regime_id="uptrend",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        ),
    )

    assert result["should_submit"] is False
    assert result["action"] == "hold"
    assert result["decision"] == "hold"
    assert result["reason"] == "strategy_routing_action_not_allowed"


def test_router_selected_report_only_candidate_is_hard_gated_to_no_submit() -> None:
    close_momentum = get_strategy_definition("close_momentum_v1")
    candidate = get_strategy_definition("equity_momentum_continuation_v1")
    test_catalog = (
        replace(close_momentum, validation_status="deprecated_metadata"),
        candidate,
    )
    closes = (100.0, 100.5, 100.2, 101.0, 101.2)
    regime_result = classify_regime(
        RegimeClassificationInput(closes=closes, volatility_percent=2.0)
    )
    routing_result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=test_catalog,
            regime_result=regime_result,
        )
    )

    assert routing_result.selected_strategy_id == "equity_momentum_continuation_v1"

    signal_result = evaluate_selected_strategy_signal(
        StrategyEvaluationInput(
            closes=closes,
            selected_strategy_id=routing_result.selected_strategy_id,
        )
    ).signal_result
    action_proposal = build_action_proposal(
        symbol="AAPL",
        qty=1,
        signal_result=signal_result,
    )
    final_proposal = main.apply_strategy_routing_submit_gate(
        action_proposal,
        RuntimeStrategySeamResult(
            regime_id=routing_result.regime_id,
            selected_strategy_id=routing_result.selected_strategy_id,
            routing_reason=routing_result.reason,
            eligible_strategy_ids=routing_result.eligible_strategy_ids,
            rejected_strategy_ids=routing_result.rejected_strategy_ids,
        ),
    )

    assert action_proposal["should_submit"] is True
    assert action_proposal["action"] == "buy"
    assert final_proposal["should_submit"] is False
    assert final_proposal["action"] == "hold"
    assert final_proposal["decision"] == "hold"
    assert final_proposal["reason"] == "strategy_report_only_candidate_no_submit"


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
    strategy_evaluated_events = _strategy_events(
        main_harness["events"],
        "strategy_evaluated",
    )
    assert len(strategy_evaluated_events) == 1
    for field_name in (
        "regime_id",
        "selected_strategy_id",
        "routing_reason",
        "eligible_strategy_ids",
        "rejected_strategy_ids",
    ):
        assert field_name not in strategy_evaluated_events[0]["payload"]
    assert len(main_harness["observations"]) == 1
    _assert_no_flat_routing_fields(main_harness["observations"][0])


def test_metadata_assembly_failure_does_not_change_runtime_decision_fields(
    monkeypatch, main_harness
) -> None:
    monkeypatch.setattr(
        "main.build_runtime_strategy_metadata",
        lambda _input_model: (_ for _ in ()).throw(ValueError("metadata failed")),
    )

    main.main()

    assert main_harness["action_proposal_calls"]
    assert len(main_harness["signal_generation_calls"]) == 1
    assert main_harness["signal_generation_calls"][0][0][0] == [
        100.0,
        100.2,
        100.4,
        100.8,
        101.2,
    ]
    assert main_harness["strategy_evaluator_calls"] == []
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
    _assert_flat_routing_fields(
        main_harness["observations"][0],
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )


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
