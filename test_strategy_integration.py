from __future__ import annotations

import inspect
import json
import subprocess
import sys

import pytest

import strategy_integration
from strategy_integration import (
    StrategyIntegrationInput,
    StrategyIntegrationResult,
    evaluate_strategy_integration,
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


def test_integrates_default_catalog_regime_classifier_and_router_deterministically() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            volatility_percent=2.0,
        )
    )

    assert result == StrategyIntegrationResult(
        regime_id="uptrend",
        selected_strategy_id="close_momentum_v1",
        routing_reason="selected_first_eligible_strategy",
        eligible_strategy_ids=(
            "close_momentum_v1",
            "equity_momentum_continuation_v1",
        ),
        rejected_strategy_ids=(),
    )


def test_returns_regime_id_from_classify_regime() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(closes=(100.0, 103.0, 104.0, 105.0, 106.0))
    )

    assert result.regime_id == "volatile"


def test_returns_selected_strategy_id_from_route_strategy() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            volatility_percent=2.0,
        )
    )

    assert result.selected_strategy_id == "close_momentum_v1"
    assert result.routing_reason == "selected_first_eligible_strategy"


def test_returns_eligible_and_rejected_ids_from_route_result() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            volatility_percent=2.0,
        )
    )

    assert result.eligible_strategy_ids == (
        "close_momentum_v1",
        "equity_momentum_continuation_v1",
    )
    assert result.rejected_strategy_ids == ()


def test_passes_thresholds_into_regime_classification_behavior() -> None:
    sideways_result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            min_trend_percent=2.0,
            volatility_percent=5.0,
        )
    )
    volatile_result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 103.0, 104.0, 105.0, 106.0),
            min_trend_percent=2.0,
            volatility_percent=2.0,
        )
    )

    assert sideways_result.regime_id == "sideways"
    assert volatile_result.regime_id == "volatile"


def test_close_momentum_strategy_is_not_selected_for_sideways_regime() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(closes=(100.0, 100.1, 99.9, 100.2, 100.4))
    )

    assert result.regime_id == "sideways"
    assert result.selected_strategy_id is None
    assert result.routing_reason == "no_eligible_strategy"
    assert result.eligible_strategy_ids == ()
    assert result.rejected_strategy_ids == (
        "close_momentum_v1",
        "equity_momentum_continuation_v1",
    )


def test_close_momentum_strategy_is_not_selected_for_downtrend_regime() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 99.8, 99.4, 99.1, 98.8),
            volatility_percent=2.0,
        )
    )

    assert result.regime_id == "downtrend"
    assert result.selected_strategy_id is None
    assert result.routing_reason == "no_eligible_strategy"
    assert result.eligible_strategy_ids == ()
    assert result.rejected_strategy_ids == (
        "close_momentum_v1",
        "equity_momentum_continuation_v1",
    )


def test_close_momentum_strategy_is_not_selected_for_volatile_regime() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 103.0, 104.0, 105.0, 106.0),
            min_trend_percent=1.0,
            volatility_percent=2.0,
        )
    )

    assert result.regime_id == "volatile"
    assert result.selected_strategy_id is None
    assert result.routing_reason == "no_eligible_strategy"
    assert result.eligible_strategy_ids == ()
    assert result.rejected_strategy_ids == (
        "close_momentum_v1",
        "equity_momentum_continuation_v1",
    )


def test_input_and_result_dataclasses_are_frozen() -> None:
    input_model = StrategyIntegrationInput(closes=(100.0, 101.0))
    result = evaluate_strategy_integration(input_model)

    with pytest.raises(AttributeError):
        input_model.lookback = 3  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.regime_id = "sideways"  # type: ignore[misc]


def test_input_rejects_non_tuple_closes() -> None:
    with pytest.raises(ValueError, match="closes must be a tuple"):
        StrategyIntegrationInput(closes=[100.0, 101.0])  # type: ignore[arg-type]


def test_invalid_closes_propagate_value_error_from_regime_classifier() -> None:
    with pytest.raises(ValueError, match="closes must contain positive values"):
        evaluate_strategy_integration(StrategyIntegrationInput(closes=(100.0, 0.0)))


def test_invalid_thresholds_propagate_value_error_from_regime_classifier() -> None:
    with pytest.raises(ValueError, match="min_trend_percent must be >= 0"):
        evaluate_strategy_integration(
            StrategyIntegrationInput(
                closes=(100.0, 101.0),
                min_trend_percent=-1.0,
            )
        )

    with pytest.raises(ValueError, match="volatility_percent must be >= 0"):
        evaluate_strategy_integration(
            StrategyIntegrationInput(
                closes=(100.0, 101.0),
                volatility_percent=-1.0,
            )
        )


