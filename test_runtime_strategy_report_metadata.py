from __future__ import annotations

import inspect

import pytest

import runtime_strategy_report_metadata
from runtime_strategy_metadata_adapter import StrategyArchitectureMetadata
from runtime_strategy_report_metadata import (
    build_orchestration_strategy_architecture_payload,
)


def _metadata() -> StrategyArchitectureMetadata:
    return StrategyArchitectureMetadata(
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )


def test_accepts_strategy_architecture_metadata() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())

    assert isinstance(payload, dict)


def test_rejects_non_strategy_architecture_metadata_input() -> None:
    with pytest.raises(ValueError, match="metadata must be StrategyArchitectureMetadata"):
        build_orchestration_strategy_architecture_payload(
            {"regime_id": "uptrend"}  # type: ignore[arg-type]
        )


def test_returns_exact_top_level_strategy_architecture_key() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())

    assert tuple(payload) == ("strategy_architecture",)


def test_nested_fields_match_documented_contract() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())
    strategy_architecture = payload["strategy_architecture"]

    assert tuple(strategy_architecture) == (  # type: ignore[arg-type]
        "metadata_schema_version",
        "regime_id",
        "selected_strategy_id",
        "routing_reason",
        "eligible_strategy_ids",
        "rejected_strategy_ids",
        "source",
    )


def test_copies_metadata_fields_exactly() -> None:
    metadata = _metadata()
    payload = build_orchestration_strategy_architecture_payload(metadata)
    strategy_architecture = payload["strategy_architecture"]

    assert strategy_architecture == {
        "metadata_schema_version": metadata.metadata_schema_version,
        "regime_id": metadata.regime_id,
        "selected_strategy_id": metadata.selected_strategy_id,
        "routing_reason": metadata.routing_reason,
        "eligible_strategy_ids": metadata.eligible_strategy_ids,
        "rejected_strategy_ids": metadata.rejected_strategy_ids,
        "source": metadata.source,
    }


def test_source_equals_runtime_strategy_seam() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())
    strategy_architecture = payload["strategy_architecture"]

    assert strategy_architecture["source"] == "runtime_strategy_seam"  # type: ignore[index]


def test_metadata_schema_version_is_first_nested_report_field() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())
    strategy_architecture = payload["strategy_architecture"]

    assert tuple(strategy_architecture)[0] == "metadata_schema_version"  # type: ignore[arg-type]
    assert strategy_architecture["metadata_schema_version"] == "1"  # type: ignore[index]


def test_eligible_and_rejected_ids_remain_tuples() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())
    strategy_architecture = payload["strategy_architecture"]

    assert isinstance(strategy_architecture["eligible_strategy_ids"], tuple)  # type: ignore[index]
    assert isinstance(strategy_architecture["rejected_strategy_ids"], tuple)  # type: ignore[index]


def test_no_extra_top_level_keys() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())

    assert set(payload) == {"strategy_architecture"}


def test_no_extra_nested_keys() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())

    assert set(payload["strategy_architecture"]) == {  # type: ignore[arg-type]
        "metadata_schema_version",
        "regime_id",
        "selected_strategy_id",
        "routing_reason",
        "eligible_strategy_ids",
        "rejected_strategy_ids",
        "source",
    }


def test_result_exposes_no_persistence_reporting_observation_or_event_fields() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())
    forbidden_fields = {
        "persist",
        "persistence",
        "report",
        "reporting",
        "observation",
        "observations",
        "event",
        "events",
        "jsonl",
        "last_run_report",
    }

    assert forbidden_fields.isdisjoint(payload)
    assert forbidden_fields.isdisjoint(payload["strategy_architecture"])  # type: ignore[arg-type]


def test_result_exposes_no_signal_action_risk_order_broker_or_runtime_fields() -> None:
    payload = build_orchestration_strategy_architecture_payload(_metadata())
    forbidden_fields = {
        "signal",
        "decision",
        "action",
        "risk",
        "order",
        "order_id",
        "qty",
        "side",
        "submit",
        "cancel",
        "flatten",
        "broker",
        "execution",
        "runtime",
    }

    assert forbidden_fields.isdisjoint(payload)
    assert forbidden_fields.isdisjoint(payload["strategy_architecture"])  # type: ignore[arg-type]


def test_module_does_not_import_main_reporting_observation_or_event_modules() -> None:
    assert not hasattr(runtime_strategy_report_metadata, "main")
    assert not hasattr(runtime_strategy_report_metadata, "reporting")
    assert not hasattr(runtime_strategy_report_metadata, "persist_report")
    assert not hasattr(runtime_strategy_report_metadata, "append_observation")
    assert not hasattr(runtime_strategy_report_metadata, "log_event")


def test_module_does_not_import_forbidden_outer_modules() -> None:
    assert not hasattr(runtime_strategy_report_metadata, "config")
    assert not hasattr(runtime_strategy_report_metadata, "broker_factory")
    assert not hasattr(runtime_strategy_report_metadata, "risk_engine")
    assert not hasattr(runtime_strategy_report_metadata, "execution_engine")
    assert not hasattr(runtime_strategy_report_metadata, "state_manager")
    assert not hasattr(runtime_strategy_report_metadata, "market_data")
    assert not hasattr(runtime_strategy_report_metadata, "strategy_engine")


def test_repeated_calls_return_equal_payloads() -> None:
    metadata = _metadata()

    assert build_orchestration_strategy_architecture_payload(metadata) == (
        build_orchestration_strategy_architecture_payload(metadata)
    )


def test_no_file_env_or_network_side_effect_fragments_are_present() -> None:
    source = inspect.getsource(runtime_strategy_report_metadata)
    forbidden_fragments = (
        "open(",
        "os.environ",
        "getenv",
        "socket",
        "requests",
        "urllib",
        "subprocess",
    )

    assert not any(fragment in source for fragment in forbidden_fragments)
