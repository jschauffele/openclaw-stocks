from __future__ import annotations

import sys

import pytest

import strategy_router
from regime_classifier import RegimeClassificationResult
from strategy_library import StrategyDefinition
from strategy_router import (
    StrategyRoutingInput,
    StrategyRoutingResult,
    route_strategy,
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
    "strategy_engine",
    "signal_validator",
    "market_data",
)


def test_selects_first_active_eligible_strategy_deterministically() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(
                strategy_definition("first"),
                strategy_definition("second"),
            ),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id == "first"
    assert result.reason == "selected_first_eligible_strategy"
    assert result.eligible_strategy_ids == ("first", "second")
    assert result.rejected_strategy_ids == ()


def test_returns_none_when_no_strategies_are_eligible() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(
                strategy_definition(
                    "uptrend_only",
                    allowed_regimes=("uptrend",),
                ),
            ),
            regime_result=regime_result("downtrend"),
        )
    )

    assert result.selected_strategy_id is None
    assert result.reason == "no_eligible_strategy"
    assert result.eligible_strategy_ids == ()
    assert result.rejected_strategy_ids == ("uptrend_only",)


def test_preserves_catalog_order() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(
                strategy_definition("beta"),
                strategy_definition("alpha"),
            ),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id == "beta"
    assert result.eligible_strategy_ids == ("beta", "alpha")


def test_rejects_duplicate_strategy_ids() -> None:
    with pytest.raises(ValueError, match="Duplicate strategy_id"):
        StrategyRoutingInput(
            strategy_catalog=(
                strategy_definition("duplicate"),
                strategy_definition("duplicate"),
            ),
            regime_result=regime_result("sideways"),
        )


def test_rejects_empty_catalog() -> None:
    with pytest.raises(ValueError, match="strategy_catalog must be non-empty"):
        StrategyRoutingInput(
            strategy_catalog=(),
            regime_result=regime_result("sideways"),
        )


def test_rejects_execution_authority_metadata() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(
                strategy_definition("runtime_enabled", execution_authority=True),
            ),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id is None
    assert result.rejected_strategy_ids == ("runtime_enabled",)


def test_mutated_execution_authority_metadata_remains_rejected() -> None:
    strategy = strategy_definition("runtime_enabled")
    object.__setattr__(strategy, "execution_authority", True)

    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(strategy,),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id is None
    assert result.rejected_strategy_ids == ("runtime_enabled",)


def test_rejects_broker_compatibility_metadata() -> None:
    strategy = strategy_definition("broker_enabled")
    object.__setattr__(strategy, "broker_compatibility", ("paper",))

    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(strategy,),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id is None
    assert result.rejected_strategy_ids == ("broker_enabled",)


def test_mutated_broker_compatibility_metadata_remains_rejected() -> None:
    strategy = strategy_definition("broker_enabled")
    object.__setattr__(strategy, "broker_compatibility", ("paper",))

    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(strategy,),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id is None
    assert result.rejected_strategy_ids == ("broker_enabled",)


def test_rejects_non_active_validation_status_metadata() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(
                strategy_definition("scaffolded", validation_status="scaffolded"),
                strategy_definition(
                    "deprecated",
                    validation_status="deprecated_metadata",
                ),
            ),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id is None
    assert result.rejected_strategy_ids == ("scaffolded", "deprecated")


def test_honors_allowed_regimes_when_present() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(
                strategy_definition("sideways_only", allowed_regimes=("sideways",)),
                strategy_definition("uptrend_only", allowed_regimes=("uptrend",)),
            ),
            regime_result=regime_result("sideways"),
        )
    )

    assert result.selected_strategy_id == "sideways_only"
    assert result.eligible_strategy_ids == ("sideways_only",)
    assert result.rejected_strategy_ids == ("uptrend_only",)


def test_empty_allowed_regimes_are_regime_agnostic_metadata() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(strategy_definition("agnostic", allowed_regimes=()),),
            regime_result=regime_result("volatile"),
        )
    )

    assert result.selected_strategy_id == "agnostic"
    assert result.eligible_strategy_ids == ("agnostic",)


def test_route_strategy_result_regime_id_matches_input_regime_result() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(strategy_definition("agnostic"),),
            regime_result=regime_result("volatile"),
        )
    )

    assert result.regime_id == "volatile"


def test_input_and_result_dataclasses_are_frozen() -> None:
    input_model = StrategyRoutingInput(
        strategy_catalog=(strategy_definition("example"),),
        regime_result=regime_result("sideways"),
    )
    result = route_strategy(input_model)

    with pytest.raises(AttributeError):
        input_model.strategy_catalog = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.selected_strategy_id = None  # type: ignore[misc]


def test_result_exposes_no_execution_broker_risk_order_action_or_signal_fields() -> None:
    result = route_strategy(
        StrategyRoutingInput(
            strategy_catalog=(strategy_definition("example"),),
            regime_result=regime_result("sideways"),
        )
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
        "route",
        "strategy_execution",
    }

    assert forbidden_fields.isdisjoint(result.__dataclass_fields__)


def test_import_does_not_load_forbidden_modules() -> None:
    loaded_modules = set(sys.modules)

    assert not loaded_modules.intersection(FORBIDDEN_MODULES)
    assert not any(module_name.startswith("ibkr_") for module_name in loaded_modules)
    assert not any(
        module_name.startswith("manual_ibkr_") for module_name in loaded_modules
    )


