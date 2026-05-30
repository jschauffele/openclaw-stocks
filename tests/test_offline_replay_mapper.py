from __future__ import annotations

import json
import sys
from pathlib import Path
from types import FunctionType

import tools.replay.offline_mapper as offline_mapper
import tools.replay.package_schema as package_schema
from tools.replay.offline_mapper import build_replay_package
from tools.replay.package_schema import (
    AUTHORITY_BOUNDARY,
    ENVELOPE_SECTIONS,
    OUT_OF_SCOPE,
)


EVIDENCE_CANDIDATE_DIR = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "3_close_trend_confirmation"
    / "local_alpaca_2026_01_02_to_2026_05_24"
)


def _event_payloads() -> list[dict]:
    return [
        {
            "schema_version": 1,
            "run_id": "run_1",
            "event_id": "evt_0001",
            "event_type": "data",
            "stage": "market_input_captured",
            "timestamp_utc": "2026-05-01T14:30:00Z",
            "timestamp": "2026-05-01T14:30:00Z",
            "status": "ok",
            "payload": {
                "symbol": "AAPL",
                "timeframe": "5Min",
                "candles": [{"close": 100.0}],
            },
        },
        {
            "schema_version": 1,
            "run_id": "run_1",
            "event_id": "evt_0002",
            "event_type": "strategy",
            "stage": "strategy_evaluated",
            "timestamp_utc": "2026-05-01T14:31:00Z",
            "timestamp": "2026-05-01T14:31:00Z",
            "status": "ok",
            "payload": {
                "signal": "buy",
                "decision": "buy",
                "action": "buy",
                "reason": "test_signal",
            },
        },
        {
            "schema_version": 1,
            "run_id": "run_1",
            "event_id": "evt_0003",
            "event_type": "risk",
            "stage": "risk_check",
            "timestamp_utc": "2026-05-01T14:32:00Z",
            "timestamp": "2026-05-01T14:32:00Z",
            "status": "ok",
            "payload": {"passed": True, "symbol": "AAPL", "qty": 1},
        },
    ]


def _run_report() -> dict:
    return {
        "run_id": "run_1",
        "timestamp": "2026-05-01T14:33:00Z",
        "trigger_source": "test",
        "result": "success",
        "reason": "paper_order_submitted",
        "symbol": "AAPL",
        "side": "buy",
        "qty": 1,
        "orchestration": {
            "runtime_visibility": {
                "runtime_visibility_reports": [],
                "runtime_visibility_blocking": False,
                "runtime_visibility_reason": "runtime_visibility_clear",
            }
        },
    }


def _observations() -> list[dict]:
    return [
        {
            "timestamp_utc": "2026-05-01T14:33:00Z",
            "run_id": "run_1",
            "symbol": "AAPL",
            "signal": "buy",
            "action": "buy",
            "result": "success",
            "reason": "test_signal",
        }
    ]


def _order_state() -> dict:
    return {
        "run_id": "run_1",
        "timestamp": "2026-05-01T14:33:00Z",
        "symbol": "AAPL",
        "side": "buy",
        "qty": 1,
        "mode": "paper_submit",
    }


def _runtime_visibility() -> dict:
    return {
        "runtime_visibility_reports": [],
        "runtime_visibility_blocking": False,
        "runtime_visibility_reason": "runtime_visibility_clear",
    }


def _committed_candidate_artifacts() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(EVIDENCE_CANDIDATE_DIR.glob("*_candidates.json"))
    ]


def test_mapper_returns_documented_top_level_envelope_sections() -> None:
    package = build_replay_package(events=_event_payloads())

    assert tuple(package) == ENVELOPE_SECTIONS


def test_mapper_uses_in_memory_inputs_and_preserves_source_payload_shapes() -> None:
    events = _event_payloads()
    run_report = _run_report()
    observations = _observations()
    order_state = _order_state()
    runtime_visibility = _runtime_visibility()

    package = build_replay_package(
        events=events,
        run_report=run_report,
        observations=observations,
        order_state=order_state,
        runtime_visibility=runtime_visibility,
    )

    assert package["package_status"]["status"] == "complete"
    assert package["run_identity"]["run_id"] == "run_1"
    assert package["event_order_references"]["events"] == events
    assert package["configuration_references"]["run_report"] == run_report
    assert package["reconciliation_risk_references"]["observations"] == observations
    assert (
        package["portfolio_risk_snapshot_references"]["order_state"]
        == order_state
    )
    assert (
        package["broker_visible_state_references"]["runtime_visibility"]
        == runtime_visibility
    )
    assert package["authority_boundary"] == AUTHORITY_BOUNDARY


def test_missing_sections_are_marked_absent_without_inventing_facts() -> None:
    package = build_replay_package(events=[])

    assert package["package_status"]["status"] == "incomplete"
    assert package["package_status"]["section_statuses"] == {
        "events": "absent",
        "run_report": "absent",
        "observations": "absent",
        "order_state": "absent",
        "runtime_visibility": "absent",
    }
    assert package["package_identity"] == {
        "status": "absent",
        "reason": "run_id_not_supplied",
    }
    assert package["event_order_references"] == {
        "status": "absent",
        "reason": "events_not_supplied",
    }
    assert package["integrity"]["reason"] == "deferred_until_integrity_gate"
    assert package["immutability"]["reason"] == "deferred_until_storage_gate"


def test_mapper_does_not_mutate_inputs_or_return_input_objects_by_identity() -> None:
    events = _event_payloads()
    run_report = _run_report()
    observations = _observations()
    order_state = _order_state()
    runtime_visibility = _runtime_visibility()
    original = (
        repr(events),
        repr(run_report),
        repr(observations),
        repr(order_state),
        repr(runtime_visibility),
    )

    package = build_replay_package(
        events=events,
        run_report=run_report,
        observations=observations,
        order_state=order_state,
        runtime_visibility=runtime_visibility,
    )

    assert (
        repr(events),
        repr(run_report),
        repr(observations),
        repr(order_state),
        repr(runtime_visibility),
    ) == original
    assert package["event_order_references"]["events"] is not events
    assert package["configuration_references"]["run_report"] is not run_report
    assert package["reconciliation_risk_references"]["observations"] is not observations
    assert package["portfolio_risk_snapshot_references"]["order_state"] is not order_state
    assert (
        package["broker_visible_state_references"]["runtime_visibility"]
        is not runtime_visibility
    )


def test_partial_candidate_artifact_shape_maps_to_incomplete_replay_package() -> None:
    run_id = "run_2026-05-26T13:45:27Z_efa92a"
    market_input_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0001",
        "event_type": "data",
        "stage": "market_input_captured",
        "timestamp_utc": "2026-05-26T13:45:28Z",
        "timestamp": "2026-05-26T13:45:28Z",
        "status": "ok",
        "payload": {
            "symbol": "AAPL",
            "timeframe": "5Min",
            "source": "alpaca",
            "adjustment": "raw",
            "adjusted": False,
            "warnings": [],
            "candles": [
                {
                    "timestamp": "2026-05-26T13:30:00+00:00",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.5,
                    "close": 100.4,
                    "volume": 1000.0,
                },
                {
                    "timestamp": "2026-05-26T13:35:00+00:00",
                    "open": 100.4,
                    "high": 101.4,
                    "low": 100.1,
                    "close": 100.9,
                    "volume": 1100.0,
                },
                {
                    "timestamp": "2026-05-26T13:40:00+00:00",
                    "open": 100.9,
                    "high": 101.8,
                    "low": 100.6,
                    "close": 101.5,
                    "volume": 1200.0,
                },
            ],
        },
    }
    strategy_evaluated_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0002",
        "event_type": "strategy",
        "stage": "strategy_evaluated",
        "timestamp_utc": "2026-05-26T13:45:29Z",
        "timestamp": "2026-05-26T13:45:29Z",
        "status": "ok",
        "payload": {
            "signal": "buy",
            "decision": "buy",
            "action": "buy",
            "reason": "percent_change_meets_buy_threshold",
            "previous_close": 100.9,
            "latest_close": 101.5,
            "price_delta": 0.6,
            "percent_change": 0.5946481665014867,
            "three_close_percent_change": 1.095617529880476,
        },
    }
    action_proposal_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0003",
        "event_type": "strategy",
        "stage": "action_proposal",
        "timestamp_utc": "2026-05-26T13:45:30Z",
        "timestamp": "2026-05-26T13:45:30Z",
        "status": "blocked",
        "payload": {
            "signal": "buy",
            "decision": "buy",
            "action": "buy",
            "reason": "strategy_hold",
        },
    }
    completion_event = {
        "schema_version": 1,
        "run_id": run_id,
        "event_id": "evt_0004",
        "event_type": "system",
        "stage": "completion",
        "timestamp_utc": "2026-05-26T13:45:31Z",
        "timestamp": "2026-05-26T13:45:31Z",
        "status": "blocked",
        "payload": {"reason": "strategy_hold"},
    }
    events = [
        market_input_event,
        strategy_evaluated_event,
        action_proposal_event,
        completion_event,
    ]
    observations = [
        {
            "timestamp_utc": "2026-05-26T13:45:30Z",
            "run_id": run_id,
            "symbol": "AAPL",
            "signal": "buy",
            "action": "buy",
            "result": "blocked",
            "reason": "strategy_hold",
            "previous_close": 100.9,
            "latest_close": 101.5,
            "price_delta": 0.6,
            "percent_change": 0.5946481665014867,
            "three_close_percent_change": 1.095617529880476,
            "signal_timeframe": "5Min",
            "signal_limit": 5,
            "latest_candle_timestamp": "2026-05-26T13:40:00+00:00",
        }
    ]

    package = build_replay_package(events=events, observations=observations)

    assert package["package_status"]["status"] == "incomplete"
    assert package["package_status"]["section_statuses"] == {
        "events": "present",
        "run_report": "absent",
        "observations": "present",
        "order_state": "absent",
        "runtime_visibility": "absent",
    }
    assert package["event_order_references"]["events"] == events
    assert package["event_order_references"]["events"] is not events
    assert package["market_input_references"]["events"] == [market_input_event]
    assert package["market_input_references"]["events"][0] is not market_input_event
    assert package["strategy_decision_references"]["events"] == [
        strategy_evaluated_event,
        action_proposal_event,
    ]
    assert completion_event in package["event_order_references"]["events"]
    assert package["reconciliation_risk_references"]["observations"] == observations
    assert (
        package["reconciliation_risk_references"]["observations"]
        is not observations
    )
    assert package["configuration_references"] == {
        "status": "absent",
        "reason": "not_supplied",
    }
    assert package["portfolio_risk_snapshot_references"] == {
        "status": "absent",
        "reason": "portfolio_risk_reference_not_supplied",
    }
    assert package["broker_visible_state_references"] == {
        "status": "absent",
        "reason": "broker_visible_reference_not_supplied",
    }