def test_evaluate_strategy_integration_rejects_non_input_model() -> None:
    with pytest.raises(ValueError, match="input_model must be StrategyIntegrationInput"):
        evaluate_strategy_integration({"closes": (100.0, 101.0)})  # type: ignore[arg-type]


def test_result_rejects_blank_regime_id_and_routing_reason() -> None:
    with pytest.raises(ValueError, match="regime_id must be non-empty"):
        StrategyIntegrationResult(
            regime_id=" ",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )

    with pytest.raises(ValueError, match="routing_reason must be non-empty"):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason=" ",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )


def test_result_rejects_non_tuple_evidence_ids() -> None:
    with pytest.raises(ValueError, match="eligible_strategy_ids must be a tuple"):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=["a"],  # type: ignore[arg-type]
            rejected_strategy_ids=(),
        )

    with pytest.raises(ValueError, match="rejected_strategy_ids must be a tuple"):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=["a"],  # type: ignore[arg-type]
        )


def test_result_rejects_non_string_evidence_ids() -> None:
    with pytest.raises(ValueError, match="eligible_strategy_ids must contain strings"):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=("a", 1),  # type: ignore[arg-type]
            rejected_strategy_ids=(),
        )

    with pytest.raises(ValueError, match="rejected_strategy_ids must contain strings"):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("a", 1),  # type: ignore[arg-type]
        )


def test_result_rejects_blank_evidence_ids() -> None:
    with pytest.raises(
        ValueError,
        match="eligible_strategy_ids must contain non-empty strings",
    ):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=(" ",),
            rejected_strategy_ids=(),
        )

    with pytest.raises(
        ValueError,
        match="rejected_strategy_ids must contain non-empty strings",
    ):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(" ",),
        )


def test_result_rejects_duplicate_eligible_ids() -> None:
    with pytest.raises(
        ValueError,
        match="eligible_strategy_ids contains duplicate strategy_id",
    ):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=("a", "a"),
            rejected_strategy_ids=(),
        )


def test_result_rejects_duplicate_rejected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="rejected_strategy_ids contains duplicate strategy_id",
    ):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=("a", "a"),
        )


def test_result_rejects_overlap_between_eligible_and_rejected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="strategy ID appears in both eligible and rejected",
    ):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id=None,
            routing_reason="example",
            eligible_strategy_ids=("a",),
            rejected_strategy_ids=("a",),
        )


def test_result_rejects_selected_strategy_not_in_eligible_ids() -> None:
    with pytest.raises(
        ValueError,
        match="selected_strategy_id must be present in eligible_strategy_ids",
    ):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id="missing",
            routing_reason="example",
            eligible_strategy_ids=("a",),
            rejected_strategy_ids=(),
        )


def test_result_rejects_selected_strategy_when_eligible_ids_empty() -> None:
    with pytest.raises(
        ValueError,
        match="selected_strategy_id requires non-empty eligible_strategy_ids",
    ):
        StrategyIntegrationResult(
            regime_id="sideways",
            selected_strategy_id="missing",
            routing_reason="example",
            eligible_strategy_ids=(),
            rejected_strategy_ids=(),
        )


def test_result_exposes_no_signal_order_broker_execution_or_runtime_fields() -> None:
    result = evaluate_strategy_integration(
        StrategyIntegrationInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            volatility_percent=2.0,
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
        "state",
        "observation",
        "reporting",
        "route_to_runtime",
        "strategy_execution",
    }

    assert forbidden_fields.isdisjoint(result.__dataclass_fields__)


def test_module_does_not_import_strategy_engine_or_signal_validator() -> None:
    assert not hasattr(strategy_integration, "generate_signal_from_closes")
    assert not hasattr(strategy_integration, "validate_signal_result")
    _assert_clean_import_does_not_load_forbidden_modules("strategy_integration")


def test_module_does_not_import_forbidden_outer_modules() -> None:
    _assert_clean_import_does_not_load_forbidden_modules("strategy_integration")


def test_repeated_calls_return_equal_results() -> None:
    input_model = StrategyIntegrationInput(
        closes=(100.0, 100.2, 100.4, 100.8, 101.2),
        volatility_percent=2.0,
    )

    assert evaluate_strategy_integration(input_model) == evaluate_strategy_integration(
        input_model
    )


def test_no_file_env_or_network_side_effects_are_present() -> None:
    source = inspect.getsource(strategy_integration)
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


def _assert_clean_import_does_not_load_forbidden_modules(module_name: str) -> None:
    code = f"""
import json
import sys
import {module_name}

forbidden = set({FORBIDDEN_MODULES!r})
loaded = set(sys.modules)
violations = sorted(
    forbidden.intersection(loaded)
    | {{name for name in loaded if name.startswith("ibkr_")}}
    | {{name for name in loaded if name.startswith("manual_ibkr_")}}
)
print(json.dumps(violations))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []
