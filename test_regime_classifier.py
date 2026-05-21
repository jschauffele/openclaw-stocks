from __future__ import annotations

import sys

import pytest

from regime_classifier import (
    RegimeClassificationInput,
    RegimeClassificationResult,
    classify_regime,
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
)


def test_insufficient_data_when_closes_length_is_below_lookback() -> None:
    result = classify_regime(RegimeClassificationInput(closes=(100.0, 101.0)))

    assert result.regime_id == "insufficient_data"
    assert result.reason == "sample_count_below_lookback"
    assert result.lookback == 5
    assert result.sample_count == 2
    assert result.latest_close == 101.0
    assert result.oldest_close == 100.0


def test_uptrend_classification_is_deterministic() -> None:
    result = classify_regime(
        RegimeClassificationInput(
            closes=(100.0, 100.2, 100.4, 100.8, 101.2),
            volatility_percent=2.0,
        )
    )

    assert result.regime_id == "uptrend"
    assert result.reason == "percent_change_meets_uptrend_threshold"
    assert result.percent_change == pytest.approx(1.2)


def test_downtrend_classification_is_deterministic() -> None:
    result = classify_regime(
        RegimeClassificationInput(
            closes=(100.0, 99.8, 99.4, 99.1, 98.8),
            volatility_percent=2.0,
        )
    )

    assert result.regime_id == "downtrend"
    assert result.reason == "percent_change_meets_downtrend_threshold"
    assert result.percent_change == pytest.approx(-1.2)


def test_sideways_classification_is_deterministic() -> None:
    result = classify_regime(
        RegimeClassificationInput(
            closes=(100.0, 100.1, 99.9, 100.2, 100.4),
            volatility_percent=2.0,
        )
    )

    assert result.regime_id == "sideways"
    assert result.reason == "percent_change_inside_trend_thresholds"
    assert result.percent_change == pytest.approx(0.4)


def test_volatile_classification_has_precedence_over_trend() -> None:
    result = classify_regime(
        RegimeClassificationInput(
            closes=(100.0, 103.0, 104.0, 105.0, 106.0),
            min_trend_percent=1.0,
            volatility_percent=2.0,
        )
    )

    assert result.regime_id == "volatile"
    assert result.reason == "one_period_move_meets_volatility_threshold"
    assert result.percent_change == pytest.approx(6.0)
    assert result.max_one_period_move_percent == pytest.approx(3.0)


def test_only_the_last_lookback_closes_are_used() -> None:
    result = classify_regime(
        RegimeClassificationInput(
            closes=(200.0, 100.0, 100.5, 101.0),
            lookback=3,
            min_trend_percent=0.5,
            volatility_percent=2.0,
        )
    )

    assert result.oldest_close == 100.0
    assert result.latest_close == 101.0
    assert result.percent_change == pytest.approx(1.0)
    assert result.regime_id == "uptrend"


def test_change_fields_are_computed_correctly() -> None:
    result = classify_regime(
        RegimeClassificationInput(
            closes=(100.0, 101.0, 100.0, 102.0),
            lookback=4,
            min_trend_percent=5.0,
            volatility_percent=5.0,
        )
    )

    assert result.percent_change == pytest.approx(2.0)
    assert result.absolute_percent_change == pytest.approx(2.0)
    assert result.max_one_period_move_percent == pytest.approx(2.0)


def test_input_and_result_dataclasses_are_frozen() -> None:
    input_model = RegimeClassificationInput(closes=(100.0, 101.0))
    result = classify_regime(input_model)

    with pytest.raises(AttributeError):
        input_model.lookback = 3  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.regime_id = "sideways"  # type: ignore[misc]


def test_invalid_lookback_is_rejected() -> None:
    with pytest.raises(ValueError, match="lookback must be >= 2"):
        RegimeClassificationInput(closes=(100.0, 101.0), lookback=1)

    with pytest.raises(ValueError, match="lookback must be an int"):
        RegimeClassificationInput(closes=(100.0, 101.0), lookback=True)  # type: ignore[arg-type]


def test_non_int_lookback_is_rejected() -> None:
    with pytest.raises(ValueError, match="lookback must be an int"):
        RegimeClassificationInput(closes=(100.0, 101.0), lookback=2.5)  # type: ignore[arg-type]


def test_negative_thresholds_are_rejected() -> None:
    with pytest.raises(ValueError, match="min_trend_percent must be >= 0"):
        RegimeClassificationInput(closes=(100.0, 101.0), min_trend_percent=-0.1)

    with pytest.raises(ValueError, match="volatility_percent must be >= 0"):
        RegimeClassificationInput(closes=(100.0, 101.0), volatility_percent=-0.1)


def test_bool_thresholds_are_rejected() -> None:
    with pytest.raises(ValueError, match="min_trend_percent must be numeric"):
        RegimeClassificationInput(closes=(100.0, 101.0), min_trend_percent=True)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="volatility_percent must be numeric"):
        RegimeClassificationInput(closes=(100.0, 101.0), volatility_percent=False)  # type: ignore[arg-type]


def test_non_numeric_thresholds_are_rejected() -> None:
    with pytest.raises(ValueError, match="min_trend_percent must be numeric"):
        RegimeClassificationInput(closes=(100.0, 101.0), min_trend_percent="1.0")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="volatility_percent must be numeric"):
        RegimeClassificationInput(closes=(100.0, 101.0), volatility_percent="2.0")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_threshold", (float("nan"), float("inf"), float("-inf")))
