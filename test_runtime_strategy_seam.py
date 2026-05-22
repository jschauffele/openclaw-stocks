from __future__ import annotations

import inspect
import sys

import pytest

import runtime_strategy_seam
from runtime_strategy_seam import (
    RuntimeStrategySeamInput,
    RuntimeStrategySeamResult,
    build_runtime_strategy_metadata,
)


FORBIDDEN_MODULES = (
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


def test_builds_metadata_from_already_available_closes() -> None:
    result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            volatility_percent=2.0,
        )
    )

    assert result == RuntimeStrategySeamResult(
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=("close_momentum_v1",),
        rejected_strategy_ids=(),
    )


def test_propagates_regime_id_from_strategy_integration() -> None:
    result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(closes=(100.0, 103.0, 104.0, 105.0, 106.0))
    )

    assert result.regime_id == "volatile"


def test_propagates_selected_strategy_id() -> None:
    result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(closes=(100.0, 100.1, 100.2, 100.3, 100.4))
    )

    assert result.selected_strategy_id == "close_momentum_v1"


def test_propagates_routing_reason() -> None:
    result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(closes=(100.0, 100.1, 100.2, 100.3, 100.4))
    )

    assert result.routing_reason == "selected_first_eligible_strategy"


def test_propagates_eligible_and_rejected_strategy_ids() -> None:
    result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(closes=(100.0, 100.1, 100.2, 100.3, 100.4))
    )

    assert result.eligible_strategy_ids == ("close_momentum_v1",)
    assert result.rejected_strategy_ids == ()


def test_passes_thresholds_through_to_strategy_integration() -> None:
    sideways_result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            min_trend_percent=2.0,
            volatility_percent=5.0,
        )
    )
    volatile_result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(
            closes=(100.0, 103.0, 104.0, 105.0, 106.0),
            min_trend_percent=2.0,
            volatility_percent=2.0,
        )
    )

    assert sideways_result.regime_id == "sideways"
    assert volatile_result.regime_id == "volatile"


def test_input_and_result_dataclasses_are_frozen() -> None:
    input_model = RuntimeStrategySeamInput(closes=(100.0, 101.0))
    result = build_runtime_strategy_metadata(input_model)

    with pytest.raises(AttributeError):
        input_model.lookback = 3  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.regime_id = "sideways"  # type: ignore[misc]


def test_rejects_non_runtime_strategy_seam_input() -> None:
    with pytest.raises(ValueError, match="input_model must be RuntimeStrategySeamInput"):
        build_runtime_strategy_metadata({"closes": (100.0, 101.0)})  # type: ignore[arg-type]


def test_input_rejects_non_tuple_closes() -> None:
    with pytest.raises(ValueError, match="closes must be a tuple"):
        RuntimeStrategySeamInput(closes=[100.0, 101.0])  # type: ignore[arg-type]


def test_result_rejects_blank_regime_id() -> None:
    with pytest.raises(ValueError, match="regime_id must be non-empty"):
        RuntimeStrategySeamResult(
            regime_id=" ",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        )


def test_result_rejects_blank_routing_reason() -> None:
    with pytest.raises(ValueError, match="routing_reason must be non-empty"):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason=" ",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1",),
        )


def test_result_rejects_non_tuple_eligible_strategy_ids() -> None:
    with pytest.raises(ValueError, match="eligible_strategy_ids must be a tuple"):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=["close_momentum_v1"],  # type: ignore[arg-type]
            rejected_strategy_ids=(),
        )


def test_result_rejects_non_tuple_rejected_strategy_ids() -> None:
    with pytest.raises(ValueError, match="rejected_strategy_ids must be a tuple"):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=["other_strategy"],  # type: ignore[arg-type]
        )


def test_result_rejects_non_string_ids_in_evidence_tuples() -> None:
    with pytest.raises(ValueError, match="eligible_strategy_ids must contain strings"):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(123,),  # type: ignore[typeddict-item]
            rejected_strategy_ids=(),
        )
    with pytest.raises(ValueError, match="rejected_strategy_ids must contain strings"):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(123,),  # type: ignore[typeddict-item]
        )


