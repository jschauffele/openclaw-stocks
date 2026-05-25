from __future__ import annotations

import inspect

import pytest

import runtime_strategy_metadata_adapter
from runtime_strategy_metadata_adapter import (
    STRATEGY_ARCHITECTURE_SOURCE,
    StrategyArchitectureMetadata,
    build_strategy_architecture_metadata,
)
from runtime_strategy_seam import RuntimeStrategySeamResult


def _seam_result() -> RuntimeStrategySeamResult:
    return RuntimeStrategySeamResult(
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )


def test_accepts_runtime_strategy_seam_result_and_returns_metadata() -> None:
    metadata = build_strategy_architecture_metadata(_seam_result())

    assert isinstance(metadata, StrategyArchitectureMetadata)


def test_metadata_fields_match_documented_strategy_architecture_contract() -> None:
    metadata = build_strategy_architecture_metadata(_seam_result())

    assert tuple(metadata.__dataclass_fields__) == (
        "metadata_schema_version",
        "regime_id",
        "selected_strategy_id",
        "routing_reason",
        "eligible_strategy_ids",
        "rejected_strategy_ids",
        "source",
    )


def test_metadata_schema_version_defaults_to_deterministic_value() -> None:
    metadata = build_strategy_architecture_metadata(_seam_result())

    assert metadata.metadata_schema_version == "1"


def test_copies_runtime_strategy_seam_result_fields() -> None:
    seam_result = _seam_result()
    metadata = build_strategy_architecture_metadata(seam_result)

    assert metadata.metadata_schema_version == "1"
    assert metadata.regime_id == seam_result.regime_id
    assert metadata.selected_strategy_id == seam_result.selected_strategy_id
    assert metadata.routing_reason == seam_result.routing_reason
    assert metadata.eligible_strategy_ids == seam_result.eligible_strategy_ids
    assert metadata.rejected_strategy_ids == seam_result.rejected_strategy_ids


def test_source_equals_runtime_strategy_seam() -> None:
    metadata = build_strategy_architecture_metadata(_seam_result())

    assert metadata.source == "runtime_strategy_seam"
    assert metadata.source == STRATEGY_ARCHITECTURE_SOURCE


def test_eligible_and_rejected_strategy_ids_remain_tuples() -> None:
    metadata = build_strategy_architecture_metadata(_seam_result())

    assert isinstance(metadata.eligible_strategy_ids, tuple)
    assert isinstance(metadata.rejected_strategy_ids, tuple)


def test_rejects_non_runtime_strategy_seam_result_input() -> None:
    with pytest.raises(ValueError, match="seam_result must be RuntimeStrategySeamResult"):
        build_strategy_architecture_metadata({"regime_id": "uptrend"})  # type: ignore[arg-type]


def test_metadata_rejects_blank_regime_id() -> None:
    with pytest.raises(ValueError, match="regime_id must be non-empty"):
        StrategyArchitectureMetadata(
            regime_id=" ",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        )


def test_metadata_rejects_blank_routing_reason() -> None:
    with pytest.raises(ValueError, match="routing_reason must be non-empty"):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason=" ",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        )


def test_metadata_rejects_invalid_source() -> None:
    with pytest.raises(ValueError, match="source must be runtime_strategy_seam"):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
            source="main",
        )


def test_metadata_rejects_malformed_eligible_and_rejected_id_tuples() -> None:
    with pytest.raises(ValueError, match="eligible_strategy_ids must be a tuple"):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=["close_momentum_v1"],  # type: ignore[arg-type]
            rejected_strategy_ids=(),
        )
    with pytest.raises(ValueError, match="rejected_strategy_ids must be a tuple"):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=["other_strategy"],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="eligible_strategy_ids must contain strings"):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(123,),  # type: ignore[arg-type]
            rejected_strategy_ids=(),
        )
    with pytest.raises(
        ValueError, match="rejected_strategy_ids must contain non-empty strings"
    ):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(" ",),
        )


def test_metadata_rejects_duplicate_ids() -> None:
    with pytest.raises(
        ValueError,
        match="eligible_strategy_ids contains duplicate strategy_id: close_momentum_v1",
    ):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1", "close_momentum_v1"),
            rejected_strategy_ids=(),
        )
    with pytest.raises(
        ValueError,
        match="rejected_strategy_ids contains duplicate strategy_id: close_momentum_v1",
    ):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1", "close_momentum_v1"),
        )


def test_metadata_rejects_overlap_between_eligible_and_rejected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="strategy ID appears in both eligible and rejected: close_momentum_v1",
    ):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=("close_momentum_v1",),
        )


def test_metadata_rejects_selected_strategy_id_not_present_in_eligible_ids() -> None:
    with pytest.raises(
        ValueError,
        match="selected_strategy_id must be present in eligible_strategy_ids",
    ):
        StrategyArchitectureMetadata(
            regime_id="sideways",
            selected_strategy_id="missing_strategy",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        )


def test_metadata_exposes_no_persistence_reporting_observation_or_event_fields() -> None:
    metadata = build_strategy_architecture_metadata(_seam_result())
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

    assert forbidden_fields.isdisjoint(metadata.__dataclass_fields__)


def test_metadata_exposes_no_signal_action_risk_order_broker_or_runtime_fields() -> None:
    metadata = build_strategy_architecture_metadata(_seam_result())
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

    assert forbidden_fields.isdisjoint(metadata.__dataclass_fields__)


def test_module_does_not_import_forbidden_outer_modules() -> None:
    assert not hasattr(runtime_strategy_metadata_adapter, "main")
    assert not hasattr(runtime_strategy_metadata_adapter, "config")
    assert not hasattr(runtime_strategy_metadata_adapter, "persist_report")
    assert not hasattr(runtime_strategy_metadata_adapter, "append_observation")


def test_repeated_calls_return_equal_results() -> None:
    seam_result = _seam_result()

    assert build_strategy_architecture_metadata(seam_result) == (
        build_strategy_architecture_metadata(seam_result)
    )


def test_no_file_env_or_network_side_effect_fragments_are_present() -> None:
    source = inspect.getsource(runtime_strategy_metadata_adapter)
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