def test_nan_and_infinite_thresholds_are_rejected(bad_threshold: float) -> None:
    with pytest.raises(ValueError, match="min_trend_percent must be finite"):
        RegimeClassificationInput(
            closes=(100.0, 101.0),
            min_trend_percent=bad_threshold,
        )

    with pytest.raises(ValueError, match="volatility_percent must be finite"):
        RegimeClassificationInput(
            closes=(100.0, 101.0),
            volatility_percent=bad_threshold,
        )


def test_non_numeric_closes_are_rejected() -> None:
    with pytest.raises(ValueError, match="closes must contain numeric values"):
        RegimeClassificationInput(closes=(100.0, "101.0"))  # type: ignore[arg-type]


def test_bool_closes_are_rejected() -> None:
    with pytest.raises(ValueError, match="closes must contain numeric values"):
        RegimeClassificationInput(closes=(100.0, True))  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_close", (float("nan"), float("inf"), float("-inf")))
def test_nan_and_infinite_closes_are_rejected(bad_close: float) -> None:
    with pytest.raises(ValueError, match="closes must contain finite values"):
        RegimeClassificationInput(closes=(100.0, bad_close))


@pytest.mark.parametrize("bad_close", (0.0, -1.0))
def test_non_positive_closes_are_rejected(bad_close: float) -> None:
    with pytest.raises(ValueError, match="closes must contain positive values"):
        RegimeClassificationInput(closes=(100.0, bad_close))


def test_repeated_calls_return_equal_results() -> None:
    input_model = RegimeClassificationInput(
        closes=(100.0, 100.2, 100.4, 100.8, 101.2),
        volatility_percent=2.0,
    )

    assert classify_regime(input_model) == classify_regime(input_model)


def test_classify_regime_rejects_non_input_model() -> None:
    with pytest.raises(ValueError, match="input_model must be RegimeClassificationInput"):
        classify_regime({"closes": (100.0, 101.0)})  # type: ignore[arg-type]


def test_result_rejects_unsupported_regime_ids() -> None:
    with pytest.raises(ValueError, match="Unsupported regime_id"):
        RegimeClassificationResult(
            regime_id="runtime_signal",
            reason="example",
            lookback=5,
            sample_count=5,
            latest_close=101.0,
            oldest_close=100.0,
            percent_change=1.0,
            absolute_percent_change=1.0,
            max_one_period_move_percent=1.0,
        )


def test_result_rejects_blank_reason() -> None:
    with pytest.raises(ValueError, match="reason must be non-empty"):
        RegimeClassificationResult(
            regime_id="sideways",
            reason=" ",
            lookback=5,
            sample_count=5,
            latest_close=101.0,
            oldest_close=100.0,
            percent_change=1.0,
            absolute_percent_change=1.0,
            max_one_period_move_percent=1.0,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "latest_close",
        "oldest_close",
        "percent_change",
        "absolute_percent_change",
        "max_one_period_move_percent",
    ),
)
def test_result_rejects_non_finite_numeric_outputs(field_name: str) -> None:
    values = {
        "regime_id": "sideways",
        "reason": "example",
        "lookback": 5,
        "sample_count": 5,
        "latest_close": 101.0,
        "oldest_close": 100.0,
        "percent_change": 1.0,
        "absolute_percent_change": 1.0,
        "max_one_period_move_percent": 1.0,
    }
    values[field_name] = float("nan")

    with pytest.raises(ValueError, match=f"{field_name} must be finite"):
        RegimeClassificationResult(**values)


def test_reserved_unknown_regime_id_is_allowed_for_explicit_result_only() -> None:
    result = RegimeClassificationResult(
        regime_id="unknown",
        reason="reserved_manual_classification",
        lookback=5,
        sample_count=0,
        latest_close=0.0,
        oldest_close=0.0,
        percent_change=0.0,
        absolute_percent_change=0.0,
        max_one_period_move_percent=0.0,
    )

    assert result.regime_id == "unknown"


def test_invalid_input_raises_value_error_instead_of_returning_unknown() -> None:
    with pytest.raises(ValueError, match="closes must contain positive values"):
        classify_regime(RegimeClassificationInput(closes=(100.0, 0.0)))


def test_import_does_not_load_forbidden_modules() -> None:
    loaded_modules = set(sys.modules)

    assert not loaded_modules.intersection(FORBIDDEN_MODULES)
    assert not any(module_name.startswith("ibkr_") for module_name in loaded_modules)
    assert not any(
        module_name.startswith("manual_ibkr_") for module_name in loaded_modules
    )


def test_result_has_no_execution_or_strategy_selection_fields() -> None:
    result = classify_regime(
        RegimeClassificationInput(
            closes=(100.0, 100.1, 100.2, 100.3, 100.4),
        )
    )
    forbidden_fields = {
        "execution",
        "broker",
        "risk",
        "order",
        "order_id",
        "submit",
        "cancel",
        "flatten",
        "route",
        "strategy",
        "strategy_id",
        "selected_strategy",
    }

    assert forbidden_fields.isdisjoint(result.__dataclass_fields__)