def test_mapper_rejects_non_loaded_input_shapes() -> None:
    try:
        build_replay_package(events={"run_id": "run_1"})  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "events must be a list of dictionaries"
    else:
        raise AssertionError("expected TypeError")

    try:
        build_replay_package(events=str(EVIDENCE_CANDIDATE_DIR))  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "events must be a list of dictionaries"
    else:
        raise AssertionError("expected TypeError")

    try:
        build_replay_package(events=[], run_report=[])  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "optional replay inputs must be dictionaries"
    else:
        raise AssertionError("expected TypeError")


def test_committed_three_close_candidate_jsons_are_review_inputs_not_replay_packages() -> None:
    artifacts = _committed_candidate_artifacts()

    assert {artifact["artifact_type"] for artifact in artifacts} == {
        "review_input_not_test",
    }
    assert {artifact["schema"] for artifact in artifacts} == {
        "openclaw_3_close_evidence_candidates_v1",
    }

    for artifact in artifacts:
        assert "package_status" not in artifact
        assert "event_order_references" not in artifact
        assert "authority_boundary" not in artifact
        assert "out_of_scope" not in artifact
        assert artifact["candidates"]
        for candidate in artifact["candidates"]:
            assert candidate["reviewer_decision"] == "PENDING_REVIEW"
            assert candidate["review_status"] == "GENERATED_CANDIDATE_NOT_ACCEPTED"


def test_candidate_artifacts_cannot_be_promoted_to_complete_replay_packages() -> None:
    artifacts = _committed_candidate_artifacts()

    for artifact in artifacts:
        package = build_replay_package(
            events=artifact["candidates"],
            run_report=artifact,
        )

        assert package["package_status"]["status"] == "incomplete"
        assert package["package_status"]["section_statuses"] == {
            "events": "present",
            "run_report": "present",
            "observations": "absent",
            "order_state": "absent",
            "runtime_visibility": "absent",
        }
        assert package["market_input_references"] == {
            "status": "absent",
            "reason": "market_input_event_not_supplied",
        }
        assert package["portfolio_risk_snapshot_references"] == {
            "status": "present",
            "run_report": artifact,
            "order_state": None,
        }
        assert package["broker_visible_state_references"] == {
            "status": "present",
            "run_report": artifact,
            "runtime_visibility": None,
        }
        assert package["integrity"]["reason"] == "deferred_until_integrity_gate"
        assert package["immutability"]["reason"] == "deferred_until_storage_gate"
        assert package["authority_boundary"] == AUTHORITY_BOUNDARY
        assert package["out_of_scope"] == OUT_OF_SCOPE
        assert package["out_of_scope"]["artifact_writer"] is True
        assert package["out_of_scope"]["runtime_capture"] is True
        assert package["out_of_scope"]["storage"] is True
        assert package["out_of_scope"]["broker_live_api_work"] is True
        assert package["out_of_scope"]["replay_based_promotion_decisions"] is True


def test_import_isolation_and_no_side_effect_fragments() -> None:
    forbidden_modules = {
        "main",
        "config",
        "broker_factory",
        "broker_interface",
        "alpaca",
        "ibkr",
        "ib_insync",
        "event_logger",
        "observation_logger",
        "reporting",
        "state_manager",
        "runtime_visibility_preflight",
        "runtime_visibility_orchestrator",
        "runtime_visibility_provider_composer",
    }

    assert forbidden_modules.isdisjoint(sys.modules)
    for module in (package_schema, offline_mapper):
        assert not any(hasattr(module, name) for name in forbidden_modules)

    forbidden_names = {
        "open",
        "Path",
        "environ",
        "getenv",
        "load_dotenv",
        "socket",
        "requests",
        "urllib",
        "subprocess",
        "append_observation",
        "persist_report",
        "log_event",
        "initialize_event_logger",
        "write_order_state",
        "write_run_report",
    }

    for module in (package_schema, offline_mapper):
        for value in module.__dict__.values():
            if isinstance(value, FunctionType):
                assert forbidden_names.isdisjoint(value.__code__.co_names)