def test_repeated_calls_return_equal_results() -> None:
    input_model = StrategyRoutingInput(
        strategy_catalog=(strategy_definition("example"),),
        regime_result=regime_result("sideways"),
    )

    assert route_strategy(input_model) == route_strategy(input_model)


def test_route_strategy_rejects_non_input_model() -> None:
    with pytest.raises(ValueError, match="input_model must be StrategyRoutingInput"):
        route_strategy({"strategy_catalog": ()})  # type: ignore[arg-type]


def test_router_does_not_call_classify_regime_or_run_strategy_logic() -> None:
    assert not hasattr(strategy_router, "classify_regime")
    assert not hasattr(strategy_router, "generate_signal_from_closes")
    assert not hasattr(strategy_router, "validate_signal_result")


def test_rejects_non_strategy_catalog_entries() -> None:
    with pytest.raises(
        ValueError,
        match="strategy_catalog must contain StrategyDefinition",
    ):
        StrategyRoutingInput(
            strategy_catalog=("not_strategy",),  # type: ignore[arg-type]
            regime_result=regime_result("sideways"),
        )


def test_rejects_non_regime_result() -> None:
    with pytest.raises(ValueError, match="regime_result must be RegimeClassificationResult"):
        StrategyRoutingInput(
            strategy_catalog=(strategy_definition("example"),),
            regime_result="sideways",  # type: ignore[arg-type]
        )


def test_routing_result_rejects_blank_reason_and_regime() -> None:
    with pytest.raises(ValueError, match="reason must be non-empty"):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason=" ",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )

    with pytest.raises(ValueError, match="regime_id must be non-empty"):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id=" ",
            reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )


def test_routing_result_rejects_blank_selected_strategy_id() -> None:
    with pytest.raises(ValueError, match="selected_strategy_id must be non-empty"):
        StrategyRoutingResult(
            selected_strategy_id=" ",
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )


def test_routing_result_rejects_non_tuple_evidence_ids() -> None:
    with pytest.raises(ValueError, match="eligible_strategy_ids must be a tuple"):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=["a"],  # type: ignore[arg-type]
            rejected_strategy_ids=(),
        )

    with pytest.raises(ValueError, match="rejected_strategy_ids must be a tuple"):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=["a"],  # type: ignore[arg-type]
        )


def test_routing_result_rejects_non_string_evidence_ids() -> None:
    with pytest.raises(ValueError, match="eligible_strategy_ids must contain strings"):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=("a", 1),  # type: ignore[arg-type]
            rejected_strategy_ids=(),
        )

    with pytest.raises(ValueError, match="rejected_strategy_ids must contain strings"):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("a", 1),  # type: ignore[arg-type]
        )


def test_routing_result_rejects_blank_evidence_ids() -> None:
    with pytest.raises(
        ValueError,
        match="eligible_strategy_ids must contain non-empty strings",
    ):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=(" ",),
            rejected_strategy_ids=(),
        )

    with pytest.raises(
        ValueError,
        match="rejected_strategy_ids must contain non-empty strings",
    ):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(" ",),
        )


def test_routing_result_rejects_duplicate_eligible_ids() -> None:
    with pytest.raises(
        ValueError,
        match="eligible_strategy_ids contains duplicate strategy_id",
    ):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=("a", "a"),
            rejected_strategy_ids=(),
        )


def test_routing_result_rejects_duplicate_rejected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="rejected_strategy_ids contains duplicate strategy_id",
    ):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("a", "a"),
        )


def test_routing_result_rejects_overlap_between_eligible_and_rejected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="strategy ID appears in both eligible and rejected",
    ):
        StrategyRoutingResult(
            selected_strategy_id=None,
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=("a",),
            rejected_strategy_ids=("a",),
        )


def test_routing_result_rejects_selected_strategy_not_in_eligible_ids() -> None:
    with pytest.raises(
        ValueError,
        match="selected_strategy_id must be present in eligible_strategy_ids",
    ):
        StrategyRoutingResult(
            selected_strategy_id="missing",
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=("a",),
            rejected_strategy_ids=(),
        )


def test_routing_result_rejects_selected_strategy_when_eligible_ids_empty() -> None:
    with pytest.raises(
        ValueError,
        match="selected_strategy_id requires non-empty eligible_strategy_ids",
    ):
        StrategyRoutingResult(
            selected_strategy_id="missing",
            regime_id="sideways",
            reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )


def strategy_definition(
    strategy_id: str,
    *,
    allowed_regimes: tuple[str, ...] = (),
    execution_authority: bool = False,
    validation_status: str = "active_metadata",
) -> StrategyDefinition:
    return StrategyDefinition(
        strategy_id=strategy_id,
        version="1.0.0",
        name=f"Strategy {strategy_id}",
        description="Strategy metadata for routing tests.",
        family="test",
        required_inputs=("closes",),
        output_schema=("signal",),
        allowed_regimes=allowed_regimes,
        validation_status=validation_status,
        execution_authority=execution_authority,
    )


def regime_result(regime_id: str) -> RegimeClassificationResult:
    return RegimeClassificationResult(
        regime_id=regime_id,
        reason="test_regime",
        lookback=5,
        sample_count=5,
        latest_close=101.0,
        oldest_close=100.0,
        percent_change=1.0,
        absolute_percent_change=1.0,
        max_one_period_move_percent=1.0,
    )