def test_result_rejects_blank_ids_in_evidence_tuples() -> None:
    with pytest.raises(
        ValueError, match="eligible_strategy_ids must contain non-empty strings"
    ):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(" ",),
            rejected_strategy_ids=(),
        )
    with pytest.raises(
        ValueError, match="rejected_strategy_ids must contain non-empty strings"
    ):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(" ",),
        )


def test_result_rejects_duplicate_eligible_ids() -> None:
    with pytest.raises(
        ValueError,
        match="eligible_strategy_ids contains duplicate strategy_id: close_momentum_v1",
    ):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1", "close_momentum_v1"),
            rejected_strategy_ids=(),
        )


def test_result_rejects_duplicate_rejected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="rejected_strategy_ids contains duplicate strategy_id: close_momentum_v1",
    ):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="no eligible strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("close_momentum_v1", "close_momentum_v1"),
        )


def test_result_rejects_overlap_between_eligible_and_rejected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="strategy ID appears in both eligible and rejected: close_momentum_v1",
    ):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=("close_momentum_v1",),
        )


def test_result_rejects_selected_strategy_not_in_eligible_strategy_ids() -> None:
    with pytest.raises(
        ValueError,
        match="selected_strategy_id must be present in eligible_strategy_ids",
    ):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id="missing_strategy",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=("close_momentum_v1",),
            rejected_strategy_ids=(),
        )


def test_result_rejects_selected_strategy_when_eligible_strategy_ids_is_empty() -> None:
    with pytest.raises(
        ValueError,
        match="selected_strategy_id requires non-empty eligible_strategy_ids",
    ):
        RuntimeStrategySeamResult(
            regime_id="sideways",
            selected_strategy_id="close_momentum_v1",
            routing_reason="selected_first_eligible_strategy",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )


def test_invalid_closes_propagate_value_error() -> None:
    with pytest.raises(ValueError, match="closes must contain positive values"):
        build_runtime_strategy_metadata(RuntimeStrategySeamInput(closes=(100.0, 0.0)))


def test_result_exposes_no_signal_action_order_broker_execution_or_runtime_fields() -> None:
    result = build_runtime_strategy_metadata(
        RuntimeStrategySeamInput(closes=(100.0, 100.1, 100.2, 100.3, 100.4))
    )
    forbidden_fields = {
        "signal",
        "decision",
        "action",
        "order",
        "order_id",
        "qty",
        "side",
        "submit",
        "cancel",
        "flatten",
        "broker",
        "execution",
        "risk",
        "state",
        "observation",
        "reporting",
        "route_to_runtime",
        "strategy_execution",
    }

    assert forbidden_fields.isdisjoint(result.__dataclass_fields__)


def test_module_does_not_import_main_strategy_engine_or_signal_validator() -> None:
    loaded_modules = set(sys.modules)

    assert "main" not in loaded_modules
    assert "strategy_engine" not in loaded_modules
    assert "signal_validator" not in loaded_modules
    assert not hasattr(runtime_strategy_seam, "main")
    assert not hasattr(runtime_strategy_seam, "generate_signal_from_closes")
    assert not hasattr(runtime_strategy_seam, "validate_signal_result")


def test_module_does_not_import_forbidden_outer_modules() -> None:
    loaded_modules = set(sys.modules)

    assert not loaded_modules.intersection(FORBIDDEN_MODULES)
    assert not any(module_name.startswith("ibkr_") for module_name in loaded_modules)
    assert not any(
        module_name.startswith("manual_ibkr_") for module_name in loaded_modules
    )


def test_repeated_calls_return_equal_results() -> None:
    input_model = RuntimeStrategySeamInput(
        closes=(100.0, 100.2, 100.4, 100.8, 101.2),
        volatility_percent=2.0,
    )

    assert build_runtime_strategy_metadata(input_model) == (
        build_runtime_strategy_metadata(input_model)
    )


def test_no_file_env_or_network_side_effects_are_present() -> None:
    source = inspect.getsource(runtime_strategy_seam)
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
